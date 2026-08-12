/* StunAssure — interactive verification demo.
 *
 * An in-browser port of the real prototype engine (prototype/src/stunassure/*.py):
 * simulate a batch -> verify each fish (dose -> recovery-clock -> optional Echo-Stun) ->
 * certify the lot by Welfare-by-Sampling -> emit a SHA-256-signed batch record.
 *
 * Runs on SIMULATED data. Mirrors the fail-safe contract exactly: missing / un-verifiable
 * evidence is UNCERTAIN, never PASS; a species with no published spec (gilthead sea bream)
 * cannot be certified. This is a faithful demonstration, not a mock-up.
 */
(function () {
  "use strict";

  // ---- Cited species library (subset of prototype/src/stunassure/species.py) ----
  var SPECIES = {
    atlantic_salmon:    { name: "Atlantic salmon",    recovery: 44,  maxBleed: 15,   minField: 1.0,  minDur: 1.0, freq: 50,   spec: true,  water: "sea"   },
    rainbow_trout:      { name: "Rainbow trout",      recovery: 30,  maxBleed: 15,   minField: 3.0,  minDur: 1.0, freq: 1000, spec: true,  water: "fresh" },
    european_sea_bass:  { name: "European sea bass",  recovery: 120, maxBleed: null, minField: 1.0,  minDur: 1.0, freq: 50,   spec: true,  water: "sea"   },
    gilthead_sea_bream: { name: "Gilthead sea bream", recovery: 120, maxBleed: null, minField: null, minDur: null, freq: null, spec: false, water: "sea"   },
    common_carp:        { name: "Common carp",        recovery: 48,  maxBleed: null, minField: 3.0,  minDur: 5.0, freq: 50,   spec: true,  water: "fresh" }
  };

  var PASS = "PASS", UNCERTAIN = "UNCERTAIN", FAIL = "FAIL";
  var SEVERITY = { FAIL: 0, UNCERTAIN: 1, PASS: 2 };

  function hardLimit(s) { return s.maxBleed != null ? Math.min(s.maxBleed, s.recovery) : s.recovery; }

  // ---- Engine (mirrors engine.py) ----
  function checkDose(ev, s) {
    if (!s.spec || s.minField == null) return { layer: "dose", verdict: UNCERTAIN, reason: "no published electrical-stun spec — dose un-verifiable" };
    if (ev.field == null || ev.dur == null) return { layer: "dose", verdict: UNCERTAIN, reason: "field or duration not measured" };
    if (ev.field < s.minField) return { layer: "dose", verdict: FAIL, reason: "field " + ev.field.toFixed(2) + " V/cm below minimum " + s.minField.toFixed(2) };
    if (s.minDur != null && ev.dur < s.minDur) return { layer: "dose", verdict: FAIL, reason: "duration " + ev.dur.toFixed(2) + "s below minimum " + s.minDur.toFixed(2) + "s" };
    return { layer: "dose", verdict: PASS, reason: "field & duration within species spec" };
  }
  function checkRecovery(ev, s) {
    var limit = hardLimit(s);
    if (ev.interval == null) return { layer: "recovery_clock", verdict: UNCERTAIN, reason: "stun→bleed interval not recorded" };
    if (ev.interval > limit) return { layer: "recovery_clock", verdict: FAIL, reason: "stun→bleed " + ev.interval.toFixed(0) + "s exceeds " + limit.toFixed(0) + "s — recovery risk" };
    return { layer: "recovery_clock", verdict: PASS, reason: "stun→bleed " + ev.interval.toFixed(0) + "s within " + limit.toFixed(0) + "s" };
  }
  function checkEcho(ev) {
    if (ev.echo == null) return null;
    if (ev.echo) return { layer: "evoked_response", verdict: PASS, reason: "no evoked response (Echo-Stun)" };
    return { layer: "evoked_response", verdict: FAIL, reason: "evoked response present — not insensible" };
  }
  function verify(ev, s) {
    var findings = [checkDose(ev, s), checkRecovery(ev, s)];
    var echo = checkEcho(ev);
    if (echo) findings.push(echo);
    var agg = findings.reduce(function (w, f) { return SEVERITY[f.verdict] < SEVERITY[w] ? f.verdict : w; }, PASS);
    return { verdict: agg, findings: findings };
  }

  // ---- Seeded PRNG (mulberry32) for reproducible batches ----
  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function uni(r, a, b) { return a + (b - a) * r(); }

  // ---- Simulator (mirrors simulator.py) ----
  var MODES = ["weak_field", "long_interval", "short_duration"];
  function simulate(key, n, seed, failRate, useEcho) {
    var s = SPECIES[key], r = rng(seed);
    var minField = s.minField != null ? s.minField : (s.water === "sea" ? 1.0 : 3.0);
    var minDur = s.minDur != null ? s.minDur : 1.0;
    var limit = hardLimit(s);
    var out = [];
    for (var i = 0; i < n; i++) {
      var fail = r() < failRate;
      var field = uni(r, minField * 1.2, minField * 2.0);
      var dur = uni(r, minDur * 1.1, minDur * 2.0);
      var interval = uni(r, 2.0, Math.max(2.1, limit * 0.8));
      var echo = useEcho ? true : null;
      if (fail) {
        var mode = MODES[Math.floor(r() * MODES.length)];
        if (mode === "weak_field") field = uni(r, minField * 0.1, minField * 0.7);
        else if (mode === "long_interval") interval = uni(r, limit * 1.5, limit * 3.0);
        else dur = uni(r, 0.05, minDur * 0.5);
        if (useEcho && r() < 0.5) echo = false;
      }
      out.push({ id: key.slice(0, 3).toUpperCase() + "-" + seed + "-" + String(i).padStart(4, "0"),
                 field: Math.round(field * 1000) / 1000, dur: Math.round(dur * 1000) / 1000,
                 interval: Math.round(interval * 100) / 100, echo: echo });
    }
    return out;
  }

  // ---- Welfare-by-Sampling (binomial c=0; mirrors sampling.py intent) ----
  function designSample(lot, aql, conf) {
    var n = Math.ceil(Math.log(1 - conf) / Math.log(1 - aql));
    return Math.min(lot, Math.max(1, n));
  }
  function achievedConfidence(aql, n) { return 1 - Math.pow(1 - aql, n); }

  // ---- SHA-256 signature (Web Crypto) ----
  async function sign(body) {
    var enc = new TextEncoder().encode(JSON.stringify(body));
    var buf = await crypto.subtle.digest("SHA-256", enc);
    return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
  }

  // ---- DOM helpers ----
  function $(id) { return document.getElementById(id); }
  function el(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }
  var pillClass = { PASS: "pass", UNCERTAIN: "uncertain", FAIL: "fail" };
  var verdictWord = { PASS: "Pass", UNCERTAIN: "Check", FAIL: "Intervene" };

  // ---- Animation / run ----
  var running = false;
  function sleep(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }

  async function runBatch() {
    if (running) return;
    running = true;
    var btn = $("runBtn"); btn.disabled = true; btn.textContent = "Running…";

    var key = $("speciesSel").value;
    var s = SPECIES[key];
    var failRate = parseInt($("failRange").value, 10) / 100;
    var useEcho = $("echoToggle").checked;
    var lot = 25000, aql = 0.065, conf = 0.95;
    var n = designSample(lot, aql, conf);
    var seed = (Date.parse(new Date().toISOString().slice(0, 16)) % 100000) + parseInt($("failRange").value, 10);

    var sample = simulate(key, n, seed, failRate, useEcho);

    // reset UI
    var counts = { PASS: 0, UNCERTAIN: 0, FAIL: 0 };
    ["PASS", "UNCERTAIN", "FAIL"].forEach(function (v) { $("cnt" + v).textContent = "0"; });
    var track = $("track"); track.innerHTML = "";
    $("cert").classList.remove("show");
    setStations(s, "idle");

    // stream the fish through the line
    for (var i = 0; i < sample.length; i++) {
      var res = verify(sample[i], s);
      counts[res.verdict]++;
      spawnFish(track, res.verdict, i, sample.length);
      pulseStations(res);
      $("cnt" + res.verdict).textContent = String(counts[res.verdict]);
      $("focusReason").textContent = sample[i].id + ": " + res.findings.map(function (f) { return f.layer + "=" + f.verdict; }).join(" · ");
      await sleep(sample.length > 30 ? 55 : 90);
    }
    await sleep(700);

    // certify the lot (fail-safe: a defect = anything not positively PASS)
    var defects = sample.length - counts.PASS;
    var accepted = defects <= 0;
    var achieved = accepted ? achievedConfidence(aql, sample.length) : 0;
    var body = { schema: "stunassure.batch-report/v1", species: s.name, lot: lot, sample: sample.length,
                 summary: counts, aql: aql, accepted: accepted, achieved_confidence: Math.round(achieved * 1e4) / 1e4 };
    var sig = await sign(body);
    renderCert(s, lot, sample.length, counts, accepted, achieved, defects, sig);

    btn.disabled = false; btn.textContent = "Run batch ▸"; running = false;
  }

  function spawnFish(track, verdict, i, total) {
    var f = el("span", "fish " + pillClass[verdict]);
    f.style.top = (8 + (i % 5) * 17) + "%";
    f.innerHTML = "<svg viewBox='0 0 28 16' aria-hidden='true'><path d='M2 8c4-6 12-6 18 0-6 6-14 6-18 0z'/><path d='M20 8l6-4v8z'/><circle cx='7' cy='7' r='1.1' fill='#fff'/></svg>";
    track.appendChild(f);
    requestAnimationFrame(function () { f.classList.add("go"); });
    setTimeout(function () { f.classList.add("stamped"); }, 900);
    setTimeout(function () { if (f.parentNode) f.parentNode.removeChild(f); }, 2200);
  }

  function setStations(s, mode) {
    $("stDoseSpec").textContent = s.spec ? (s.minField.toFixed(1) + " V/cm · ≥" + s.minDur.toFixed(0) + "s @ " + s.freq + "Hz") : "no published spec";
    $("stRecSpec").textContent = "≤ " + hardLimit(s).toFixed(0) + "s (recovery onset " + s.recovery + "s)";
    $("stEchoSpec").textContent = $("echoToggle").checked ? "index active" : "layer off";
    ["stDose", "stRec", "stEcho", "stCert"].forEach(function (id) { $(id).classList.remove("hot"); });
  }
  function pulseStations(res) {
    var map = { dose: "stDose", recovery_clock: "stRec", evoked_response: "stEcho" };
    res.findings.forEach(function (f) {
      var node = $(map[f.layer]); if (!node) return;
      node.classList.remove("v-pass", "v-uncertain", "v-fail");
      node.classList.add("hot", "v-" + pillClass[f.verdict]);
      setTimeout(function () { node.classList.remove("hot"); }, 260);
    });
  }

  function renderCert(s, lot, n, counts, accepted, achieved, defects, sig) {
    var c = $("cert");
    $("certTitle").textContent = accepted ? "✅ Lot certified" : "⛔ Lot rejected — manual check";
    c.classList.toggle("ok", accepted);
    c.classList.toggle("bad", !accepted);
    $("certBody").innerHTML =
      "<p><b>" + s.name + "</b> · lot " + lot.toLocaleString() + " · sample " + n + " (zero-acceptance, AQL 6.5%)</p>" +
      "<p class='cert-tally'><span class='pill pass'>Pass " + counts.PASS + "</span> " +
      "<span class='pill uncertain'>Check " + counts.UNCERTAIN + "</span> " +
      "<span class='pill fail'>Intervene " + counts.FAIL + "</span></p>" +
      "<p>" + (accepted
        ? "0 sample defects → lot certified ≤6.5% welfare failures at <b>" + (achieved * 100).toFixed(1) + "% confidence</b>."
        : defects + " sample defect(s) → lot rejected; route to 100% manual check / corrective action.") +
      (s.spec ? "" : " <em>No published electrical-stun spec for this species — every fish is UNCERTAIN, so we refuse to certify. This is exactly the evidence gap StunAssure is built to close.</em>") + "</p>" +
      "<p class='cert-sig'>Signature (SHA-256, tamper-evident): <code>" + sig.slice(0, 32) + "…</code></p>";
    c.classList.add("show");
  }

  // ---- init ----
  document.addEventListener("DOMContentLoaded", function () {
    var sel = $("speciesSel");
    Object.keys(SPECIES).forEach(function (k) {
      var o = el("option"); o.value = k; o.textContent = SPECIES[k].name; sel.appendChild(o);
    });
    sel.value = "atlantic_salmon";
    var fr = $("failRange");
    var updateFail = function () { $("failVal").textContent = fr.value + "%"; };
    fr.addEventListener("input", updateFail); updateFail();
    var refresh = function () { setStations(SPECIES[sel.value], "idle"); };
    sel.addEventListener("change", refresh);
    $("echoToggle").addEventListener("change", refresh);
    refresh();
    $("runBtn").addEventListener("click", runBatch);
  });
})();

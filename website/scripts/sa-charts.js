/* StunAssure shared chart builders — cited data mirrors the State-of-the-Art / hardware pages.
   Include after Chart.js (which is loaded deferred):
     <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js" defer></script>
     <script src="scripts/sa-charts.js" defer></script>
   Then drop a canvas:  <canvas class="sa-canvas" data-chart="costTiers"></canvas>
   Chart.js is MIT-licensed and free. This file injects its own .sa-fig styles. */
(function () {
  function ready(fn){ if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function () {
    if (typeof Chart === 'undefined') return;

    // Inject scoped figure styles once (uses the site's CSS custom properties).
    if (!document.getElementById('sa-charts-style')) {
      var st = document.createElement('style'); st.id = 'sa-charts-style';
      st.textContent =
        '.sa-fig{margin:2rem 0 .5rem;background:var(--white,#fff);border:1px solid var(--border,#D9E6E3);' +
        'border-radius:16px;padding:1.1rem 1.2rem 1rem}.sa-fig h3{margin:.1rem 0 .2rem;font-size:1.04rem;' +
        'color:var(--ink,#102A2C)}.sa-fig .sa-sub{color:var(--slate,#5D7073);font-size:.87rem;margin:0 0 .8rem}' +
        '.sa-fig .sa-box{position:relative;height:300px}.sa-fig figcaption{margin:.75rem 0 0;font-size:.78rem;' +
        'color:var(--slate,#5D7073);border-top:1px dashed var(--border,#D9E6E3);padding-top:.55rem}' +
        '.sa-fig figcaption a{color:var(--data,#006D9C);text-decoration:none}';
      document.head.appendChild(st);
    }

    var css = getComputedStyle(document.documentElement), c = function (n, f) { var v = css.getPropertyValue(n).trim(); return v || f; };
    var TEAL = c('--ocean-teal','#1F6F6D'), FOAM = c('--seafoam','#3BAAA6'), DEEP = c('--deep-ocean','#0D3B3E'),
        DATA = c('--data','#006D9C'), MINT = c('--soft-mint','#A8D5CF'), SLATE = c('--slate','#5D7073'),
        LINE = c('--border','#D9E6E3'), POOR = '#C4462F', WARN = '#D98A2B';
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.color = SLATE;
    Chart.defaults.layout = { padding:{ left:6, right:10, top:4 } };
    var grid = { color:LINE, drawTicks:false }, noLeg = { legend:{ display:false } };

    var builders = {
      // Deployment cost tiers — floating range bars, log €.
      costTiers: function (cv) { new Chart(cv, { type:'bar', data:{
        labels:['Lite (phone app)','Sensor Box','Camera / Echo-Stun','Validation'],
        datasets:[{ data:[[0,200],[100,2000],[2000,10000],[10000,40000]], backgroundColor:[MINT,FOAM,TEAL,DATA], borderRadius:6 }] },
        options:{ plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ var v=x.raw; return '€'+v[0].toLocaleString()+'–'+v[1].toLocaleString()+(v[1]>=40000?'+ (project)':''); } } } },
          scales:{ y:{ type:'logarithmic', grid:grid, title:{ display:true, text:'site cost € (log)' } }, x:{ grid:{ display:false } } } } }); },

      // Cost leverage — €150k stunner vs €85 verifier, log €.
      costLeverage: function (cv) { new Chart(cv, { type:'bar', data:{
        labels:['In-water stunner','StunAssure logger'],
        datasets:[{ data:[150000,85], backgroundColor:[SLATE,TEAL], borderRadius:6 }] },
        options:{ indexAxis:'y', plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ return '€'+x.parsed.x.toLocaleString(); } } } },
          scales:{ x:{ type:'logarithmic', grid:grid, title:{ display:true, text:'€ per unit (log)' } }, y:{ grid:{ display:false } } } } }); },

      // Verification stack readiness.
      stackReadiness: function (cv) { new Chart(cv, { type:'bar', data:{
        labels:['StunDose (measure delivery)','Recovery-Clock (enforce window)','Welfare-by-Sampling (certify batch)','Echo-Stun (verify insensibility)'],
        datasets:[{ data:[90,85,70,45], backgroundColor:[TEAL,TEAL,FOAM,WARN], borderRadius:6 }] },
        options:{ indexAxis:'y', plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ var v=x.parsed.x; return v>=80?'Ready now — backbone':(v>=60?'Ready — defensible':'Research stretch (contact variant de-risked)'); } } } },
          scales:{ x:{ grid:grid, min:0, max:100, title:{ display:true, text:'indicative readiness — team assessment, qualitative' } }, y:{ grid:{ display:false } } } } }); },

      // Scale path to >1B fish, log fish/yr.
      scalePath: function (cv) { new Chart(cv, { type:'bar', data:{
        labels:['Pilot (year 1)','EU finfish retrofit','Species-profile expansion'],
        datasets:[{ data:[50000,5000000,1000000000], backgroundColor:[MINT,FOAM,TEAL], borderRadius:6 }] },
        options:{ plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ return x.parsed.y.toLocaleString()+' fish / yr'; } } } },
          scales:{ y:{ type:'logarithmic', grid:grid, min:10000, max:2000000000,
              title:{ display:true, text:'fish verified / yr (log) — >1B = "excellent"' },
              ticks:{ callback:function(v){ var p=Math.log10(v); return p%1===0 ? (v>=1e9?v/1e9+'B':v>=1e6?v/1e6+'M':v>=1e3?v/1e3+'k':v) : ''; } } },
            x:{ grid:{ display:false } } } } }); },

      // Project timeline — floating bars per phase over 12 months (factual plan dates).
      timeline: function (cv) { new Chart(cv, { type:'bar', data:{
        labels:['1 · Map & define','2 · Build prototype','3 · Semi-field pilot','4 · Camera / validation (optional)'],
        datasets:[{ data:[[0,2],[2,4],[4,6],[6,12]], backgroundColor:[DEEP,TEAL,FOAM,MINT], borderRadius:6 }] },
        options:{ indexAxis:'y', plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ var v=x.raw; return 'months '+v[0]+'–'+v[1]; } } } },
          scales:{ x:{ grid:grid, min:0, max:12, title:{ display:true, text:'project month' }, ticks:{ stepSize:2 } }, y:{ grid:{ display:false } } } } }); },

      // TRL trajectory line.
      trl: function (cv) { new Chart(cv, { type:'line', data:{
        labels:['Now','Mo 3','Mo 6','Mo 9','Mo 12'],
        datasets:[{ data:[2.5,3,4,4.5,5], borderColor:TEAL, backgroundColor:'rgba(31,111,109,.12)', fill:true, tension:.35, pointRadius:4, pointBackgroundColor:TEAL, borderWidth:2.5 }] },
        options:{ plugins:{ ...noLeg, tooltip:{ callbacks:{ label:function(x){ return 'TRL '+x.parsed.y; } } } },
          scales:{ y:{ grid:grid, min:1, max:9, ticks:{ stepSize:1, callback:function(v){ return 'TRL '+v; } }, title:{ display:true, text:'technology readiness level' } }, x:{ grid:{ display:false } } } } }); }
    };

    document.querySelectorAll('canvas.sa-canvas[data-chart]').forEach(function (cv) {
      var k = cv.getAttribute('data-chart'); if (builders[k]) builders[k](cv);
    });
  });
})();

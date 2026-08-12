// StunAssure site interactions: sticky-header state, mobile nav, scroll reveals, active link.
(function () {
  "use strict";

  // Mark JS active so .reveal elements start hidden (content stays visible if JS fails).
  document.documentElement.classList.add("js");

  var header = document.getElementById("header");
  var toggle = document.getElementById("navToggle");

  // Sticky header border on scroll
  var onScroll = function () {
    if (window.scrollY > 12) header.classList.add("scrolled");
    else header.classList.remove("scrolled");
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Mobile menu
  if (toggle) {
    toggle.addEventListener("click", function () {
      header.classList.toggle("open");
    });
    header.querySelectorAll(".nav-links a").forEach(function (a) {
      a.addEventListener("click", function () { header.classList.remove("open"); });
    });
  }

  // Scroll reveal
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // Active nav link by current page (multi-page site).
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-links a"));
  var current = location.pathname.split("/").pop() || "index.html";
  if (current === "") current = "index.html";
  links.forEach(function (l) {
    var target = (l.getAttribute("href") || "").split("#")[0].split("/").pop();
    if (target === current) l.classList.add("active");
  });
})();

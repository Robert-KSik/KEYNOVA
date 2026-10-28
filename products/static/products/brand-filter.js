(function () {
  "use strict";

  var root = document.getElementById("brand-filter");
  if (!root) return;

  var grid = document.getElementById("product-grid");
  var chipsBox = document.getElementById("brand-chips");
  var indicator = chipsBox.querySelector(".brand-indicator");
  var moreBtn = document.getElementById("brand-more");
  var panel = document.getElementById("brand-panel");
  var search = document.getElementById("brand-search");
  var emptyMsg = document.getElementById("brand-empty");
  var labelEl = document.getElementById("catalog-label");
  var statusEl = document.getElementById("brand-status");
  var options = Array.prototype.slice.call(panel.querySelectorAll(".brand-option"));

  var cardsUrl = root.dataset.cardsUrl;
  var current = root.dataset.activeBrand || "";
  var controller = null;
  var skeletonTimer = null;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- helpers ---------- */

  function chips() {
    return Array.prototype.slice.call(chipsBox.querySelectorAll(".brand-chip"));
  }

  function findChip(slug) {
    return chips().find(function (c) { return c.dataset.brand === slug; }) || null;
  }

  function optionName(slug) {
    var o = options.find(function (o) { return o.dataset.brand === slug; });
    return o ? o.dataset.name : "";
  }

  function knownBrand(slug) {
    return slug === "" || !!findChip(slug) || !!optionName(slug);
  }

  function plainClick(e) {
    return e.button === 0 && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey;
  }

  /* ---------- the sliding highlight ---------- */

  function moveIndicator() {
    var active = chipsBox.querySelector(".brand-chip.is-active");
    if (!active) return;
    indicator.style.width = active.offsetWidth + "px";
    indicator.style.transform = "translateX(" + active.offsetLeft + "px)";
    var target = active.offsetLeft - (chipsBox.clientWidth - active.offsetWidth) / 2;
    chipsBox.scrollTo({
      left: Math.max(0, target),
      behavior: reduceMotion ? "auto" : "smooth"
    });
  }

  /* ---------- marking the active brand ---------- */

  function setActive(slug) {
    var chip = findChip(slug);
    var name = "";

    if (slug) {
      name = optionName(slug) || (chip ? chip.textContent.trim() : slug);
    }

    if (!chip && slug) {
      chip = document.createElement("a");
      chip.className = "brand-chip";
      chip.href = "?brand=" + encodeURIComponent(slug);
      chip.dataset.brand = slug;
      chip.dataset.pinned = "1";
      chip.textContent = name;
      chipsBox.appendChild(chip);
    }

    Array.prototype.forEach.call(chipsBox.querySelectorAll("[data-pinned]"), function (c) {
      if (c.dataset.brand !== slug) c.remove();
    });

    chips().forEach(function (c) {
      var on = c.dataset.brand === slug;
      c.classList.toggle("is-active", on);
      if (on) c.setAttribute("aria-current", "true");
      else c.removeAttribute("aria-current");
    });

    options.forEach(function (o) {
      o.classList.toggle("is-active", o.dataset.brand === slug);
    });

    labelEl.textContent = "KEYNOVA / " + (name || "products").toUpperCase();
    moveIndicator();
    return name;
  }

  /* ---------- loading products without a reload ---------- */

  function showSkeleton(count) {
    var n = Math.min(Math.max(count, 3), 6);
    var card =
      '<div class="skeleton-card" aria-hidden="true">' +
      '<div class="skeleton-shimmer skeleton-img"></div>' +
      '<div class="skeleton-body">' +
      '<div class="skeleton-shimmer skeleton-line short"></div>' +
      '<div class="skeleton-shimmer skeleton-line"></div>' +
      '<div class="skeleton-shimmer skeleton-line medium"></div>' +
      "</div></div>";
    grid.innerHTML = new Array(n + 1).join(card);
  }

  function load(slug, name) {
    if (controller) controller.abort();
    clearTimeout(skeletonTimer);
    controller = new AbortController();
    var mine = controller;
    var query = slug ? "?brand=" + encodeURIComponent(slug) : "";

    var previousCount = grid.children.length;
    grid.style.minHeight = grid.offsetHeight + "px";
    grid.classList.add("is-loading");
    grid.setAttribute("aria-busy", "true");

    skeletonTimer = setTimeout(function () {
      showSkeleton(previousCount);
    }, 220);

    fetch(cardsUrl + query, {
      signal: mine.signal,
      credentials: "same-origin",
      headers: { Accept: "text/html" }
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Bad status " + response.status);
        return response.text();
      })
      .then(function (html) {
        clearTimeout(skeletonTimer);
        grid.innerHTML = html;

        Array.prototype.forEach.call(grid.children, function (el, i) {
          el.style.setProperty("--i", Math.min(i, 8));
        });

        grid.classList.remove("is-loading", "is-entering");
        void grid.offsetWidth;
        grid.classList.add("is-entering");
        grid.removeAttribute("aria-busy");
        grid.style.minHeight = "";

        var count = grid.querySelectorAll(".product-card").length;
        statusEl.textContent = count
          ? "Showing " + count + (name ? " " + name : "") +
            (count === 1 ? " keyboard" : " keyboards")
          : "No keyboards found.";
      })
      .catch(function (error) {
        if (error.name === "AbortError") return;
        window.location.assign(location.pathname + query);
      });
  }

  function select(slug, push) {
    closePanel(false);
    if (slug === current) return;
    current = slug;
    var name = setActive(slug);
    if (push) {
      history.pushState(
        { brand: slug },
        "",
        location.pathname + (slug ? "?brand=" + encodeURIComponent(slug) : "")
      );
    }
    load(slug, name);
  }

  /* ---------- the More brands panel ---------- */

  function filterOptions() {
    var q = search.value.trim().toLowerCase();
    var shown = 0;
    options.forEach(function (o) {
      var match = o.dataset.name.toLowerCase().indexOf(q) !== -1;
      o.parentElement.hidden = !match;
      if (match) shown++;
    });
    emptyMsg.hidden = shown !== 0;
  }

  function openPanel() {
    panel.hidden = false;
    moreBtn.setAttribute("aria-expanded", "true");
    search.value = "";
    filterOptions();
    if (window.matchMedia("(hover: hover)").matches) {
      search.focus({ preventScroll: true });
    }
  }

  function closePanel(returnFocus) {
    if (panel.hidden) return;
    panel.hidden = true;
    moreBtn.setAttribute("aria-expanded", "false");
    if (returnFocus) moreBtn.focus();
  }

  /* ---------- events ---------- */

  chipsBox.addEventListener("click", function (e) {
    var chip = e.target.closest(".brand-chip");
    if (!chip || !plainClick(e)) return;
    e.preventDefault();
    select(chip.dataset.brand, true);
  });

  panel.addEventListener("click", function (e) {
    var option = e.target.closest(".brand-option");
    if (!option || !plainClick(e)) return;
    e.preventDefault();
    select(option.dataset.brand, true);
  });

  moreBtn.addEventListener("click", function () {
    if (panel.hidden) openPanel();
    else closePanel(false);
  });

  search.addEventListener("input", filterOptions);

  search.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var first = options.find(function (o) { return !o.parentElement.hidden; });
    if (first) {
      e.preventDefault();
      select(first.dataset.brand, true);
    }
  });

  panel.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    var visible = options.filter(function (o) { return !o.parentElement.hidden; });
    if (!visible.length) return;
    e.preventDefault();
    var i = visible.indexOf(document.activeElement);
    var next = e.key === "ArrowDown" ? i + 1 : i - 1;
    if (next < 0) {
      search.focus();
      return;
    }
    if (next >= visible.length) next = visible.length - 1;
    visible[next].focus();
  });

  chipsBox.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    var list = chips();
    var i = list.indexOf(document.activeElement);
    if (i === -1) return;
    e.preventDefault();
    var next = list[i + (e.key === "ArrowRight" ? 1 : -1)];
    if (next) next.focus();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !panel.hidden) closePanel(true);
  });

  document.addEventListener("click", function (e) {
    if (!root.contains(e.target)) closePanel(false);
  });

  window.addEventListener("popstate", function () {
    var slug = new URLSearchParams(location.search).get("brand") || "";
    if (!knownBrand(slug)) slug = "";
    if (slug === current) return;
    current = slug;
    var name = setActive(slug);
    load(slug, name);
  });

  window.addEventListener("resize", moveIndicator);

  /* ---------- start ---------- */

  history.replaceState({ brand: current }, "");
  root.classList.add("js-ready");
  moveIndicator();
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      indicator.classList.add("is-ready");
    });
  });
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(moveIndicator);
  }
})();
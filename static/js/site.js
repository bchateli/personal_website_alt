// Mobile menu, publication filters, abstract/BibTeX toggles, year-nav highlighting.
(() => {
  const nav = document.querySelector(".main-nav");
  const toggle = document.querySelector(".nav-toggle");
  toggle?.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  // Light/dark theme (light by default, choice remembered)
  document.querySelector(".theme-toggle")?.addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme !== "dark";
    if (dark) root.dataset.theme = "dark"; else delete root.dataset.theme;
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch {}
  });

  // Abstract / BibTeX panels
  document.querySelectorAll("[data-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = document.getElementById(btn.dataset.toggle);
      const open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
    });
  });

  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = document.getElementById(btn.dataset.copy).textContent;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied!";
      } catch {
        btn.textContent = "Select & copy";
      }
      setTimeout(() => (btn.textContent = "Copy"), 1500);
    });
  });

  // Type filter
  const chips = document.querySelectorAll(".chip");
  const years = document.querySelectorAll(".pub-year");
  const yearLinks = document.querySelectorAll(".year-nav a");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const f = chip.dataset.filter;
      chips.forEach((c) => c.classList.toggle("active", c === chip));
      years.forEach((section) => {
        let any = false;
        section.querySelectorAll(".pub-card").forEach((card) => {
          const show = f === "all" || card.dataset.type === f;
          card.hidden = !show;
          any ||= show;
        });
        section.hidden = !any;
        document.querySelector(`.year-nav a[data-year="${section.dataset.year}"]`)
          ?.parentElement.toggleAttribute("hidden", !any);
      });
    });
  });

  // Year menu: highlight the year in view; a clicked year stays selected until the user scrolls
  const setActive = (y) => yearLinks.forEach((a) => a.classList.toggle("active", a.dataset.year === y));
  let pinned = null;
  const current = () => {
    const visible = [...years].filter((s) => !s.hidden);
    if (!visible.length) return null;
    const atBottom = innerHeight + scrollY >= document.documentElement.scrollHeight - 4;
    if (atBottom) return visible[visible.length - 1].dataset.year;
    let y = visible[0].dataset.year;
    for (const s of visible) if (s.getBoundingClientRect().top <= 140) y = s.dataset.year;
    return y;
  };
  const update = () => setActive(pinned ?? current());
  if (years.length) {
    yearLinks.forEach((a) => a.addEventListener("click", () => { pinned = a.dataset.year; setActive(pinned); }));
    const unpin = () => { if (pinned) { pinned = null; update(); } };
    ["wheel", "touchmove", "keydown"].forEach((ev) => addEventListener(ev, unpin, { passive: true }));
    addEventListener("scroll", update, { passive: true });
    chips.forEach((c) => c.addEventListener("click", () => { pinned = null; update(); }));
    update();
  }
})();

// Figure preview: click a publication figure to see it large; Esc, × or a click outside closes it
(() => {
  const box = document.querySelector(".lightbox");
  if (!box) return;
  const img = box.querySelector("img");
  const caption = box.querySelector(".lightbox-caption");
  document.querySelectorAll(".zoomable").forEach((btn) => {
    btn.addEventListener("click", () => {
      img.src = btn.dataset.full;
      img.alt = btn.querySelector("img").alt;
      caption.textContent = btn.dataset.caption;
      box.showModal();
    });
  });
  box.querySelector(".lightbox-close").addEventListener("click", () => box.close());
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && box.open) box.close(); });
})();

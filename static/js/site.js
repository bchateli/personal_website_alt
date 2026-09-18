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

// Site search: the index (search.json) is fetched on first open; "/" or Ctrl/Cmd+K opens it
(() => {
  const box = document.querySelector(".search-box");
  if (!box) return;
  const input = box.querySelector("input");
  const list = box.querySelector(".search-results");
  let index = null, sel = 0;

  const fold = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const escape = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  // wrap every occurrence of the query terms in <mark> (diacritic-insensitive, same length after folding)
  const mark = (text, terms) => {
    const f = fold(text);
    if (f.length !== text.length) return escape(text);
    const hits = [];
    terms.forEach((t) => { for (let i = f.indexOf(t); i >= 0; i = f.indexOf(t, i + 1)) hits.push([i, i + t.length]); });
    hits.sort((a, b) => a[0] - b[0]);
    let out = "", at = 0;
    for (const [s, e] of hits) {
      if (s < at) continue;
      out += escape(text.slice(at, s)) + "<mark>" + escape(text.slice(s, e)) + "</mark>";
      at = e;
    }
    return out + escape(text.slice(at));
  };
  const snippet = (text, terms) => {
    const f = fold(text);
    const i = Math.min(...terms.map((t) => f.indexOf(t)).filter((i) => i >= 0));
    if (!isFinite(i)) return "";
    const start = Math.max(0, text.lastIndexOf(" ", Math.max(0, i - 50)) + 1);
    const end = Math.min(text.length, i + 110);
    return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
  };

  const render = () => {
    const terms = fold(input.value).split(/\s+/).filter(Boolean);
    if (!terms.length || !index) { list.innerHTML = ""; return; }
    const results = [];
    for (const e of index) {
      const title = fold(e.t), meta = fold(e.m || ""), body = fold(e.x);
      if (!terms.every((t) => title.includes(t) || meta.includes(t) || body.includes(t))) continue;
      let score = 0;
      for (const t of terms) score += title.includes(t) ? 10 : meta.includes(t) ? 4 : 1;
      if (e.s === "Page") score -= 3;
      results.push([score, e]);
    }
    results.sort((a, b) => b[0] - a[0]);
    sel = 0;
    list.innerHTML = results.length
      ? results.slice(0, 30).map(([, e], i) => {
          const snip = e.x && !terms.every((t) => fold(e.t).includes(t)) ? snippet(e.x, terms) : "";
          return `<li${i === 0 ? ' class="sel"' : ""}><a href="${escape(e.u)}">` +
            `<span class="r-title"><span class="r-tag">${escape(e.s)}</span>${mark(e.t, terms)}</span>` +
            (e.m ? `<span class="r-meta">${mark(e.m, terms)}</span>` : "") +
            (snip ? `<span class="r-snip">${mark(snip, terms)}</span>` : "") + `</a></li>`;
        }).join("")
      : `<li class="none">No results for “${escape(input.value.trim())}”</li>`;
  };

  const open = async () => {
    if (box.open) return;
    box.showModal();
    input.select();
    if (!index) {
      try { index = await (await fetch("/search.json")).json(); } catch { index = []; }
      render();
    }
  };
  document.querySelector(".search-toggle")?.addEventListener("click", open);
  document.addEventListener("keydown", (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName);
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) { e.preventDefault(); open(); }
  });
  input.addEventListener("input", render);
  input.addEventListener("keydown", (e) => {
    const items = [...list.querySelectorAll("li:not(.none)")];
    if (!items.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      items[sel].classList.remove("sel");
      sel = (sel + (e.key === "ArrowDown" ? 1 : items.length - 1)) % items.length;
      items[sel].classList.add("sel");
      items[sel].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      e.preventDefault();
      items[sel].querySelector("a").click();
    }
  });
  // same-page links (e.g. a paper while on Publications) only change the hash, so close the box
  list.addEventListener("click", (e) => { if (e.target.closest("a")) box.close(); });
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
})();

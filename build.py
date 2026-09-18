#!/usr/bin/env python3
"""Static site builder for the academic homepage (Python 3.11+, standard library only).

    python3 build.py            # build into _site/
    python3 build.py --serve    # build, serve on http://localhost:8000 and rebuild on changes
    python3 build.py --serve --port 4000

Content is Markdown with a TOML front matter block between +++ lines (Hugo-style):
    content/_index.md                  site settings + home page bio
    content/news.md                    news list shown on the home page
    content/publications/<id>/index.md one folder per paper (figure and slides next to it)
    content/<page>/index.md            any other page (talks, supervision, phd, ...)
Files next to an index.md are published at the same path; static/ is copied as-is.
"""
import argparse
import hashlib
import html
import http.server
import json
import os
import random
import re
import shutil
import socketserver
import sys
import threading
import time
import tomllib
from datetime import date
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

ANALYTICS = True  # turned off by --serve so local previews are not counted

TYPE_LABELS = {"journal": "Journal", "conference": "Conference", "preprint": "Preprint"}

esc = partial(html.escape, quote=True)


# ---------------------------------------------------------------- content loading

FRONT_RE = re.compile(r"\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n?(.*)\Z", re.S)


def read_md(path):
    """Return (front matter dict, Markdown body) for a content file."""
    text = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(text)
    if not m:
        return {}, text
    try:
        return tomllib.loads(m.group(1)), m.group(2)
    except tomllib.TOMLDecodeError as e:
        raise SystemExit(f"{path.relative_to(ROOT)}: invalid front matter: {e}")


# ---------------------------------------------------------------- Markdown

def resolve(url, base):
    """Relative links inside a page folder point at that folder once published."""
    if re.match(r"^([a-z]+:|/|#)", url):
        return url
    return base + url


def ext_attrs(url):
    return ' target="_blank" rel="noopener"' if re.match(r"^https?:", url) else ""


def _emphasis(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", s)
    return s


def md_inline(text, base="/"):
    """Inline Markdown: `code`, ![img](src), [link](url), **bold**, *italic*, _italic_."""
    keep = []

    def stash(html_):
        keep.append(html_)
        return f"\x00{len(keep) - 1}\x00"

    s = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{esc(m.group(1))}</code>"), text)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: stash(f'<img src="{esc(resolve(m.group(2), base))}" alt="{esc(m.group(1))}" loading="lazy">'), s)

    def link(m):
        url = resolve(m.group(2), base)
        return stash(f'<a href="{esc(url)}"{ext_attrs(url)}>{_emphasis(esc(m.group(1), quote=False))}</a>')

    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = _emphasis(esc(s, quote=False))
    while "\x00" in s:
        s = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)
    return s


LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+(.*)")


def md_block(text, base="/"):
    """Block Markdown: headings, paragraphs, lists, fenced code, images, rules, raw HTML."""
    lines = text.strip("\n").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or re.match(r"^\s*<!--.*-->\s*$", line):
            i += 1
        elif line.startswith("```"):
            lang = line[3:].strip()
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            cls = f' class="language-{esc(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{esc(chr(10).join(lines[i + 1:j]))}</code></pre>")
            i = j + 1
        elif m := re.match(r"^(#{1,6})\s+(.*)", line):
            n = len(m.group(1))
            out.append(f"<h{n}>{md_inline(m.group(2), base)}</h{n}>")
            i += 1
        elif re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
        elif line.lstrip().startswith("<"):
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            out.append("\n".join(lines[i:j]))
            i = j
        elif m := LIST_RE.match(line):
            tag = "ol" if m.group(1)[0].isdigit() else "ul"
            items = []
            while i < len(lines):
                m = LIST_RE.match(lines[i])
                if m:
                    items.append(m.group(2))
                elif lines[i].strip() and lines[i].startswith((" ", "\t")):
                    items[-1] += " " + lines[i].strip()
                elif not lines[i].strip() and i + 1 < len(lines) and LIST_RE.match(lines[i + 1]):
                    pass
                else:
                    break
                i += 1
            lis = "\n".join(f"<li>{md_inline(it, base)}</li>" for it in items)
            out.append(f"<{tag}>\n{lis}\n</{tag}>")
        else:
            j = i
            while (j < len(lines) and lines[j].strip() and not LIST_RE.match(lines[j])
                   and not lines[j].startswith(("#", "```"))):
                j += 1
            para = " ".join(l.strip() for l in lines[i:j])
            if m := re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", para):
                cap = f"<figcaption>{md_inline(m.group(1), base)}</figcaption>" if m.group(1) else ""
                out.append(f'<figure><img src="{esc(resolve(m.group(2), base))}" alt="{esc(m.group(1))}">'
                           f'{cap}</figure>')
            else:
                out.append(f"<p>{md_inline(para, base)}</p>")
            i = j
    return "\n".join(out)


def strip_md(text):
    return re.sub(r"[*_`]", "", text)


# ---------------------------------------------------------------- layout

def page(site, nav, current, title, body, page_class=""):
    """`title` may contain inline Markdown (e.g. **PhD**); None hides the heading."""
    items = "\n".join(
        f'<li{" class=\"current\"" if url == current else ""}><a href="{url}">{esc(label)}</a></li>'
        for label, url in nav
    )
    full_title = site["name"] if title is None else f"{strip_md(title)} — {site['name']}"
    heading = "" if title is None else f'<h1 class="page-title">{md_inline(title)}</h1>'
    ga = ""
    if ANALYTICS and site.get("google_analytics"):
        gid = esc(site["google_analytics"])
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
              f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}'
              f'gtag("js",new Date());gtag("config","{gid}");</script>\n')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(site['description'])}">
<meta name="author" content="{esc(site['name'])}">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<script>try{{if(localStorage.getItem("theme")==="dark")document.documentElement.dataset.theme="dark"}}catch(e){{}}</script>
{ga}</head>
<body class="{page_class}">
<header class="site-header">
  <div class="wrap">
    <p class="site-title"><a href="/">{esc(site['name'])}</a></p>
  </div>
  <nav class="main-nav" aria-label="Main">
    <div class="wrap">
      <button class="nav-toggle" aria-expanded="false" aria-controls="menu">
        <span class="bars" aria-hidden="true"></span><span class="sr">Menu</span>
      </button>
      <ul id="menu">
{items}
      </ul>
      <button class="search-toggle" aria-label="Search the site" title="Search (/)">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.8-4.8"/></svg>
      </button>
      <button class="theme-toggle" aria-label="Toggle dark theme" title="Toggle light/dark theme">
        <svg class="sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
      </button>
    </div>
  </nav>
</header>
<main class="wrap site-main">
{heading}
{body}
</main>
<dialog class="search-box" aria-label="Search">
  <div class="search-field">
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.8-4.8"/></svg>
    <input type="search" placeholder="Search publications, talks, news…" aria-label="Search the site" autocomplete="off" spellcheck="false">
    <kbd>Esc</kbd>
  </div>
  <ul class="search-results" role="listbox"></ul>
</dialog>
<footer class="site-footer">
  <div class="wrap">
    <span>Copyright © {date.today().year} {esc(site['name'])}.</span>
    <span class="footer-links">{social_links(site, plain=True)}</span>
  </div>
</footer>
<script src="/js/site.js" defer></script>
</body>
</html>
"""


ICONS = {
    "Email": '<path d="M3 5h18v14H3z" fill="none" stroke="currentColor" stroke-width="2"/><path d="m3 6 9 7 9-7" fill="none" stroke="currentColor" stroke-width="2"/>',
    "Google Scholar": '<path d="M12 3 1 10l11 7 9-5.7V17h2v-7z" fill="currentColor"/><path d="M6 14.2V18c0 1.7 2.7 3 6 3s6-1.3 6-3v-3.8l-6 3.8z" fill="currentColor"/>',
    "LinkedIn": '<path d="M4 9h4v11H4zM6 3.5a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4zM10 9h3.8v1.6c.6-1 1.9-1.9 3.8-1.9 4 0 4.4 2.5 4.4 5.8V20h-4v-4.8c0-1.3 0-2.9-1.8-2.9s-2.1 1.4-2.1 2.8V20H10z" fill="currentColor"/>',
    "Chalmers": '<path d="M12 2 2 7v2h20V7z" fill="currentColor"/><path d="M5 11h2v7H5zM11 11h2v7h-2zM17 11h2v7h-2z" fill="currentColor"/><path d="M2 20h20v2H2z" fill="currentColor"/>',
    "GitHub": '<path fill="currentColor" d="M12 2a10 10 0 0 0-3.2 19.5c.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.3-3.4-1.3-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.6 2.4 1.1 2.9.8.1-.7.4-1.1.6-1.4-2.2-.2-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.8 1a9.6 9.6 0 0 1 5 0c1.9-1.3 2.8-1 2.8-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9V21c0 .3.2.6.7.5A10 10 0 0 0 12 2z"/>',
}


def social_links(site, plain=False):
    out = []
    for s in site.get("social", []):
        icon = ICONS.get(s["name"], "")
        svg = f'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">{icon}</svg>' if icon and not plain else ""
        out.append(f'<a href="{esc(s["url"])}"{ext_attrs(s["url"])}>{svg}<span>{esc(s["name"])}</span></a>')
    return ("" if plain else "\n").join(out)


# ---------------------------------------------------------------- pages

def build_home(site, bio, nav):
    cv = (f'<p><a class="cv-link" href="{esc(resolve(site["cv"], "/"))}">Download my CV</a></p>'
          if site.get("cv") else "")
    _, news_md = read_md(CONTENT / "news.md")
    items = []
    for line in md_items(news_md):
        d = re.match(r"\*\*([^*]+)\*\*\s*(.*)", line, re.S)
        when, text = (d.group(1), d.group(2)) if d else ("", line)
        items.append(f'<li><span class="news-date">{esc(when)}</span><span class="news-text">{md_inline(text)}</span></li>')
    body = f"""
<h2 class="headline">{md_inline(site['headline'])}</h2>
<div class="intro clearfix">
  <img class="portrait" src="{esc(resolve(site['photo'], '/'))}" alt="Portrait of {esc(site['name'])}" width="220" height="220">
  {md_block(bio)}
  {cv}
  <div class="social">
{social_links(site)}
  </div>
</div>
<section class="news">
  <h2>News</h2>
  <ul class="news-list">
{chr(10).join(items)}
  </ul>
</section>
"""
    return page(site, nav, "/", None, body, "page-home")


def md_items(text):
    """List items of a Markdown list, with continuation lines joined."""
    items = []
    for line in text.split("\n"):
        if m := LIST_RE.match(line):
            items.append(m.group(2))
        elif line.strip() and items and line.startswith((" ", "\t")):
            items[-1] += " " + line.strip()
    return items


def placeholder_svg(seed):
    """Deterministic bubble image for papers without a figure (in the spirit of luost.me)."""
    rng = random.Random(int(hashlib.md5(seed.encode()).hexdigest(), 16))
    palette = ["#4682b4", "#36648b", "#87aed0", "#b0c4de", "#f0a04b", "#e76f51", "#5f9ea0"]
    circles = "".join(
        f'<circle cx="{rng.randint(0, 320)}" cy="{rng.randint(0, 200)}" r="{rng.randint(28, 90)}" '
        f'fill="{rng.choice(palette)}" fill-opacity="{rng.uniform(0.45, 0.85):.2f}"/>'
        for _ in range(9)
    )
    return (f'<svg class="pub-placeholder" viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" '
            f'role="img" aria-label="Decorative placeholder">{circles}</svg>')


def load_publications():
    pubs = []
    for f in sorted((CONTENT / "publications").glob("*/index.md")):
        meta, body = read_md(f)
        meta["id"] = f.parent.name
        meta["base"] = f"/publications/{f.parent.name}/"
        bib = re.search(r"```bib(?:tex)?\s*\n(.*?)```", body, re.S | re.I)
        meta["bibtex"] = bib.group(1).strip() if bib else ""
        meta["abstract"] = (body[:bib.start()] + body[bib.end():] if bib else body).strip()
        pubs.append(meta)
    pubs.sort(key=lambda p: (p["year"], str(p.get("date", ""))), reverse=True)
    return pubs


def build_publications(site, nav, meta, intro):
    pubs = load_publications()
    years = sorted({p["year"] for p in pubs}, reverse=True)
    counts = {t: sum(p["type"] == t for p in pubs) for t in TYPE_LABELS}

    filters = [f'<button class="chip active" data-filter="all">All <span>{len(pubs)}</span></button>']
    filters += [
        f'<button class="chip" data-filter="{t}">{label}s <span>{counts[t]}</span></button>'
        for t, label in TYPE_LABELS.items() if counts[t]
    ]

    groups = []
    for y in years:
        cards = [pub_card(p, site["name"]) for p in pubs if p["year"] == y]
        groups.append(f'<section class="pub-year" id="y{y}" data-year="{y}">\n<h2 class="year">{y}</h2>\n'
                      f'<div class="pub-group">\n' + "\n".join(cards) + "\n</div>\n</section>")

    yearnav = "\n".join(f'<li><a href="#y{y}" data-year="{y}">{y}</a></li>' for y in years)
    body = f"""
<div class="lead">{md_block(intro, "/publications/")}</div>
<div class="pub-layout">
  <div class="pub-main">
    <div class="pub-filters" role="group" aria-label="Filter by type">
      {''.join(filters)}
    </div>
{chr(10).join(groups)}
  </div>
  <aside class="year-nav" aria-label="Jump to year">
    <ul>
{yearnav}
    </ul>
  </aside>
</div>
<dialog class="lightbox" aria-label="Figure preview">
  <button class="lightbox-close" aria-label="Close">×</button>
  <img alt="">
  <p class="lightbox-caption"></p>
</dialog>
"""
    return page(site, nav, "/publications/", meta.get("title", "Publications"), body, "page-publications")


def author_list(authors, me):
    return ", ".join(f'<span class="me">{esc(a)}</span>' if a == me else esc(a) for a in authors)


def pub_card(p, me):
    links = {k: resolve(v, p["base"]) for k, v in p.get("links", {}).items() if v}
    main_url = links.get("paper") or links.get("publisher")  # open-access version first
    title = esc(p["title"])
    title_html = f'<a href="{esc(main_url)}" target="_blank" rel="noopener">{title}</a>' if main_url else title

    if p.get("image"):
        src = esc(resolve(p["image"], p["base"]))
        thumb = (f'<button class="pub-thumb zoomable" data-full="{src}" data-caption="{title}" '
                 f'aria-label="Enlarge figure"><img src="{src}" alt="Figure from “{title}”" loading="lazy"></button>')
    else:
        thumb = f'<div class="pub-thumb">{placeholder_svg(p["id"])}</div>'

    buttons, panels = [], []
    labels = {"paper": "PDF", "publisher": "Publisher", "slides": "Slides", "code": "Code", "video": "Video"}
    for key, label in labels.items():
        if links.get(key):
            buttons.append(f'<a class="btn" href="{esc(links[key])}"{ext_attrs(links[key])}>{label}</a>')
    if p["abstract"]:
        buttons.append(f'<button class="btn" data-toggle="abs-{p["id"]}" aria-expanded="false">Abstract</button>')
        panels.append(f'<div class="pub-panel" id="abs-{p["id"]}" hidden>{md_block(p["abstract"], p["base"])}</div>')
    if p["bibtex"]:
        buttons.append(f'<button class="btn" data-toggle="bib-{p["id"]}" aria-expanded="false">BibTeX</button>')
        panels.append(f'<div class="pub-panel bib" id="bib-{p["id"]}" hidden>'
                      f'<button class="copy" data-copy="bibtex-{p["id"]}">Copy</button>'
                      f'<pre id="bibtex-{p["id"]}">{esc(p["bibtex"])}</pre></div>')
    if not links:
        buttons.append('<span class="soon">Paper coming soon</span>')

    return f"""<article class="pub-card" data-type="{esc(p['type'])}" id="{esc(p['id'])}">
  {thumb}
  <div class="pub-body">
    <h3 class="pub-title">{title_html}</h3>
    <p class="pub-authors">{author_list(p['authors'], me)}</p>
    <p class="pub-venue"><em>{esc(p['venue'])}</em>, {p['year']}
      <span class="badge {esc(p['type'])}">{esc(p['venue_short'])}</span></p>
    <p class="pub-summary">{md_inline(p.get('summary', ''))}</p>
    <div class="pub-links">{''.join(buttons)}</div>
    {''.join(panels)}
  </div>
</article>"""


# ---------------------------------------------------------------- search

def plain(text):
    """Markdown to plain text for the search index."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", md_inline(text)))).strip()


def search_index(bio, pages):
    """One entry per paper, news item, list item (talk, student, ...) and page."""
    entries = [{"t": "Home", "u": "/", "s": "Page", "x": plain(bio)}]
    for p in load_publications():
        entries.append({"t": p["title"], "u": f"/publications/#{p['id']}", "s": TYPE_LABELS[p["type"]],
                        "m": f"{p['venue_short']} · {', '.join(p['authors'])}",
                        "x": plain(f"{p.get('summary', '')} {p['venue']} {p['abstract']}")})
    _, news_md = read_md(CONTENT / "news.md")
    for line in md_items(news_md):
        d = re.match(r"\*\*([^*]+)\*\*\s*(.*)", line, re.S)
        when, text = (d.group(1), d.group(2)) if d else ("", line)
        entries.append({"t": plain(text), "u": "/", "s": "News", "m": when, "x": ""})
    for section, meta, body in pages:
        if section == "publications":
            continue
        name, url = strip_md(meta.get("title", section.title())), f"/{section}/"
        entries.append({"t": name, "u": url, "s": "Page", "x": plain(re.sub(r"^\s*([-*+]|#).*$", "", body, flags=re.M))})
        year = ""
        for line in body.split("\n"):
            if h := re.match(r"^##\s+(.*)", line):
                year = plain(h.group(1))
            elif m := LIST_RE.match(line):
                head = re.match(r"\*\*(.+?)\*\*\s*(.*)", m.group(2))
                title, rest = (plain(head.group(1)), plain(head.group(2))) if head else (plain(m.group(2)), "")
                entries.append({"t": title, "u": url, "s": name.rstrip("s") if name.endswith("s") else name,
                                "m": year, "x": rest})
    return json.dumps(entries, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------- build

def sync(src_root, dst_root, skip=lambda p: False):
    """Copy files from src_root into dst_root, skipping those already up to date."""
    for src in src_root.rglob("*"):
        if src.is_dir() or src.name == ".DS_Store" or skip(src):
            continue
        dst = dst_root / src.relative_to(src_root)
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime and dst.stat().st_size == src.stat().st_size:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def write(path, content):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build():
    t0 = time.perf_counter()
    site, bio = read_md(CONTENT / "_index.md")
    OUT.mkdir(exist_ok=True)
    sync(STATIC, OUT)
    sync(CONTENT, OUT, skip=lambda p: p.suffix == ".md")

    # every content/<section>/index.md (or _index.md) is a page; menu order follows `weight`
    pages = []
    for f in sorted(CONTENT.glob("*/*index.md")):
        meta, body = read_md(f)
        pages.append((f.parent.name, meta, body))
    nav = [(site.get("menu", "HOME"), "/")] + [
        (m.get("menu", m.get("title", s)), f"/{s}/")
        for s, m, _ in sorted(pages, key=lambda x: x[1].get("weight", 99)) if m.get("menu")
    ]

    write("index.html", build_home(site, bio, nav))
    for section, meta, body in pages:
        if section == "publications":
            html_ = build_publications(site, nav, meta, body)
        else:
            html_ = page(site, nav, f"/{section}/", meta.get("title", section.title()),
                         f'<div class="prose">\n{md_block(body, f"/{section}/")}\n</div>', f"page-{section}")
        write(f"{section}/index.html", html_)
    write("search.json", search_index(bio, pages))
    write("404.html", page(site, nav, "", "Page not found", '<p>Sorry, this page does not exist. <a href="/">Back home</a>.</p>'))
    print(f"Built _site/ in {(time.perf_counter() - t0) * 1000:.0f} ms")


def snapshot():
    files = [ROOT / "build.py", *CONTENT.rglob("*"), *STATIC.rglob("*")]
    return {f: f.stat().st_mtime for f in files if f.is_file()}


def watch():
    state = snapshot()
    while True:
        time.sleep(1)
        new = snapshot()
        if new != state:
            if new.get(ROOT / "build.py") != state.get(ROOT / "build.py"):
                print("build.py changed, restarting…")
                os.execv(sys.executable, [sys.executable, *sys.argv])
            state = new
            try:
                build()
            except (Exception, SystemExit) as e:  # keep serving on content errors
                print(f"Build failed: {e}", file=sys.stderr)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(OUT), **kw)

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (OUT / "404.html").exists():
            body = (OUT / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().send_error(code, message, explain)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="serve _site/ locally and rebuild on changes")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    global ANALYTICS
    ANALYTICS = not args.serve
    build()
    if not args.serve:
        return
    threading.Thread(target=watch, daemon=True).start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"Serving on http://localhost:{args.port}  (Ctrl+C to stop, edits rebuild automatically)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()

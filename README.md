# Academic homepage

Static site built with a single Python script (Python 3.11+, no dependencies).

```bash
python3 build.py --serve     # build + preview at http://localhost:8000, rebuilds on every save
python3 build.py             # production build in _site/ (includes Google Analytics; --serve leaves it out)
python3 check_links.py       # check every link/image in _site/ (add --local to skip the network)
```

## Content (all Markdown)

Each `.md` file starts with a settings block between `+++` lines (TOML, as in Hugo),
followed by normal Markdown.

| What                               | Where                                        |
|------------------------------------|----------------------------------------------|
| Site settings, social links, bio   | `content/_index.md`                          |
| News (home page)                   | `content/news.md` — one `- **YYYY.MM** text` per item |
| Publications page intro            | `content/publications/_index.md`             |
| One paper                          | `content/publications/<id>/index.md` (+ `cover.jpg`, `slides.pdf`) |
| Talks / Supervision / PhD          | `content/<page>/index.md`                    |
| Styles / scripts                   | `static/css/style.css`, `static/js/site.js`  |

**Add a paper:** copy an existing folder in `content/publications/`, then edit its
`index.md`. The settings block holds title, authors, year, type, venue and links, the text
below it is the abstract, and an optional ` ```bibtex ` block gives the citation. Without
a `cover.jpg`, a coloured placeholder image is generated.

**Add a page:** create `content/<name>/index.md` with `title`, `menu` (the label in the
menu bar) and `weight` (its position in the menu). Files next to it are published at `/<name>/`.

## Deploying (GitHub Pages)

`.github/workflows/deploy.yml` builds the site and publishes it on every push to `main`.
In the repo settings, set **Pages > Source** to **GitHub Actions** and add the custom domain there.

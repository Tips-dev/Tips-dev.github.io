import csv, os, re, html
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

SITE_NAME = "ChecklistVault"

# ✅ IMPORTANT: absolute URL required for Google sitemap + canonical
BASE_URL = "https://tips-dev.github.io"

# ✅ IMPORTANT: build from the generated variants file
INPUT_CSV = "checklists_generated.csv"

# build into /site then your workflow copies site/* to repo root
OUT_DIR = "site"


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\- ]+", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def esc(s: str) -> str:
    return html.escape(s or "")


def split_items(items: str):
    if not items:
        return []
    return [i.strip() for i in items.split("|") if i.strip()]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title} | {site}</title>
  <meta name="description" content="{meta_desc}" />
  <link rel="canonical" href="{canonical}" />
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 24px; max-width: 860px; }}
    a {{ color: inherit; }}
    header a {{ text-decoration: none; }}
    .crumbs {{ font-size: 14px; opacity: .75; margin-bottom: 12px; }}
    h1 {{ margin: 6px 0 8px; }}
    .intro {{ margin: 0 0 18px; line-height: 1.45; }}
    .box {{ border: 1px solid #e6e6e6; border-radius: 10px; padding: 16px; margin: 16px 0; }}
    ul {{ margin: 10px 0 0 18px; }}
    li {{ margin: 6px 0; }}
    .related a {{ display: inline-block; margin: 6px 10px 0 0; padding: 8px 10px; border: 1px solid #eee; border-radius: 999px; text-decoration:none; }}
    .print {{ display:inline-block; margin-top: 10px; padding: 10px 12px; border:1px solid #ddd; border-radius: 10px; text-decoration:none; }}
    footer {{ margin-top: 28px; font-size: 13px; opacity: .75; }}
    @media print {{
      .print, .related, header, footer {{ display:none !important; }}
      body {{ margin: 0; }}
      .box {{ border: none; padding: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="crumbs">
      <a href="{home_url}">{site}</a> › <a href="{category_url}">{category_label}</a>
    </div>
  </header>

  <h1>{title}</h1>
  <p class="intro">{intro}</p>
  <a class="print" href="#" onclick="window.print();return false;">Print this checklist</a>

  <section class="box">
    <h2>{s1_title}</h2>
    <ul>
      {s1_list}
    </ul>
  </section>

  <section class="box">
    <h2>{s2_title}</h2>
    <ul>
      {s2_list}
    </ul>
  </section>

  <section class="related">
    <h3>Related checklists</h3>
    {related_links}
  </section>

  <footer>
    Updated {updated}. <a href="{all_url}">Browse all checklists</a>.
  </footer>
</body>
</html>
"""


INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{site} | Free Printable Checklists</title>
  <meta name="description" content="Free printable checklists for real life: moving, travel, emergency, college, pets, and more." />
  <link rel="canonical" href="{home_url}" />
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 24px; max-width: 920px; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .card {{ border:1px solid #e6e6e6; border-radius: 12px; padding: 14px; }}
    .card a {{ text-decoration:none; }}
    .muted {{ opacity:.75; font-size: 14px; }}
    ul {{ margin: 10px 0 0 18px; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <h1>{site}</h1>
  <p class="muted">Free printable checklists. Pick a category below.</p>

  <div class="grid">
    {category_cards}
  </div>

  <h2 style="margin-top:22px;">All checklists</h2>
  <ul>
    {all_links}
  </ul>

  <p class="muted" style="margin-top:18px;">Updated {updated}.</p>
</body>
</html>
"""


def main():
    rows = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r = {k.strip(): (v or "").strip() for k, v in r.items()}
            if not r.get("slug") or not r.get("title"):
                continue
            r["slug"] = slugify(r["slug"])
            r["category"] = slugify(r.get("category", "general"))
            rows.append(r)

    if not rows:
        raise SystemExit(f"No rows found in {INPUT_CSV}")

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    ensure_dir(OUT_DIR)
    ensure_dir(os.path.join(OUT_DIR, "checklists"))

    # group by category for hubs + related links
    cats = {}
    for r in rows:
        cats.setdefault(r["category"], []).append(r)

    # generate checklist pages
    for r in rows:
        slug = r["slug"]
        title = r["title"]
        category = r["category"]

        intro = r.get("intro", "Printable checklist.")
        s1_title = r.get("section1_title", "Essentials") or "Essentials"
        s2_title = r.get("section2_title", "Nice to Have") or "Nice to Have"

        s1_items = split_items(r.get("section1_items", ""))
        s2_items = split_items(r.get("section2_items", ""))

        s1_list = "\n      ".join(f"<li>{esc(x)}</li>" for x in s1_items) if s1_items else "<li>(Add items)</li>"
        s2_list = "\n      ".join(f"<li>{esc(x)}</li>" for x in s2_items) if s2_items else "<li>(Add items)</li>"

        # related links = same category, up to 8
        related = []
        for rr in cats.get(category, [])[:8]:
            if rr["slug"] == slug:
                continue
            related.append(f'<a href="{BASE_URL}/checklists/{rr["slug"]}/">{esc(rr["title"])}</a>')
        related_links = "\n    ".join(related) if related else ""

        page_dir = os.path.join(OUT_DIR, "checklists", slug)
        ensure_dir(page_dir)

        canonical = f"{BASE_URL}/checklists/{slug}/"
        category_url = f"{BASE_URL}/checklists/{category}/"

        page_html = PAGE_TEMPLATE.format(
            title=esc(title),
            site=esc(SITE_NAME),
            meta_desc=esc(intro[:155]),
            canonical=canonical,
            intro=esc(intro),
            s1_title=esc(s1_title),
            s1_list=s1_list,
            s2_title=esc(s2_title),
            s2_list=s2_list,
            related_links=related_links,
            updated=updated,
            home_url=f"{BASE_URL}/",
            category_url=category_url,
            category_label=esc(category),
            all_url=f"{BASE_URL}/",
        )

        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page_html)

    # category hub pages
    for cat, items in cats.items():
        hub_dir = os.path.join(OUT_DIR, "checklists", cat)
        ensure_dir(hub_dir)

        links = []
        for r in items:
            links.append(f'<li><a href="{BASE_URL}/checklists/{r["slug"]}/">{esc(r["title"])}</a></li>')

        hub_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{esc(cat)} checklists | {esc(SITE_NAME)}</title>
<meta name="description" content="Free printable {esc(cat)} checklists." />
<link rel="canonical" href="{BASE_URL}/checklists/{cat}/" />
</head>
<body>
<p><a href="{BASE_URL}/">{esc(SITE_NAME)}</a></p>
<h1>{esc(cat)} checklists</h1>
<ul>
{''.join(links)}
</ul>
</body>
</html>
"""
        with open(os.path.join(hub_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(hub_html)

    # homepage
    category_cards = []
    for cat, items in sorted(cats.items(), key=lambda x: (-len(x[1]), x[0])):
        category_cards.append(
            f'<div class="card"><a href="{BASE_URL}/checklists/{cat}/"><strong>{esc(cat)}</strong></a>'
            f'<div class="muted">{len(items)} checklists</div></div>'
        )

    all_links = []
    for r in rows:
        all_links.append(f'<li><a href="{BASE_URL}/checklists/{r["slug"]}/">{esc(r["title"])}</a></li>')

    index_html = INDEX_TEMPLATE.format(
        site=esc(SITE_NAME),
        category_cards="".join(category_cards),
        all_links="".join(all_links),
        updated=updated,
        home_url=f"{BASE_URL}/",
    )

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # robots.txt (absolute sitemap URL)
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    # ✅ VALID XML sitemap with absolute URLs
    urls = [f"{BASE_URL}/"]
    urls += [f"{BASE_URL}/checklists/{cat}/" for cat in cats.keys()]
    urls += [f"{BASE_URL}/checklists/{r['slug']}/" for r in rows]

    sitemap_lines = []
    sitemap_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    sitemap_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for u in urls:
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{xml_escape(u)}</loc>")
        sitemap_lines.append(f"    <lastmod>{updated}</lastmod>")
        sitemap_lines.append("  </url>")

    sitemap_lines.append("</urlset>")

    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))

    print(f"Generated {len(rows)} checklist pages + {len(cats)} category hubs into ./{OUT_DIR}/")


if __name__ == "__main__":
    main()

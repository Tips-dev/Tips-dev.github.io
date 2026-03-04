import csv, os, re, html
from datetime import datetime

SITE_NAME = "ChecklistVault"
BASE_URL = ""  # leave blank for relative links on GitHub Pages
INPUT_CSV = "checklists.csv"
OUT_DIR = "site"

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\- ]+", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-{2,}", "-", s)
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
    # Read CSV
    rows = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize keys just in case
            r = {k.strip(): (v or "").strip() for k, v in r.items()}
            if not r.get("slug") or not r.get("title"):
                continue
            r["slug"] = slugify(r["slug"])
            r["category"] = slugify(r.get("category", "general") or "general")
            rows.append(r)

    if not rows:
        raise SystemExit("No rows found in checklists.csv")

    ensure_dir(OUT_DIR)
    ensure_dir(os.path.join(OUT_DIR, "checklists"))

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    # Build category index
    cats = {}
    for r in rows:
        cats.setdefault(r["category"], []).append(r)

    # Create category hub pages
    for cat, items in cats.items():
        hub_dir = os.path.join(OUT_DIR, "checklists", cat)
        ensure_dir(hub_dir)
        hub_path = os.path.join(hub_dir, "index.html")

        links = []
        for it in sorted(items, key=lambda x: x["title"].lower()):
            url = f"{BASE_URL}/checklists/{it['slug']}/"
            links.append(f'<li><a href="{url}">{esc(it["title"])}</a></li>')

        hub_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(cat.title())} Checklists | {SITE_NAME}</title>
  <meta name="description" content="Printable {esc(cat)} checklists." />
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin:24px; max-width: 860px; }}
    a {{ color: inherit; }}
    .muted {{ opacity:.75; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <p class="muted"><a href="{BASE_URL}/">{SITE_NAME}</a> › {esc(cat.title())}</p>
  <h1>{esc(cat.title())} Checklists</h1>
  <ul>
    {''.join(links)}
  </ul>
  <p class="muted"><a href="{BASE_URL}/">Back home</a></p>
</body>
</html>
"""
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(hub_html)

    # Create individual checklist pages
    for r in rows:
        slug = r["slug"]
        title = r["title"]
        category = r["category"]
        intro = r.get("intro", "").strip() or "Printable checklist."
        s1_title = r.get("section1_title", "").strip() or "Essentials"
        s2_title = r.get("section2_title", "").strip() or "Nice to Have"
        s1_items = split_items(r.get("section1_items", ""))
        s2_items = split_items(r.get("section2_items", ""))

        # Basic meta description: intro truncated
        meta_desc = (intro[:155] + "...") if len(intro) > 158 else intro

        # Related: same category, pick first 8 excluding self
        related = [x for x in cats.get(category, []) if x["slug"] != slug]
        related = sorted(related, key=lambda x: x["title"].lower())[:8]
        related_links = " ".join(
            f'<a href="{BASE_URL}/checklists/{x["slug"]}/">{esc(x["title"])}</a>' for x in related
        ) or '<span class="muted">More coming soon.</span>'

        s1_list = "\n".join(f"<li>{esc(it)}</li>" for it in s1_items) or "<li>—</li>"
        s2_list = "\n".join(f"<li>{esc(it)}</li>" for it in s2_items) or "<li>—</li>"

        page_dir = os.path.join(OUT_DIR, "checklists", slug)
        ensure_dir(page_dir)
        page_path = os.path.join(page_dir, "index.html")

        url = f"{BASE_URL}/checklists/{slug}/"
        canonical = url  # relative canonical is fine for GH Pages; you can replace later

        html_out = PAGE_TEMPLATE.format(
            title=esc(title),
            site=esc(SITE_NAME),
            meta_desc=esc(meta_desc),
            canonical=esc(canonical),
            home_url=f"{BASE_URL}/",
            all_url=f"{BASE_URL}/#all",
            category_url=f"{BASE_URL}/checklists/{category}/",
            category_label=esc(category.title()),
            intro=esc(intro),
            s1_title=esc(s1_title),
            s1_list=s1_list,
            s2_title=esc(s2_title),
            s2_list=s2_list,
            related_links=related_links,
            updated=esc(updated),
        )

        with open(page_path, "w", encoding="utf-8") as f:
            f.write(html_out)

    # Create home index with category cards + all links
    category_cards = []
    for cat in sorted(cats.keys()):
        count = len(cats[cat])
        category_cards.append(
            f'''<div class="card">
  <a href="{BASE_URL}/checklists/{cat}/"><strong>{esc(cat.title())}</strong></a>
  <div class="muted">{count} checklists</div>
</div>'''
        )

    all_links = []
    for r in sorted(rows, key=lambda x: x["title"].lower()):
        all_links.append(f'<li><a href="{BASE_URL}/checklists/{r["slug"]}/">{esc(r["title"])}</a></li>')

    index_html = INDEX_TEMPLATE.format(
        site=esc(SITE_NAME),
        category_cards="\n".join(category_cards),
        all_links="\n".join(all_links),
        updated=esc(updated),
    )

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # robots.txt
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n")

    # sitemap.xml
    urls = [f"{BASE_URL}/"] + [f"{BASE_URL}/checklists/{cat}/" for cat in cats.keys()] + [
        f"{BASE_URL}/checklists/{r['slug']}/" for r in rows
    ]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{esc(u)}</loc>")
        sitemap.append(f"    <lastmod>{updated}</lastmod>")
        sitemap.append("  </url>")
    sitemap.append("</urlset>")

    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))

    print(f"Generated {len(rows)} pages + hubs into ./{OUT_DIR}/")

if __name__ == "__main__":
    main()

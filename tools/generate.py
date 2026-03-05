import csv
import os
import re
import html
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

BASE_URL = "https://tips-dev.github.io"
INPUT_CSV = "checklists_generated.csv"
OUT_DIR = "site"

SITE_NAME = "ChecklistVault"

# How many URLs per sitemap chunk (Google limit is 50,000; keep buffer)
SITEMAP_MAX_URLS = 45000


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def safe(s: str) -> str:
    return html.escape(s or "", quote=True)


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def render_page(title: str, description: str, h1: str, items: list[str], canonical_url: str) -> str:
    items_html = "\n".join([f"<li>{safe(x)}</li>" for x in items if (x or "").strip()])
    meta_desc = safe(description)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe(title)}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{safe(canonical_url)}">
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
    header {{ padding: 24px 16px; border-bottom: 1px solid #eee; }}
    main {{ max-width: 900px; margin: 0 auto; padding: 24px 16px; }}
    .card {{ border: 1px solid #eee; border-radius: 12px; padding: 16px; }}
    ul {{ padding-left: 20px; }}
    footer {{ padding: 24px 16px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
  </style>
</head>
<body>
  <header><strong>{SITE_NAME}</strong></header>
  <main>
    <h1>{safe(h1)}</h1>
    <p>{meta_desc}</p>
    <div class="card">
      <h2>Checklist</h2>
      <ul>{items_html}</ul>
    </div>
    <p style="margin-top: 18px;"><a href="{BASE_URL}/">← Back to home</a></p>
  </main>
  <footer>© {datetime.utcnow().year} {SITE_NAME}</footer>
</body>
</html>
"""


def render_category_page(cat: str, pages: list[dict]) -> str:
    cat_title = cat.replace("-", " ").title()
    title = f"{cat_title} Checklists | {SITE_NAME}"
    description = f"Browse printable {cat_title.lower()} checklists. Fast, simple, and free."
    canonical = f"{BASE_URL}/checklists/{cat}/"

    links_html = "\n".join(
        [f'<li><a href="{safe(p["url"])}">{safe(p["name"])}</a></li>' for p in pages]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe(title)}</title>
  <meta name="description" content="{safe(description)}">
  <link rel="canonical" href="{safe(canonical)}">
</head>
<body>
  <h1>{safe(cat_title)} Checklists</h1>
  <p>{safe(description)}</p>
  <ul>{links_html}</ul>
  <p><a href="{BASE_URL}/">← Back to home</a></p>
</body>
</html>
"""


def render_home(cats: dict) -> str:
    title = f"{SITE_NAME} | Printable Checklists"
    description = "Printable checklists for life, travel, home, work, and more. Free and easy to use."
    canonical = f"{BASE_URL}/"

    cat_links = "\n".join(
        [f'<li><a href="{BASE_URL}/checklists/{safe(c)}/">{safe(c.replace("-", " ").title())}</a></li>'
         for c in sorted(cats.keys())]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe(title)}</title>
  <meta name="description" content="{safe(description)}">
  <link rel="canonical" href="{safe(canonical)}">
</head>
<body>
  <h1>Printable Checklists</h1>
  <p>{safe(description)}</p>
  <h2>Categories</h2>
  <ul>{cat_links}</ul>
</body>
</html>
"""


def write_urlset(path: str, url_list: list[str], lastmod: str) -> None:
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in url_list:
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(u)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    ensure_dir(OUT_DIR)
    ensure_dir(os.path.join(OUT_DIR, "checklists"))

    rows = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            slug = (r.get("slug") or "").strip() or slugify(name)
            category = slugify((r.get("category") or "").strip() or "general")
            description = (r.get("description") or "").strip() or f"Printable {name.lower()} checklist."
            items_raw = (r.get("items") or "").strip()

            if "|" in items_raw:
                items = [x.strip() for x in items_raw.split("|")]
            else:
                items = [x.strip() for x in items_raw.splitlines()]

            rows.append(
                {"name": name, "slug": slugify(slug), "category": category, "description": description, "items": items}
            )

    # group by category
    cats: dict[str, list[dict]] = {}
    for r in rows:
        cats.setdefault(r["category"], []).append(r)

    # pages
    for r in rows:
        out_dir = os.path.join(OUT_DIR, "checklists", r["slug"])
        ensure_dir(out_dir)

        canonical = f"{BASE_URL}/checklists/{r['slug']}/"
        title = f"{r['name']} | {SITE_NAME}"
        html_doc = render_page(title, r["description"], r["name"], r["items"], canonical)

        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)

    # category hubs
    for cat, pages in cats.items():
        out_dir = os.path.join(OUT_DIR, "checklists", cat)
        ensure_dir(out_dir)

        cat_pages = sorted(
            [{"name": p["name"], "url": f"{BASE_URL}/checklists/{p['slug']}/"} for p in pages],
            key=lambda x: x["name"].lower(),
        )

        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_category_page(cat, cat_pages))

    # home
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_home(cats))

    # robots.txt
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    # ✅ sitemap index + chunks
    lastmod = datetime.utcnow().strftime("%Y-%m-%d")

    urls = [f"{BASE_URL}/"]
    urls += [f"{BASE_URL}/checklists/{cat}/" for cat in sorted(cats.keys())]
    urls += [f"{BASE_URL}/checklists/{r['slug']}/" for r in rows]

    sitemap_files: list[str] = []
    for i in range(0, len(urls), SITEMAP_MAX_URLS):
        part_num = (i // SITEMAP_MAX_URLS) + 1
        filename = f"sitemap-pages-{part_num}.xml"
        write_urlset(os.path.join(OUT_DIR, filename), urls[i:i + SITEMAP_MAX_URLS], lastmod)
        sitemap_files.append(filename)

    index_lines = []
    index_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    index_lines.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for fn in sitemap_files:
        index_lines.append("  <sitemap>")
        index_lines.append(f"    <loc>{xml_escape(f'{BASE_URL}/{fn}')}</loc>")
        index_lines.append(f"    <lastmod>{lastmod}</lastmod>")
        index_lines.append("  </sitemap>")
    index_lines.append("</sitemapindex>")

    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    print(f"Generated {len(rows)} pages, {len(cats)} categories, {len(sitemap_files)} sitemap chunk(s).")


if __name__ == "__main__":
    main()

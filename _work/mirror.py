#!/usr/bin/env python3
"""Mirror groupleads.framer.website into a self-contained local site."""
import os, re, sys, time, pathlib, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

WORK = pathlib.Path(__file__).resolve().parent
ROOT = WORK.parent                      # ~/Documents/groupleads-site
ASSETS = ROOT / "assets"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125 Safari/537.36")

PAGES = ["home", "pricing", "features", "integrations", "compare", "resellers",
         "affiliates", "testimonials", "termsofuse", "privacypolicy", "contact",
         "vs-group-convert", "vs-group-funnels", "vs-group-boss",
         "vs-group-collector", "vs-group-kit", "vs-groupx", "vs-group-doorman",
         "vs-group-pro", "vs-social-tribes", "vs-group-buddy",
         "vs-group-answer-collector", "vs-group-track"]

# generic path-only URLs (query stripped → original full-size resource served)
URL_RE = re.compile(r"https://(?:framerusercontent\.com|fonts\.gstatic\.com)/[A-Za-z0-9_\-./%]+")
# special single-variant querystring resources
SPECIALS = {
    "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap":
        "fonts.googleapis.com/css2.css",
    "https://events.framer.com/script?v=2":
        "events.framer.com/script.js",
}
TEXT_EXT = {".mjs", ".js", ".css", ".json", ".svg", ".html", ".txt", ".xml"}

def local_path(url):
    p = urllib.parse.urlparse(url)
    return ASSETS / p.netloc / p.path.lstrip("/")

def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            dest.write_bytes(data)
            return "ok"
        except Exception as e:
            if attempt == 3:
                return f"FAIL {e}"
            time.sleep(1.5 * (attempt + 1))

def scan_text(content, base_url=None):
    """Find downloadable URLs in text. base_url = URL the text came from (for relative .mjs imports)."""
    found = set(URL_RE.findall(content))
    if base_url and base_url.endswith(".mjs"):
        base_dir = base_url.rsplit("/", 1)[0] + "/"
        for m in re.findall(r"""["'](\.?\.?/?[A-Za-z0-9_\-./]+\.mjs)["']""", content):
            found.add(urllib.parse.urljoin(base_dir, m))
    return {u for u in found if "/" in urllib.parse.urlparse(u).path.lstrip("/") or
            urllib.parse.urlparse(u).path.lstrip("/")}

def main():
    # ---- round 0: collect from page HTML ----
    queue = set()
    page_html = {}
    for name in PAGES:
        html = (WORK / f"{name}.html").read_text(encoding="utf-8")
        page_html[name] = html
        queue |= scan_text(html, None)
        for s in SPECIALS:
            if s in html or s.replace("&", "&amp;") in html:
                queue.add(s)

    downloaded = {}
    failures = []
    round_no = 0
    while queue:
        round_no += 1
        batch = sorted(queue - set(downloaded))
        queue = set()
        if not batch:
            break
        print(f"-- round {round_no}: {len(batch)} urls")
        def job(u):
            dest = ASSETS / SPECIALS[u] if u in SPECIALS else local_path(u)
            return u, dest, fetch(u, dest)
        with ThreadPoolExecutor(max_workers=16) as ex:
            for fut in as_completed([ex.submit(job, u) for u in batch]):
                u, dest, status = fut.result()
                if status.startswith("FAIL"):
                    failures.append(f"{u} {status}")
                    continue
                downloaded[u] = dest
                if dest.suffix.lower() in TEXT_EXT:
                    try:
                        txt = dest.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
                    queue |= scan_text(txt, u) - set(downloaded)
    print(f"downloaded {len(downloaded)} assets, {len(failures)} failures")
    for f in failures:
        print("  !!", f)

    # ---- rewrite downloaded text assets ----
    repl_map = {}  # absolute url (no query) -> local Path
    for u, dest in downloaded.items():
        key = u.split("?")[0] if u not in SPECIALS else u
        repl_map.setdefault(key, dest)

    def rewrite(content, from_dir):
        for url, dest in sorted(repl_map.items(), key=lambda kv: -len(kv[0])):
            rel = os.path.relpath(dest, from_dir).replace(os.sep, "/")
            content = content.replace(url.replace("&", "&amp;"), rel)
            content = content.replace(url, rel)
        return content

    for u, dest in list(downloaded.items()):
        if dest.suffix.lower() in TEXT_EXT:
            try:
                txt = dest.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new = rewrite(txt, dest.parent)
            if new != txt:
                dest.write_text(new, encoding="utf-8")

    # ---- write pages & rewrite their URLs + internal links ----
    for name, html in page_html.items():
        if name == "home":
            out, depth_dir = ROOT / "index.html", ROOT
        else:
            out, depth_dir = ROOT / name / "index.html", ROOT / name
        out.parent.mkdir(parents=True, exist_ok=True)
        html = rewrite(html, depth_dir)
        if name != "home":
            # ./pricing → ../pricing/ etc. (pages live one level deep)
            html = re.sub(r'href="\./(?=[a-z])', 'href="../', html)
            html = html.replace('href="./"', 'href="../"')
            html = html.replace('href="./#', 'href="../#')
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")

    print("DONE")

if __name__ == "__main__":
    main()

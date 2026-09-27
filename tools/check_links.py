"""Link checker for the built site (stdlib only).

Parses every HTML file in site/ and checks that each local reference resolves to a real
file inside site/, as it would when served from the GitHub Pages project subpath
(https://<user>.github.io/ankle360-poc/). Fragments (#id) must match an id on the target page.

404.html is also resolved as if served at a nested missing URL (GitHub Pages serves it
for any missing path at any depth), so its references must not depend on the request path.

Checked: <a href>, <img src/srcset>, <source src/srcset>, <link href>, <script src>,
<video poster>, <iframe src>. <base href> is honored.
Skipped: external http(s):// and protocol-relative links, mailto:, tel:, data:.
Form actions aren't followed (they're Shopify endpoints the prototype's JS intercepts),
but root-absolute ones are listed for review.

Usage: python3 tools/check_links.py [site_dir] [--base-path /ankle360-poc/]
Exits 1 if any reference is broken."""
import sys, pathlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote

CHECKED = {
    "a": ("href",), "img": ("src", "srcset"), "source": ("src", "srcset"), "link": ("href",),
    "script": ("src",), "video": ("poster",), "iframe": ("src",),
}
SKIP_SCHEMES = ("http", "https", "mailto", "tel", "data")
HOST = "pages.invalid"  # stand-in origin used to resolve URLs like a browser would
ANY_DEPTH = {"404.html": "nope/deeper/missing"}  # page -> an extra URL path it's served at


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.refs, self.forms, self.base = set(), [], [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("id", "name") if tag == "a" else ("id",):
            if a.get(key):
                self.ids.add(a[key])
        if tag == "base" and a.get("href") and self.base is None:
            self.base = a["href"]
        if tag == "form" and a.get("action", "").startswith("/"):
            self.forms.append((self.getpos()[0], a["action"]))
        for attr in CHECKED.get(tag, ()):
            val = a.get(attr)
            if val is None:
                continue
            urls = [c.strip().split()[0] for c in val.split(",") if c.strip()] if attr == "srcset" else [val.strip()]
            self.refs.extend((self.getpos()[0], tag, attr, u) for u in urls)

    handle_startendtag = handle_starttag


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    base_path = "/ankle360-poc/"
    if "--base-path" in argv:
        base_path = argv[argv.index("--base-path") + 1]
        args.remove(base_path)
    base_path = "/" + base_path.strip("/") + "/" if base_path.strip("/") else "/"
    site = pathlib.Path(args[0] if args else pathlib.Path(__file__).resolve().parent.parent / "site").resolve()
    if not site.is_dir():
        sys.exit(f"check_links: {site} not found. Run build.py first.")

    pages = {}
    for f in sorted(site.rglob("*.html")):
        p = Page(); p.feed(f.read_text(encoding="utf-8")); pages[f] = p

    def target_file(path):
        rel = unquote(path[len(base_path):])
        t = (site / rel).resolve()
        if t.is_dir() or path.endswith("/"):
            t = t / "index.html"
        return t

    broken, checked, skipped, forms = [], 0, 0, []
    for f, p in pages.items():
        rel = f.relative_to(site).as_posix()
        forms += [(rel, line, action) for line, action in p.forms]
        served_at = [rel] + ([ANY_DEPTH[rel]] if rel in ANY_DEPTH else [])
        for (line, tag, attr, ref), url_path in ((r, u) for u in served_at for r in p.refs):
            page_url = f"https://{HOST}{base_path}{url_path}"
            doc_url = urljoin(page_url, p.base) if p.base else page_url
            where = f"{rel}:{line} <{tag} {attr}=\"{ref}\">" + (f" (served at {base_path}{url_path})" if url_path != rel else "")
            scheme = urlsplit(ref).scheme.lower()
            if scheme in SKIP_SCHEMES or ref.startswith("//"):
                skipped += 1
                continue
            checked += 1
            if scheme:
                broken.append(f"{where}: unsupported scheme '{scheme}:'"); continue
            if ref.startswith("#") and not p.base:  # same-page fragment, whatever URL serves the page
                if ref != "#" and unquote(ref[1:]) not in p.ids:
                    broken.append(f"{where}: no id=\"{unquote(ref[1:])}\" on this page")
                continue
            url = urlsplit(urljoin(doc_url, ref))
            if not url.path.startswith(base_path):
                broken.append(f"{where}: resolves to {url.path}, outside the site at {base_path}"); continue
            target = target_file(url.path)
            if site not in target.parents and target != site:
                broken.append(f"{where}: escapes site/"); continue
            if not target.is_file():
                broken.append(f"{where}: missing file {target.relative_to(site).as_posix()}"); continue
            if url.fragment:
                page = pages.get(target)
                if page is None:
                    broken.append(f"{where}: #{url.fragment} points into a non-HTML file")
                elif unquote(url.fragment) not in page.ids:
                    broken.append(f"{where}: no id=\"{unquote(url.fragment)}\" in {target.relative_to(site).as_posix()}")

    print(f"check_links: {len(pages)} pages, {checked} local references checked, {skipped} external/skipped, base path {base_path}")
    if forms:
        print("Root-absolute form actions (intentional Shopify endpoints, not checked):")
        for rel, line, action in forms:
            print(f"  {rel}:{line} action=\"{action}\"")
    if broken:
        print(f"{len(broken)} broken reference(s):")
        for b in broken:
            print("  " + b)
        return 1
    print("All local references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

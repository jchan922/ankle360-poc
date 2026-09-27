"""POC build: assembles layout + partials + pages into site/ (deployable to GitHub Pages)
and preview/ (single-file pages with CSS, JS, and images inlined).
Also generates the temporary illustrations in assets/img/.
In Shopify, layout/theme.liquid + sections do this assembly and images come from Shopify media."""
import os, re, pathlib, shutil, base64

ROOT = pathlib.Path(__file__).parent
# URL path the site is served from. GitHub Pages project sites live under /<repo>/.
BASE_PATH = "/" + os.environ.get("SITE_BASE_PATH", "/ankle360-poc/").strip("/") + "/"
read = lambda p: (ROOT / p).read_text()

COLORWAYS = {
    "ember":    dict(rim="#F0522A", face="#2E2F31", center="#2E2F31", groove="rgba(241,241,236,.14)", label="rgba(241,241,236,.55)"),
    "blaze":    dict(rim="#F0522A", face="#F0522A", center="#E34A23", groove="rgba(28,30,32,.16)",  label="rgba(28,30,32,.5)"),
    "target":   dict(rim="#2E2F31", face="#2E2F31", center="#F0522A", groove="rgba(241,241,236,.14)", label="rgba(28,30,32,.55)"),
    "concrete": dict(rim="#F2C21B", face="#A7A9A6", center="#A7A9A6", groove="rgba(28,30,32,.16)",  label="rgba(28,30,32,.5)"),
}

def style_vars(cw):
    c = COLORWAYS[cw]
    return (f'<style>svg{{--disc-rim:{c["rim"]};--disc-face:{c["face"]};--disc-center:{c["center"]};'
            f'--disc-groove:{c["groove"]};--disc-label:{c["label"]};--color-speckle:#1C1E20}}</style>')

def speckle_pattern(pid="speckle"):
    rng, dots = 7, []
    for _ in range(38):
        rng = (rng * 1103515245 + 12345) % 2**31; x = rng % 120
        rng = (rng * 1103515245 + 12345) % 2**31; y = rng % 120
        rng = (rng * 1103515245 + 12345) % 2**31; r = 0.6 + (rng % 10) / 10
        dots.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}"/>')
    return f'<pattern id="{pid}" width="120" height="120" patternUnits="userSpaceOnUse"><g fill="var(--color-speckle)" opacity=".55">{"".join(dots)}</g></pattern>'

def disc_top_body():
    grooves = "".join(f'<circle cx="200" cy="200" r="{r}" fill="none" stroke="var(--disc-groove)" stroke-width="2.6"/>' for r in range(92, 180, 7))
    return f'''<circle cx="200" cy="200" r="198" fill="var(--disc-rim)"/>
<circle cx="200" cy="200" r="184" fill="var(--disc-face)"/>{grooves}
<rect x="14" y="194" width="372" height="12" fill="var(--disc-face)"/>
<path d="M62 196l8 8 8-8M322 204l8-8 8 8" fill="none" stroke="var(--disc-label)" stroke-width="2"/>
<circle cx="200" cy="200" r="80" fill="var(--disc-center)"/>
<text x="200" y="207" text-anchor="middle" font-family="Schibsted Grotesk, Helvetica, Arial, sans-serif" font-size="18" letter-spacing="5" fill="var(--disc-label)">ANKLE360</text>
<circle cx="200" cy="200" r="198" fill="url(#speckle)"/>'''

CX, RX, RY = 300, 230, 72
def slab(cy, h, grooves=False, face="var(--disc-face)", side="var(--disc-rim)", rim="var(--disc-rim)", cx=CX, rx=RX, ry=RY):
    l, r = cx - rx, cx + rx
    body = f'M{l} {cy} A{rx} {ry} 0 0 0 {r} {cy} V{cy+h} A{rx} {ry} 0 0 1 {l} {cy+h} Z'
    out = [f'<path d="{body}" fill="{side}"/>', f'<path d="{body}" fill="url(#speckle)"/>',
           f'<path d="M{l} {cy+h} A{rx} {ry} 0 0 0 {r} {cy+h}" fill="none" stroke="rgba(28,30,32,.35)" stroke-width="2"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{rim}"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="{rx-rx*0.06:.0f}" ry="{ry-ry*0.07:.0f}" fill="{face}"/>']
    if grooves:
        for gx in range(int(rx*0.42), int(rx*0.92), max(4, int(rx*0.043))):
            out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{gx}" ry="{gx*ry/rx:.1f}" fill="none" stroke="var(--disc-groove)" stroke-width="2"/>')
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.34:.0f}" ry="{rx*0.34*ry/rx:.1f}" fill="var(--disc-center)"/>')
    return "".join(out)

def base(cy):
    return (f'<path d="M226 {cy+30} Q{CX} {cy+250} 374 {cy+30} Z" fill="#3A3C3F" stroke="rgba(241,241,236,.28)" stroke-width="1.5"/>'
            + slab(cy, 30, face="#55585B", side="#434548", rim="#434548")
            + f'<ellipse cx="{CX}" cy="{cy}" rx="{RX}" ry="{RY}" fill="none" stroke="rgba(241,241,236,.28)" stroke-width="1.5"/>')

def magnets(cy):
    pts = [(CX-150, cy), (CX+150, cy), (CX, cy-47), (CX, cy+47)]
    return "".join(f'<rect x="{x-11}" y="{y-10}" width="22" height="10" fill="#8E908D"/><ellipse cx="{x}" cy="{y}" rx="11" ry="4.5" fill="#C9CAC4"/><ellipse cx="{x}" cy="{y-10}" rx="11" ry="4.5" fill="#E2E3DE"/>' for x, y in pts)

def stack_body(n, b=300):
    return base(b) + "".join(slab(b - 26 * (i + 1), 24, grooves=(i == n - 1)) for i in range(n))

def stack_inline(n):
    b = 300; top = b - 26 * n - RY - 10
    return f'<svg class="level__stack" viewBox="60 {top} 480 {b+150-top}" aria-hidden="true" data-colorway="ember">{stack_body(n)}</svg>'

def exploded_svg():
    b = 400
    return f'''<svg class="exploded__figure" viewBox="0 -70 600 680" role="img" aria-labelledby="exploded-title exploded-desc" data-colorway="ember">
  <title id="exploded-title">ANKLE360 disc, exploded view</title>
  <desc id="exploded-desc">From bottom to top: a dome base, four magnets, and three stacking rings, the top ring with a grooved grip surface.</desc>
  <g class="exploded__layer" style="--shift: 0px">{base(b)}</g>
  <g class="exploded__layer exploded__magnets" style="--shift: -18px">{magnets(b)}</g>
  <g class="exploded__layer" style="--shift: -110px">{slab(b-26, 24)}</g>
  <g class="exploded__layer" style="--shift: -190px">{slab(b-52, 24)}</g>
  <g class="exploded__layer" style="--shift: -270px">{slab(b-78, 24, grooves=True)}</g>
</svg>'''

# ---------- Temporary scene illustrations (replace with photography) ----------
SCENES = {
    # name: wall, floor, floor detail, leg, shoe, sock, colorway  (moody, spotlit)
    "hero-gym":       ("#1B1C1E", "#0E0F10", "rubber", "#141414", "#F4F4F2", "#F4F4F2", "ember"),
    "in-use-studio":  ("#2A2B2D", "#1A1B1C", "plain",  "#8D5B3E", "#FF4F1F", "#F4F4F2", "ember"),
    "story-soccer":   ("#1E2A33", "#2F4A2A", "grass",  "#C68863", "#F4F4F2", "#F4F4F2", "blaze"),
    "story-trail":    ("#3A3F3A", "#4A3C2E", "dirt",   "#141414", "#FF4F1F", "#C9CAC4", "concrete"),
    "story-court":    ("#2B2E33", "#8C6A45", "court",  "#5A3A28", "#F4F4F2", "#F4F4F2", "target"),
    "story-lifter":   ("#1B1C1E", "#0E0F10", "rubber", "#E0B08E", "#141414", "#141414", "ember"),
    "story-hiker":    ("#34403A", "#4E4436", "dirt",   "#8D5B3E", "#4A4E52", "#B5B7B2", "blaze"),
    "story-home":     ("#3A3430", "#6E5236", "wood",   "#E0B08E", "#FF4F1F", "#F4F4F2", "target"),
}

def scene(name, w=800, h=600, dx=0, dy=0):
    wall, floor, detail, leg, shoe, sock, cw = SCENES[name]
    top = -dy
    d = []
    if detail == "wood":
        d = [f'<path d="M0 {y} H800" stroke="rgba(28,30,32,.12)" stroke-width="2"/>' for y in (420, 470, 530, 590)]
    elif detail == "court":
        d = ['<path d="M0 450 H800" stroke="#F0522A" stroke-width="6" opacity=".7"/>']
    elif detail == "grass":
        d = [f'<path d="M{x} 600 l6 -24 l4 24" fill="#4E7A3E"/>' for x in range(0, 800, 37)]
    elif detail == "dirt":
        d = ['<ellipse cx="120" cy="560" rx="40" ry="14" fill="rgba(28,30,32,.18)"/>', '<ellipse cx="700" cy="520" rx="28" ry="10" fill="rgba(28,30,32,.15)"/>']
    elif detail == "rubber":
        d = [f'<path d="M{x} 380 L{x*1.6-240} 600" stroke="rgba(241,241,236,.05)" stroke-width="2"/>' for x in range(0, 900, 120)]
    disc = slab(470, 26, grooves=True, cx=410, rx=190, ry=46)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{style_vars(cw)}
<defs>{speckle_pattern()}
<radialGradient id="spot" cx="52%" cy="38%" r="62%"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset=".55" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></radialGradient>
<linearGradient id="rim" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".85" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".35"/></linearGradient>
</defs>
<rect width="{w}" height="{380+dy}" fill="{wall}"/>
<rect y="{380+dy}" width="{w}" height="{h-380-dy}" fill="{floor}"/>
<rect y="{372+dy}" width="{w}" height="10" fill="rgba(0,0,0,.25)"/>
<g transform="translate(0 {dy}) scale({w/800} 1)">{"".join(d)}</g>
<g transform="translate({dx} {dy})">
<ellipse cx="410" cy="505" rx="210" ry="40" fill="rgba(28,30,32,.25)"/>
{disc}
<path d="M235 {top} L300 {top} L300 250 Q298 285 270 300 L220 300 Q200 296 205 280 L240 262 Z" fill="{leg}"/>
<path d="M190 272 Q185 300 215 305 L290 306 Q300 296 292 282 Q260 262 238 262 Z" fill="{shoe}"/>
<rect x="188" y="300" width="108" height="9" rx="4" fill="#F1F1EC" opacity=".9"/>
<path d="M378 {top} L466 {top} L452 360 L386 360 Z" fill="{leg}"/>
<rect x="382" y="352" width="74" height="40" rx="6" fill="{sock}"/>
<path d="M340 452 Q338 405 392 388 L452 386 Q510 398 526 452 Z" fill="{shoe}"/>
<path d="M400 400 L440 398 M398 412 L444 410 M400 424 L446 422" stroke="rgba(128,128,128,.6)" stroke-width="3"/>
<rect x="334" y="448" width="198" height="12" rx="6" fill="#F1F1EC"/>
<path d="M378 {top} L466 {top} L452 360 L386 360 Z" fill="url(#rim)"/>
</g>
<rect width="{w}" height="{h}" fill="url(#spot)"/>
</svg>'''

def standalone(body, viewbox, cw="ember", w=800, h=800):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="{w}" height="{h}">{style_vars(cw)}<defs>{speckle_pattern()}</defs>{body}</svg>'

def build_images():
    img = ROOT / "assets" / "img"; img.mkdir(parents=True, exist_ok=True)
    for cw in COLORWAYS:
        (img / f"disc-{cw}.svg").write_text(standalone(disc_top_body(), "-20 -20 440 440", cw))
    (img / "disc-stack.svg").write_text(standalone(stack_body(3), "40 110 520 400", "ember", 800, 615))
    for name in SCENES:
        (img / f"{name}.svg").write_text(scene(name))
    (img / "hero-wide.svg").write_text(scene("hero-gym", 1600, 900, 700, 260))
    (img / "og-image.svg").write_text(scene("hero-gym"))

# ---------- Page assembly ----------
PAGES = {
    "index":    ("ANKLE360 | Stronger ankles, a few minutes a day", "A stackable, non-powered balance disc with a four-level plan for stronger, steadier ankles.", "home"),
    "product":  ("The ANKLE360 Disc | ANKLE360", "Stackable ankle balance disc. Supports up to 300 lb, non-marking, four difficulty levels. $60 with free US shipping.", "product"),
    "training": ("Training plan | ANKLE360", "Four levels and a four-week plan for building ankle strength and balance with the ANKLE360 disc.", "training"),
    "stories":  ("Customer stories | ANKLE360", "How players, runners, lifters, and coaches use the ANKLE360 disc.", "stories"),
    "cart":     ("Your cart | ANKLE360", "Review the items in your cart.", "cart"),
    "contact":  ("Contact | ANKLE360", "Questions about the disc, an order, or team pricing.", "contact"),
    "policies": ("Shipping, returns, and policies | ANKLE360", "Shipping, returns, privacy, and terms for ANKLE360.", "policies"),
    "404":      ("Page not found | ANKLE360", "This page doesn't exist.", "none"),
    "devices":  ("Device preview | ANKLE360 prototype", "Preview pages at phone, tablet, laptop, and desktop sizes.", "none"),
}

def render(name):
    title, desc, nav = PAGES[name]
    html = read("layout/theme.html")
    header = read("partials/header.html").replace(f'data-nav="{nav}"', f'data-nav="{nav}" aria-current="page"')
    content = read(f"pages/{name}.html").replace("{{exploded}}", exploded_svg())
    content = re.sub(r"\{\{stack:(\d)\}\}", lambda m: stack_inline(int(m.group(1))), content)
    sprite = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>{speckle_pattern()}</defs></svg>'
    for k, v in {"title": title, "description": desc, "sprite": sprite, "header": header,
                 "footer": read("partials/footer.html"), "consent": read("partials/consent.html"), "content": content}.items():
        html = html.replace("{{" + k + "}}", v)
    return html

def inline(html):
    html = re.sub(r'<link rel="stylesheet" href="assets/([\w.]+)">', lambda m: f"<style>\n{read('assets/'+m.group(1))}\n</style>", html)
    html = re.sub(r'<script src="assets/([\w.]+)" defer></script>',
                  lambda m: f"<script>\ndocument.addEventListener('DOMContentLoaded',()=>{{\n{read('assets/'+m.group(1))}\n}});\n</script>", html)
    def data_uri(m):
        b64 = base64.b64encode((ROOT / "assets/img" / m.group(1)).read_bytes()).decode()
        return f'data:image/svg+xml;base64,{b64}'
    html = re.sub(r'assets/img/([\w-]+\.svg)', data_uri, html)
    # Preview files embed one video (the phone cut, smallest) so they stay self-contained.
    html = re.sub(r'\s*<source src="assets/video/hero-loop\.(webm|mp4)"[^>]*>', '', html)
    html = html.replace(' media="(max-width: 47.99em)"', '')
    def vid_uri(m):
        mime = {"mp4": "video/mp4", "webm": "video/webm", "jpg": "image/jpeg"}[m.group(2)]
        b64 = base64.b64encode((ROOT / "assets/video" / f"{m.group(1)}.{m.group(2)}").read_bytes()).decode()
        return f'data:{mime};base64,{b64}'
    return re.sub(r'assets/video/([\w-]+)\.(mp4|webm|jpg)', vid_uri, html)

def anchor_to_base(html):
    """GitHub Pages serves 404.html for a missing URL at any depth, so its relative paths would
    resolve against that URL. Prefix them with BASE_PATH. (A <base href> would also retarget the
    #main skip link to the home page.) Fragment-only, root-absolute, and scheme URLs are left as is."""
    return re.sub(r'\b(href|src|poster)="(?![a-zA-Z][\w+.-]*:|/|#)([^"]*)"',
                  lambda m: f'{m.group(1)}="{BASE_PATH}{m.group(2)}"', html)

if __name__ == "__main__":
    build_images()
    site, preview = ROOT / "site", ROOT / "preview"
    for d in (site, preview):
        shutil.rmtree(d, ignore_errors=True); d.mkdir()
    for name in PAGES:
        html = render(name)
        (site / f"{name}.html").write_text(anchor_to_base(html) if name == "404" else html)
        if name not in ("devices",):
            (preview / f"{name}.html").write_text(inline(html))
    shutil.copytree(ROOT / "assets", site / "assets")
    (site / ".nojekyll").write_text("")
    print("built", list(PAGES))

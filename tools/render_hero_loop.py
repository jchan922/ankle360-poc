"""Renders a placeholder hero loop: a spotlit athlete sprinting in place.
Outputs assets/video/hero-loop.{mp4,webm,gif} and hero-poster.jpg.
Placeholder only: swap for real footage with the same framing (subject right of center)."""
import math, pathlib, subprocess, random
from PIL import Image, ImageDraw, ImageFilter

W, H, S = 1600, 900, 2            # output size, supersample factor
FRAMES, CYCLE = 32, 16            # 2 strides per loop, 24 fps
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "video"
TMP = pathlib.Path("/tmp/hero_frames"); TMP.mkdir(exist_ok=True)
ORANGE = (255, 79, 31)
HIP = (1060, 470)
L = dict(torso=200, thigh=150, shin=150, foot=54, uarm=108, farm=100)

def vec(angle_deg, length):
    a = math.radians(angle_deg)
    return (math.sin(a) * length, math.cos(a) * length)

def add(p, v): return (p[0] + v[0], p[1] + v[1])

def capsule(d, a, b, w, fill):
    a = (a[0]*S, a[1]*S); b = (b[0]*S, b[1]*S); w = w*S
    d.line([a, b], fill=fill, width=int(w))
    r = w / 2
    for p in (a, b):
        d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=fill)

def pose(f):
    ph = 2 * math.pi * f / CYCLE
    hip = (HIP[0], HIP[1] + 9 * math.cos(2 * ph))
    lean = 11
    shoulder = add(hip, (math.sin(math.radians(lean)) * L["torso"], -math.cos(math.radians(lean)) * L["torso"]))
    legs, arms = [], []
    for side, p in (("near", ph), ("far", ph + math.pi)):
        thigh = 40 * math.sin(p)
        knee = 12 + 95 * max(0.0, math.cos(p - 0.35)) ** 1.6
        shin = thigh - knee
        k = add(hip, vec(thigh, L["thigh"]))
        a = add(k, vec(shin, L["shin"]))
        toe = add(a, vec(shin + 95, L["foot"]))
        legs.append((side, hip, k, a, toe))
        ua = -48 * math.sin(p)
        e = add(shoulder, vec(ua, L["uarm"]))
        hnd = add(e, vec(ua + 95, L["farm"]))
        arms.append((side, shoulder, e, hnd))
    head = add(shoulder, (math.sin(math.radians(lean)) * 58, -58))
    return hip, shoulder, head, legs, arms

def draw_figure(d, f, offset=(0, 0), color=None, alpha_far=True):
    hip, sh, head, legs, arms = pose(f)
    o = lambda p: (p[0] + offset[0], p[1] + offset[1])
    near = color or (22, 22, 23)
    far = color or (44, 44, 46)
    shoe = color or (236, 236, 232)
    # far side first
    for side, h, k, a, t in legs:
        if side == "far":
            capsule(d, o(h), o(k), 44, far); capsule(d, o(k), o(a), 34, far); capsule(d, o(a), o(t), 26, color or (200, 200, 196))
    for side, s, e, hn in arms:
        if side == "far":
            capsule(d, o(s), o(e), 28, far); capsule(d, o(e), o(hn), 24, far)
    # torso and head
    capsule(d, o(hip), o(sh), 78, near)
    r = 36 * S; c = (o(head)[0]*S, o(head)[1]*S)
    d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=near)
    for side, h, k, a, t in legs:
        if side == "near":
            capsule(d, o(h), o(k), 48, near); capsule(d, o(k), o(a), 36, near); capsule(d, o(a), o(t), 28, shoe)
    for side, s, e, hn in arms:
        if side == "near":
            capsule(d, o(s), o(e), 30, near); capsule(d, o(e), o(hn), 26, near)

random.seed(4)
STREAKS = [(random.randint(0, W), random.randint(160, 640), random.randint(80, 320), random.randint(2, 5)) for _ in range(26)]

def background(f):
    img = Image.new("RGB", (W*S, H*S), (10, 10, 11))
    d = ImageDraw.Draw(img)
    # wall gradient + floor
    for y in range(0, 660*S, 4):
        v = int(14 + 16 * (y / (660*S)))
        d.rectangle([0, y, W*S, y+4], fill=(v, v, v+1))
    for y in range(660*S, H*S, 4):
        v = int(24 - 16 * ((y - 660*S) / ((H-660)*S)))
        d.rectangle([0, y, W*S, y+4], fill=(v, v, v))
    # scrolling floor markers (period divides the loop)
    shift = (f * 25) % 200
    for x in range(-200, W + 200, 200):
        xx = x - shift
        d.rectangle([xx*S, 700*S, (xx+90)*S, 706*S], fill=(46, 46, 48))
        d.rectangle([(xx-60)*S, 800*S, (xx+60)*S, 810*S], fill=(34, 34, 36))
    # speed streaks
    for sx, sy, ln, th in STREAKS:
        x = (sx - f * 50) % (W + 400) - 200
        d.rectangle([x*S, sy*S, (x+ln)*S, (sy+th)*S], fill=(58, 58, 60))
    return img

def spotlight(img):
    glow = Image.new("L", img.size, 0)
    g = ImageDraw.Draw(glow)
    cx, cy = HIP[0]*S, 420*S
    for i in range(40, 0, -1):
        r = i * 22 * S
        g.ellipse([cx - r*1.3, cy - r, cx + r*1.3, cy + r], fill=int(150 * (1 - i / 40) ** 1.6))
    glow = glow.filter(ImageFilter.GaussianBlur(30 * S))
    light = Image.new("RGB", img.size, (120, 118, 114))
    return Image.composite(light, img, glow.point(lambda v: int(v * 0.9)))

def frame(f, grain=True):
    img = spotlight(background(f))
    # shadow
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).ellipse([(HIP[0]-150)*S, 752*S, (HIP[0]+170)*S, 790*S], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(14 * S))
    img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, sh)
    # motion trails (previous poses)
    for back, a in ((2, 40), (1, 70)):
        trail = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_figure(ImageDraw.Draw(trail), f - back, offset=(-18 * back, 0), color=(90, 90, 94, 255))
        trail.putalpha(trail.getchannel("A").point(lambda v: v * a // 255))
        img.paste(trail, (0, 0), trail)
    # orange rim light (drawn offset, then figure on top)
    rim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_figure(ImageDraw.Draw(rim), f, offset=(-5, -3), color=ORANGE + (255,))
    rim = rim.filter(ImageFilter.GaussianBlur(1.5 * S))
    img.paste(rim, (0, 0), rim)
    d = ImageDraw.Draw(img)
    draw_figure(d, f)
    # grain + vignette
    img = img.resize((W, H), Image.LANCZOS)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W*0.2, -H*0.4, W*1.2, H*1.4], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), vig)
    if not grain:
        return img
    noise = Image.effect_noise((W, H), 18).convert("RGB")
    return Image.blend(img, noise, 0.04)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for f in range(FRAMES):
        im = frame(f)
        im.save(TMP / f"f{f:03d}.png")
        frames.append(im)
    frames[0].save(OUT / "hero-poster.jpg", quality=82)
    run = lambda *a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-stream_loop", "3", "-i", str(TMP / "f%03d.png"), *a], check=True)
    run("-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26", "-preset", "slow", "-movflags", "+faststart", "-an", str(OUT / "hero-loop.mp4"))
    run("-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38", "-an", str(OUT / "hero-loop.webm"))
    small = [frame(f, grain=False).resize((800, 450), Image.LANCZOS).quantize(colors=64, method=Image.MEDIANCUT) for f in range(FRAMES)]
    small[0].save(OUT / "hero-loop.gif", save_all=True, append_images=small[1:], duration=42, loop=0, optimize=True)
    print("done")

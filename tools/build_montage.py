"""Builds the hero montage: short cuts from several clips, one shared grade, and a crossfade
from the last cut into the first so the loop never jumps.
Usage: python3 tools/build_montage.py /path/to/clips
Edit CLIPS to change order, in-points, or phone crop centers."""
import subprocess, sys, pathlib, tempfile

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads")
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "video"
CUT, XF, FPS = 1.7, 0.4, 25
GRADE = "eq=saturation=0.6:contrast=1.08:brightness=-0.04"

# (file id, in-point seconds, horizontal subject center 0–1 for the 9:16 phone crop)
CLIPS = [
    ("9943211", 3.0, 0.50),   # agility ladder
    ("6777201", 2.0, 0.50),   # defensive slides, court
    ("18234770", 8.5, 0.45),  # cone dribbling
    ("4761426", 1.0, 0.33),   # jump rope
    ("7691057", 1.0, 0.40),   # lunge, moody
    ("5275206", 7.0, 0.50),   # streetball crossover
    ("15112689", 4.0, 0.50),  # footwork, gym
    ("8691954", 6.0, 0.62),   # step-ups at sunset
]

def ff(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)

def find(cid):
    return next(SRC.glob(f"{cid}-*.mp4"))

def build(kind, tmp):
    parts = []
    for i, (cid, t, cx) in enumerate(CLIPS):
        if kind == "wide":
            vf = f"scale=2074:1166:force_original_aspect_ratio=increase,crop=1920:1080"
        else:
            # 9:16 crop around the subject, then scale to 720x1280
            vf = (f"scale=-2:1280,crop=720:1280:"
                  f"'min(max(iw*{cx}-360,0),iw-720)':0")
        seg = tmp / f"{kind}{i}.mp4"
        dur = CUT + (XF if i == 0 else 0)  # first cut is longer so the loop crossfade has material
        ff("-ss", str(t), "-t", str(dur), "-i", str(find(cid)),
           "-vf", f"fps={FPS},{vf},{GRADE},format=yuv420p", "-an",
           "-c:v", "libx264", "-crf", "16", "-preset", "ultrafast", str(seg))
        parts.append(seg)
    lst = tmp / f"{kind}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = tmp / f"{kind}-joined.mp4"
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined))
    # Loop: play from XF onward; crossfade the tail into the head so end frame == start frame
    total = CUT * len(CLIPS) + XF
    body = total - XF
    name = "hero-loop" if kind == "wide" else "hero-loop-mobile"
    fc = (f"[0:v]split[s1][s2];[s1]trim={XF}:{total},setpts=PTS-STARTPTS[a];"
          f"[s2]trim=0:{XF},setpts=PTS-STARTPTS[b];"
          f"[a][b]xfade=transition=fade:duration={XF}:offset={body - XF},format=yuv420p[v]")
    ff("-i", str(joined), "-filter_complex", fc, "-map", "[v]", "-an",
       "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-crf", "28", "-preset", "slow",
       "-movflags", "+faststart", str(OUT / f"{name}.mp4"))
    ff("-i", str(OUT / f"{name}.mp4"), "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "40", "-row-mt", "1", "-deadline", "good", "-cpu-used", "5", "-an", str(OUT / f"{name}.webm"))
    poster = "hero-poster.jpg" if kind == "wide" else "hero-poster-mobile.jpg"
    ff("-ss", "0.8", "-i", str(OUT / f"{name}.mp4"), "-frames:v", "1", "-q:v", "4", str(OUT / poster))

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        for kind in ("wide", "tall"):
            build(kind, pathlib.Path(d))
    print("montage written to", OUT)

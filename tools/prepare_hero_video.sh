#!/usr/bin/env bash
# Turns a source clip into the hero loop: crop (subject right of center on desktop, centered
# portrait on phones), desaturate/darken to sit under white copy, crossfade the end into the
# start for a seamless loop, and encode MP4 + WebM + posters.
# Usage: tools/prepare_hero_video.sh source.mp4 START_SECONDS
# Tune crop values to your footage (these match the Pexels 2560x1440 agility-ladder clip).
set -euo pipefail
SRC="$1"; START="${2:-2}"; OUT="$(dirname "$0")/../assets/video"
GRADE="eq=saturation=0.62:contrast=1.06:brightness=-0.05,colorbalance=bs=-0.04:bm=-0.03"
LOOP="split[s1][s2];[s1]trim=0.5:8.5,setpts=PTS-STARTPTS[a];[s2]trim=0:0.5,setpts=PTS-STARTPTS[b];[a][b]xfade=transition=fade:duration=0.5:offset=7.5,format=yuv420p[v]"
enc() { ffmpeg -loglevel error -y -ss "$START" -t 8.5 -i "$SRC" -filter_complex "[0:v]$1,$GRADE,$LOOP" -map "[v]" -an -c:v libx264 -crf 27 -preset slow -movflags +faststart "$2"; }
enc "crop=1880:1058:0:382,scale=1920:1080" "$OUT/hero-loop.mp4"
enc "crop=810:1440:875:0,scale=720:1280" "$OUT/hero-loop-mobile.mp4"
for n in hero-loop hero-loop-mobile; do
  ffmpeg -loglevel error -y -i "$OUT/$n.mp4" -c:v libvpx-vp9 -b:v 0 -crf 40 -row-mt 1 -an "$OUT/$n.webm"
done
ffmpeg -loglevel error -y -ss 3 -i "$OUT/hero-loop.mp4" -frames:v 1 -q:v 4 "$OUT/hero-poster.jpg"
ffmpeg -loglevel error -y -ss 3 -i "$OUT/hero-loop-mobile.mp4" -frames:v 1 -q:v 4 "$OUT/hero-poster-mobile.jpg"
echo "Hero video written to $OUT"

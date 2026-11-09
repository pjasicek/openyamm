#!/usr/bin/env bash
# Mechanical UV placement of the selected built-in imagegen repair; no generative repaint outside the mask.
set -euo pipefail
cd "$(dirname "$0")/.."
source_maps=textures/meshy_20260928
repair=textures/eye_repair_20260928
magick -size 320x320 xc:black -fill white \
  -draw 'ellipse 111,161 23,21 0,360 ellipse 208,160 23,21 0,360' \
  -blur 0x3 -threshold 0.4% \
  "$repair/mask_support.png"
magick -size 320x320 xc:black -fill white \
  -draw 'ellipse 111,161 23,21 0,360 ellipse 208,160 23,21 0,360' \
  -blur 0x3 "$repair/mask_feather.png"
magick -size 2048x2048 xc:black \
  \( "$repair/mask_feather.png" "$repair/mask_support.png" -compose Multiply -composite -rotate 90 +repage \) \
  -geometry +585+1245 -compose Over -composite -depth 8 "$repair/repair_mask.png"
magick -size 2048x2048 xc:black \
  \( "$repair/generated_face_patch.png" -resize 320x320! -rotate 90 +repage \) \
  -geometry +585+1245 -compose Over -composite -depth 8 "$repair/patch_atlas.png"
magick "$source_maps/base_color.jpg" "$repair/patch_atlas.png" "$repair/repair_mask.png" \
  -compose Over -composite -depth 8 "$repair/base_color.png"
# The false iris also occurs in the PBR data. Remove its relief and specular shape inside the same mask.
magick "$source_maps/normal.jpg" \( -size 2048x2048 'xc:rgb(128,128,255)' \) \
  "$repair/repair_mask.png" -compose Over -composite -depth 8 "$repair/normal.png"
magick "$source_maps/metallic_roughness.jpg" \( -size 2048x2048 'xc:rgb(255,153,0)' \) \
  "$repair/repair_mask.png" -compose Over -composite -depth 8 "$repair/metallic_roughness.png"

# In-game seam scan of x4 tours (MM9 dungeons, 2026-11-01)

For each map, `mm9_shots/<map>/native/<map>/NN-<shot>.png` and `mm9_shots/<map>/x4/<map>/NN-<shot>.png` are the same
camera pose in game with the original 1x textures and with the new x4 textures. `NN-<texture>-dK-closed-front`,
`-joint-graze`, `-closed-back`, `-open-front` are door shots (double doors: the two leaves must form one continuous
picture across their joint, as in native); `NN-roomK-e/n/w/s/up` are room views.

Look at every x4 shot next to its native one (open both images; crop/zoom with python PIL into a scratch file under
/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/d9fbd4c0-0c11-41ce-873f-fc55c335cdc4/scratchpad/ where detail needs it). Report shots where the x4 version shows any of:
1. a seam: a visible straight line, brightness step or broken pattern where a repeating texture meets itself
   (every 128/256 world units on walls, floors and ceilings), that the native shot does not show;
2. a tone step: two neighbouring surfaces (wall/floor/trim/door frame) whose brightness, hue or saturation relation
   differs clearly from the native (one got darker, bluer, more saturated than its neighbour);
3. a door whose leaves do not continue across the joint, or that looks different in layout from native;
4. anything broken: black/opaque areas where native is see-through (grilles, windows, crowds), magenta/checker
   placeholders, a texture clearly wrong for its surface.
More detail, sharper stones, different-looking fine grain are expected and NOT problems. Dark maps are dark by
design; brighten a crop to judge.

Output: write `mm9_shots/seam_scan_<your id>.md` with one line per suspect: `<map> <shot file> <issue> <where in the
frame>`; end with a line per map `<map>: N shots checked, M suspects`. Report the same back. Read-only otherwise:
never run game, tex.py, git, or modify files outside your output file and scratch crops.

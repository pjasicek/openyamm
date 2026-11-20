# Dagger Wound diagonal road correction

Current unresolved defect: screenshot1296 confirms a repeated concave bite in the diagonal road. V5 is still installed but its visual acceptance is superseded by `USER_REGRESSION_1296.json`. Passing seam checks did not validate the connected road silhouette.

The reported stretch uses `drsrne1` and `drsrne2`, not the NS donor repaired in v4.
Camera: (5913.830,5672.083,545.000), yaw5.446 radians, pitch−13.235 degrees.
It starts over `drsrns` at row52,col75 and looks along repeated diagonal pairs in rows53–56.
The changed runtime files are those two tiles and matching `gdrdne1`/`gdrdne2` grey-ground variants.
All other235 runtime files, including straight roads, retain their v4 bytes.

The user-visible left tooth was the upper-right tip of the large oval stone in `drsrne2`, around
(466,70) in512px authoring coordinates. A UV diagnostic at screen(690,555) returned(466,70).
Earlier edits to the opposite edge helped a separate hooked end but did not solve this tip.
The successful targeted input is `inputs/drsrne2_tip_crop.png`, cropped at(348,24,508,184).
Do not guess which edge is visible from top-down artwork: use the supplied pose and locate it.

Six built-in imagegen edits were retained under `raw/` and `prompts/`. The full-tile attempt named
`rejected_wrong_stone` removed a neighbouring stone and must not be used. Attempts1–3/captures are historical.
`compose.py` uses the final whole-tile artwork plus the isolated tip crop, Poisson insertion, local solid
coverage and matching contact shading. It asserts every runtime outer4px border strip remains unchanged.
A single coverage hole at a soft-mask insertion boundary is filled as solid road mortar before grey compositing.

`review_stage.json` binds the final native walk stage. Its sole pre-cleanup `gdrdne2` image is not used anywhere
on out01; final grey variants are separately inspected in the tile comparison. This is recorded explicitly in
`visual_review.json`, not presented as a capture of untested changed pixels. No diagnostic overlays are installed.

To reproduce the view after installation from the repository root:

```sh
./level_generation/terrain/mm8/play.sh enhanced out01.odm \
  --position 5913.830 5672.083 545 --yaw-radians 5.446 --pitch-degrees -13.235
```

`visual_review.json` binds the inspected exact-pose comparison and13 movement samples. `validation.json`
checks all724 compatible road joins and36 continuous masks. The complete export, acceptance, integration
and package reports live under `../../reports/`. `previous_delivery/` preserves the prior installed manifest.

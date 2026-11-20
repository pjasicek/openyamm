# Guard restoration review

Reviewed the native three-palette contact, all ten native pose sheets and selected enhanced outputs. The guard's
weapon is a halberd/poleaxe, not a short sword: its shaft is foreshortened in front and fully visible in side views.
Updated the initial prompt description before the first generation to reflect that evidence.

Reviewed every final frame through `all_base_dark.png` and `all_masks_light.png`, plus the magnified light/dark edge
contact. No clipped extraction cells or obvious magenta contour halos remain. All 59 frames have aligned base/mask
exports; masks track cloth separately from metal/skin rather than tinting the complete character uniformly.

Reviewed `viewer_walk.png` (palette 749, mirrored view 6, frame 3) and `viewer_attack.png` (palette 750, view 0,
frame 2). Native and enhanced figures keep comparable body height, ground alignment, weapon grip and pose;
the palette changes remain distinct. These are offline browser checks, not engine acceptance tests.

Remaining approximations: the helmet is slightly more pointed, metal/mail highlights are smoother/brighter and
ring patterns vary between poses. Halberd blade details, cloth folds and hand anatomy vary modestly between AI
sheets. Native palette ramps are approximated: boots/wood and some skin/metal undertones are less exact than
the sleeve and trouser colors. Four hue-guided masks can blend material boundaries; they are not recovered
ground-truth segmentation. Matte-derived alpha and a few cool metal reflections remain reconstruction choices.

Generation had service delays: the six-request batch stalled after several outputs, and one attack retry returned
HTTP 500. Completed sheets were retained; only missing sheets were retried individually. Ten selected sheets
cover the entire family. Prefer sequential requests for the next run if concurrent generation stalls similarly.

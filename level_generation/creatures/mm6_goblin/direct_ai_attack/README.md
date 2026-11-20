# Direct AI restoration of the six original goblin attack sprites

A separate 2D experiment: the original `gobat[a-f]0.bmp` images are the only visual input. No Blender render or
reconstructed model was used. The built-in image generation tool generated the entire six-frame sheet in one call.

- [Raw restored 3×2 sheet](attack_restored_v1.png): actual generated resolution **1682×935**.
- [Original-versus-restored playback](comparison_playback.gif), six original poses over 0.75 seconds.
- [Restored playback](attack_playback.gif) and [all-frame comparison](comparison_all_frames.png).
- [Six opaque magenta crops](frames_magenta/) and [experimental RGBA crops](frames_rgba_preview/).
- [Experimental transparent 1×6 strip](attack_rgba_preview_1x6.png): six 601×508 cells.
- [Exact prompt](prompt_v1.txt), [input sheet](original_attack_3x2_magenta.png),
  [source layout/hashes](source_layout.json) and [crop/timing manifest](preview_manifest.json).

## Method and observed result

`prepare_reference.py` packs unmodified native canvases at a common scale and offset into three columns and two
rows: a,b,c / d,e,f. Native transparency index 0 becomes opaque magenta. Nearest-neighbor doubling makes the source
pixels easy to inspect; it is only reference preparation, not the AI restoration. Extra border space protects the
raised weapon. The prompt requests the same arrangement, source pose/handedness/lighting and consistent character
detail throughout. The requested 3456×1920 was not returned; the delivered resolution above is the actual output,
without claiming an interpolated enlargement as generated detail.

The result retains all six distinct poses, the raised foot in b/c, the cross-body follow-through, and the downward
recovery. Face, olive skin, exposed anatomy, iron armor and leather costume are reasonably coherent across the sheet.
However, it changes proportions slightly, interprets fine costume details, alters blade curvature/foreshortening and
does not preserve exact grid placement or ground alignment. In particular the e-frame sword extends a little across
the nominal column boundary. This is a useful first restoration experiment, not a pixel-exact or production-approved
animation replacement. Playback should be judged alongside the native animation.

`package_preview.py` preserves fixed canvas origins and adds the same padding to every crop. It uses a seam in empty
space to keep the e-frame sword tip while excluding it from frame d; explicit extraction rectangles are recorded.
It does not independently recenter, rescale or retime poses to hide drift. Original and restored comparison canvases
use common normalized cell dimensions. Native timing is six frames × 0.125 seconds; GIF delays alternate 120/130 ms.

Magenta helps identify the background, but does **not** prevent contour artifacts or guarantee a uniform key color.
The generated background contains variations; exact RGB replacement alone would leave residue. The optional RGBA
previews use an explicitly approximate magenta-dominance key, not native generated transparency. They retain the
original opaque generated sheet for future extraction/refinement. A production matte needs close edge inspection
and possible decontamination; do not install these provisional keyed crops as final sprites. All six preview masks
are nonempty and stay inside their padded canvases; the six native source hashes remain unchanged.

## Approach to carry forward

For a short six-frame action, begin with one 3×2 sheet: the generator can see all poses and the same character in one
request. Compared with a very wide 1×6 request, this avoids spending the available image height on mostly empty
space. This run demonstrates useful consistency, not proof that it always beats separate calls. One-by-one generation
was not tested here. A practical next pass would correct any drifting frame with both its native pose and the
accepted complete sheet as references, preserving already good cells. Inspect a timed loop before accepting a sheet.

Choose opaque key-color output when testing extraction, or ask the image generator for real alpha when transparency
is the intended deliverable. Neither choice replaces edge review. For a future higher-resolution pass, keep actual
returned dimensions in the manifest; do not equate requested resolution with delivered resolution.


## Transparent-background follow-up (1256.png)

The user identified pink contamination around the sword guard/blade in the provisional keyed preview. This is
foreground RGB contamination, which the simple magenta-derived alpha mask does not remove.
Two built-in imagegen edits requested actual RGBA transparency and edge decontamination, preserving the approved
sheet. Both returned RGB images with a painted checkerboard and no alpha channel. They are failed transparency
attempts, not usable transparent outputs; see `transparency_attempts.json` and `prompt_transparent_v2/v3.txt`.
They also changed some foreground details, so neither supersedes the original approved `attack_restored_v1.png`.
Always inspect actual PNG bands/alpha extrema: a checkerboard-looking preview proves nothing about transparency.
The currently exposed built-in call has no explicit background parameter. An explicit alpha-capable API route is
a separate fallback, requiring user confirmation under the imagegen skill; no API call was made for this follow-up.


## Deterministic cleanup after pixel inspection

The approved RGB generator output already contains pink edge pixels, before our cropping/resizing. The original
alpha-only key preserved those colors. Local estimated matting plus foreground-color unmixing now provides
[cleaner RGBA frames and before/after evidence](edge_cleanup/README.md), with no additional AI/API generation.
This preserves the approved artwork and supersedes the old provisional key for evaluating contour quality.

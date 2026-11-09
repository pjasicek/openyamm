# PC01 restoration with fixed original masks

This pilot supersedes the full-figure switching experiment for PC01 in the equipment browser.
It stores **one shared body** (`pc01bod.png`) and four separate layers (`pc01lhu.png`, `pc01rhd.png`,
`pc01rhu.png`, `pc01rhb.png`). Every output is on its native canvas enlarged exactly 2× and uses the
original alpha bytes repeated 2×. Item offsets and native sprite origins are unchanged.

Open [review.html](review.html) for original/restored toggling and mask intersection, or
[the equipment browser](../../../../index.html?doll=1&trial=1&art=candidate) for candidate equipment.
The browser now shows one doll at a time with a pose selector. It uses the same body file for every pose.

## Method and evidence

The built-in imagegen tool repainted the assembled native two-pose sheet, using its silhouette stencil
and original avatar as references. [submitted_v1.json](submitted_v1.json) contains the exact prompt and
reference paths. [raw_v1.png](raw_v1.png) is the unaltered generated return. The native white-on-black
stencil is a reference only; it is not included in the output art.

`process.py` maps the complete returned canvas to the original 700×756 two-cell stage without bounding-box
fitting or item adjustments. It takes the common body, left hand, and open right arm from cell 1.
Cell 2 supplies only the held right arm and foreground fingers. It extracts each sprite at its original
table position and replaces generated alpha with that sprite's exact native 2× alpha.

Near generated edges, opaque RGB is extended under the native cutout to avoid revealing transparent
or colored-matte RGB. This is recorded per sprite in [manifest.json](manifest.json). Maximum RGB
extension is 7 pixels on the 2× canvas; it must be inspected as artwork, not accepted by a mask score.
The original blue-black boot backing/shadow pixels are explicitly retained (4,668 output pixels).
They explain much of the apparent raw boot-outline mismatch; they are not regenerated foot anatomy.

Raw generated alpha IoU is 0.889389 empty / 0.820354 held. Final alpha IoU is 1.0 for every extracted
sprite and assembled empty/one-hand/two-hand pose, with zero differing alpha pixels.
**Final mask equality is imposed by extraction. It does not prove that all internal anatomy or material
boundaries were correctly generated.** Four curled fingers plus a thumb are visible in the raw grip detail.

## Status

Visual-review candidate, not canonical acceptance or runtime installation. The browser's trial toggle
draws these parts independently of its equipment Artwork mode; its Original doll option remains available.
The `pc01lho` shield-hand variant has not been regenerated; the browser explicitly uses its original art.
The original raster silhouette is intentionally retained, including stepped edges and legacy boot backing.
No full-doll image swap is used, and no previous generation or accepted equipment file was overwritten.

The [browser checks](browser_checks.json) confirm a single canvas and the same body path for empty, one-hand,
two-hand and shield states. Toggling the original doll with the same loadout preserves every equipment path
and coordinate; the complete equipped canvas has zero differing alpha pixels in all four tests.
Candidate Leather Jerkin, Iron Longsword, accepted Helm, Hunting Bow and Trollish Shield were exercised.
An accepted Studded Leather variant was also loaded and visually inspected in the browser.

Reproduce extraction with:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepared/doll_01/mask_locked_20260924/process.py
```

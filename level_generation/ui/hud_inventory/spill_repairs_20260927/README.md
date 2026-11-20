# Geometry-preserving spill repairs — 2026-09-27

**Published:** all 1,722 review entries are now accepted. The current revision additionally resolves the 12 recent
commented targets and installs 1,531 changed runtime images. See [the acceptance receipt and current workflow](../spill_acceptance_20260927/README.md).
The following preparation results describe the frozen input batch; its candidates and pre-publication validation
remain historical evidence. Use the acceptance revision's validator for the current installation.

Current review: [review/index.html](review/index.html), served from the repository root at
<http://127.0.0.1:8899/level_generation/ui/hud_inventory/spill_repairs_20260927/review/index.html>.
The original spill audit links here. Its saved flags and placement/acceptance storage remain separate.

## Original preparation result and limits

All 1,722 `likely_spill` accepted-x2 records from the frozen spill audit were processed, including aliases.

| Result | Entries |
| --- | ---: |
| Color-repair candidates | 1,525 |
| Partial color-repair candidates with a few unresolved pixels | 6 |
| Spell ink / glow retained for contextual review | 122 |
| Native-colored or otherwise ambiguous art, no automatic edits | 69 |

The 1,531 candidates include 768 of the 770 inventory/equipment entries. `7item252` and `item266` received no
automatic edit. These preparation counts were candidates at that stage, not a claim that every colored pixel is
spill. The scanner still calls 229 candidates `likely_spill`; examples include native green cloaks, cyan moon
motifs, cold metal highlights and purple gems. Review the native/current/repaired images in context.
All 97 distinct inventory/equipment images still called `likely_spill` were inspected in the seven
`review/residual_contact/items-*.jpg` sheets (original / current / candidate). This is a contact-scale color and
feature check, not pixel-perfect acceptance. The unchanged `item266` hit is its intentional red/magenta wax seal;
`7item252` is the gold seal's small purple accents and remains a contextual review case.

Six entries retain small regions without a trustworthy donor within eight x2 pixels: elevator default/pressed
buttons (one pixel each), `7item003` (one), `lsword4` and its MM6 alias (18 each), and `item243` (four). The repair
does not extend distant colors across those features. They remain explicitly marked `needs_local_review`.
No generation was performed in this initial mechanical pass. Substantial missing artwork or demonstrably baked interior background should be
handled in a separate targeted repair; a heuristic color score alone does not authorize replacing its design.

Validation checks all 1,722 current/runtime input hashes and all 1,531 saved outputs: **alpha and dimensions
identical**, RGB changes equal the recorded masks, PNG payloads under the existing runtime filenames, 0644
permissions, no divergent duplicate repairs, and unchanged placement/ledger/master hashes. See
[review/validation.json](review/validation.json). The 610,528 edited RGB pixels do not move equipment, resize
canvases, change silhouettes or alter accepted offset tables.

## Original key versus restoration master

They are different inputs and must be inspected separately. For example:

- `wand2` original BMP: cyan key, RGB `(0,252,252)`.
- Its linked restoration sheet: opaque magenta, measured median border RGB `(248,5,249)`.
- Delivered accepted x2: RGBA with an existing fitted alpha mask.

The original is decoded using the frozen consumer transparency profiles, not a guessed universal color. The
actual linked master is inspected independently for alpha and magenta/green/cyan backing. A hidden magenta RGB
value underneath alpha zero is not an opaque magenta background. An opaque portrait background is not a cutout.

There are 140 recovered linked master files covering 726 entries: 83 measured magenta-backed sheets, 16 with true
alpha, and 41 opaque/unconfirmed. **996 entries lack a recovered master link**, including 440 inventory/equipment
entries. Do not infer their master key from their original BMP. Links can be earlier repair references rather than
the exact latest accepted parent; the manifest retains link kind, crop and evidence instead of asserting ancestry.

This pass operates on the already fitted RGBA exports:

1. Opaque portrait/HUD borders: repair excess edge RGB with nearby clean foreground color; retain opaque content.
2. Alpha cutouts: repair locally unsupported magenta/green/cyan fringe RGB while preserving every alpha byte.
   Native colored material in a surrounding neighborhood is protected. A confirmed master key permits additional
   small interior color repairs only where that hue is absent from the native neighborhood.
3. Spell ink and glow families: preserve the artwork for contextual review. A generic contour cleanup visibly
   damaged cyan glows in the exploratory run, so that treatment was rejected before this review was published.
4. Bow `item057`: a hash-bound, visually inspected string-only tint correction retains alpha and luminance while
   removing magenta/green stripes. Wood, red grip and string geometry remain intact; see
   [inspected_regions.json](inspected_regions.json).

For a **future raw-master re-extraction**, use the measured master backing, estimate alpha and unmix that actual
backing from edge RGB before premultiplied resizing (`RGBA → RGBa → resize → RGBA`). Do not apply a cyan unmix
because the original used cyan when the generated sheet actually used magenta. Do not apply that equation to
the current x2 colors and assume their already processed alpha is the original matte-mixture coefficient.

Raw masters remain intact. These are exact-x2 color-repair derivatives with provenance; they are not fabricated
high-resolution replacement masters. Re-exporting an old raw master without this repair would reintroduce spill.

## Review and historical preparation commands

The published viewer shows original art at x2, previous accepted x2, current accepted x2, light/dark backgrounds, magnified details,
changed-pixel masks and source/master evidence. Up/down navigate; left/right select a reason; Space flags;
Shift+Space accepts a repair. Text fields retain normal typing behavior. Export decisions with notes and exact
image hashes before handing off. New decisions use `openyamm-icon-spill-repairs-v1`; the viewer reads matching
old flags without modifying them. The acceptance pass recovered the user's saved decisions and draft notes from
a stable localStorage copy in an isolated browser. That capture and the 12 resolved notes are retained in
`../spill_acceptance_20260927/`; the live browser's saved feedback was not rewritten.

The first two commands below reproduce/check the historical preparation and require its original inputs. Do not
run them against the newer deployed revision. Use `../spill_acceptance_20260927/validate.py` for current checks.

```sh
python3 -B level_generation/ui/hud_inventory/repair_spill.py
python3 -B level_generation/ui/hud_inventory/validate_spill_repairs.py
python3 -B -m unittest discover -s level_generation/ui/hud_inventory -p 'test_*spill.py'
node level_generation/ui/hud_inventory/test_spill_review.mjs
```

The local server now runs independently of the Codex session as the transient user service
`openyamm-icon-review-8899.service`, bound to `127.0.0.1:8899` and serving the repository root. Check with
`systemctl --user is-active openyamm-icon-review-8899.service`; restart with
`systemctl --user restart openyamm-icon-review-8899.service`. It is not installed as a boot service.
If the service is absent after a reboot, serve the repository root with
`python3 -m http.server 8899 --bind 127.0.0.1` or recreate the transient user service.
Server restarts do not clear browser localStorage; use the same browser profile and exact `127.0.0.1:8899` origin.
Twenty focused Python checks and both browser review flows passed. The browser test uses an isolated profile;
it does not modify the user's actual flags or offsets.

Only `review/manifest.json` defines the original candidate batch. `pilot/`, `key_pilot/`, `bow_pilot/` and `full/`
are superseded exploratory outputs; do not deploy them. The publication overlay in `review/publication.js` points
to the newer accepted exports and resolutions. Runtime artwork and the global ledger now reflect that acceptance;
old accepted exports, raw masters and manual placement tables remain preserved. Redeploy current artwork with
`python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install`.

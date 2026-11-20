# Accepted Real-ESRGAN paperdolls — 2026-09-24

The user explicitly accepted all available doll bodies and limbs to retain native placement at a manageable
restoration cost. Higher-detail painted restoration is deferred, with all sources and attempts preserved.

**466 accepted sprites = 75 bodies + 391 limb/hand overlays**, including open/held arms, shield hands and
foreground grip fingers. [Decision and exact artifact hashes](decision.json).
[Equipment browser](../../index.html?doll=1) · [Original/ESRGAN/retained-paint comparison](../esrgan_baseline/index.html?doll=1).

The canonical checkpoint owns acceptance. Accepted copies live in
`checkpoint/layout_revisions/air_v1/accepted/paperdoll_esrgan_20260924/`.
`baseline_manifest.json` freezes the generation provenance. Its old comparison-only status records the state
at generation time, superseded by this user decision. No imagegen visual-review results were invented.

Validation checks every original source, native preview, prepared RGB, raw 4× inference, cropped master,
and exported 2× hash; exact RGBA size; nonempty alpha; and zero pixels outside the original 2× silhouette.
All live body/limb references with available native art must be included. Canvases and offsets are unchanged.
Alpha is antialiased rather than byte-identical to nearest-neighbor originals. Containment preserves placement
but does not promise that independently generated or previously misaligned equipment is correct.

Excluded: separate backgrounds, head/beard metadata, portraits, equipment and the jewelry panel.
Character #30 has missing original pieces; #31 lacks the body. Neither is silently substituted.
No runtime files were installed or original bitmaps changed. The browser uses accepted doll art by default.

Verify from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/accept_esrgan.py
```

`--apply` was already run under the canonical checkpoint lock; a repeat verifies and leaves accepted files unchanged.

Verification completed: all 75 available dolls load accepted body/limb art in the browser. PC01 empty,
one-hand, two-hand and shield composites retain the same equipment selections and add zero coverage outside
the corresponding native composite. The catalog comparison confirms all placement tables, resolver inputs,
and equipment artwork are unchanged. See [browser checks](browser_checks.json) and [catalog checks](catalog_checks.json).

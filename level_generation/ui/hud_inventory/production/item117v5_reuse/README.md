# Item117v5 — verified reuse

Accepted and staged the existing built-in-imagegen restoration from `item117v1`, without another generation call. Native source bytes, palette/rendered RGBA, dimensions, namespace, placement, frame and compositing contracts are identical; `contract-check.json` records these checks. Destination retains its own output identity.

Actually inspected destination native/restored/overlay comparison and donor full light/dark composites. Footprints pass. The donor measured landmarks remain valid for the identical native/output pixels (0, 0 and 0.5 x2 pixel). Exact output is 126x42 from native 63x21. Reconstructed canvas is byte-identical to reviewed output.

See `reuse-review.json`, `canvas-review.json` and `result.json` for provenance/staging. Original generation prompt/raw remain in `../item117_01/`. Runtime review remains pending; normal settings, originals and launchers unchanged.

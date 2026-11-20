# Headwear production sheet 01

## Accepted sheet

All eight cells are now accepted and staged. `acceptance.json`, individual acceptance/canvas reviews
and `measured-landmarks.json` record actual review. All 24 measured features pass the two-x2-pixel
tolerance, including the blue diamond, green fastener, orange gem and repaired horn/feather tips.
The raw master, full final sheet and every native/restored/overlay comparison were inspected.

`6crown4` and `6crown5` additionally reuse the accepted `6crown3` pixels after byte-identical source,
full consumer-contract and destination comparison review. Their separate native filenames, bindings,
exact 84×54 canvases and donor provenance remain explicit under `reuse_6crown4/`, `reuse_6crown5/`
and `verified-reuse.json`. No additional generation calls were made for acceptance or reuse.
An isolated runtime review of these new outputs is still pending. The initial processing notes below
describe the state before acceptance.

One built-in imagegen call, retained attempt `33b088019ed940d6887b81475c807a54`, generated a 3×3
sheet with eight occupied slots: repairs for `6crown1`, `6crown2`, `6crown3`, `6hat1`, `7item089`,
plus new `7item095`, `7item096`, `7item097`. Bottom-right is intentionally empty. The original eight
and nine-item experiments and their accepted siblings remain untouched.

The submitted native reference, exact amended prompt, raw output and extraction mapping are retained
here and in the checkpoint. The call took about 45 seconds. Actual output is 1254×1254. `process.py`
extracted all eight using recorded slot rectangles and the existing matte/uniform fitting path.
All eight exact-x2 exports pass footprint checks. Raw and combined enlarged final proof were actually
viewed; `review.json` records per-cell observations. Internal/feature landmarks and individual
registration comparison review remain pending, so these are candidates, not accepted/staged outputs.

Resume from this retained attempt. Do not make another generation call merely because the frozen jobs
still contain pending siblings. `manifest.json`, `processing.json` and `registration/` hold the mapping
and evidence required for review. The queue's three source-job claims were released by `record`.

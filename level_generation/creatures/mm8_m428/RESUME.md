# Resume m428

Only `native_d_v0` is missing: `m428da0`, `m428db0`, `m428dc0`, `m428xa0`. Image-service output moderation rejected request `6c911b2b-99eb-49f2-90be-04a228ffade7`; no raw output exists. See `review/generation_failures.json`. Resolve the service rejection through support with that request ID before resubmitting. Do not bypass moderation or substitute synthesized poses.

Keep all 25 selected v1 raw sheets and accepted registration transforms. Reuse `checkpoints/identity_layout_v1.png`. After the service issue is resolved, inspect `references/native_d_v0_matte.png`, use built-in imagegen with `prompts/native_d_v0_v1.txt` and the accepted identity, and save a versioned raw output. Run `process.py native_d_v0 <raw> <prompt> --identity checkpoints/identity_layout_v1.png`, then `calibrate.py`. Review and freeze only the new batch transform; retain all accepted batches. Run `tone.py`, `materials.py`, `package.py` without `--partial`, and `review_evidence.py`.

Review the new pose sequence, all affected variants and edges; rerun the approved `browser_checks.py`, create renewed `review/decision.json`, then run `finalize.py` and `../inventory_remaining.py`. Full completion requires all 140 native poses, unchanged source hashes/palettes/tables and renewed visual acceptance. Originals and gameplay assets remain untouched.

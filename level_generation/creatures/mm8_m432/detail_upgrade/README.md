# Dark elf warrior detail refinement

This is the retained refinement queue after the user identified insufficient actual character pixels
in the earlier broad sheets. **The active approach is now the user's
[common-crop front-attack grid trial](../front_attack_grid_trial/README.md).** Do not automatically resume the
smaller batches here until that sequence experiment is resolved. The earlier raw artwork and checkpoints are retained.
They are not a completed family and must not substitute for these refined frames during final export.

`jobs.json` holds compact jobs covering 157 native poses; the three accepted trial poses in
`review/trial_acceptance.json` complete the intended 160-frame scope. The tight common crop for each job
preserves native-coordinate relative placement. Generated sampling must exceed 2.5 pixels per native pixel,
and detail must remain visibly improved at the same 2× runtime size. See `review/runtime_comparison.png`.

Resume with the first pending job in `jobs.json`, reusing any already copied raw output. Inspect its listed
references, read its exact prompt, and use built-in imagegen (at most two independent requests concurrently).
Copy direct outputs into `raw/` immediately and retain rejected versions with repair prompts.

Run `python3 level_generation/creatures/mm8_m432/detail_upgrade/process_detail.py JOB RAW_FILENAME`.
Wait for completion before changing shared job/registration metadata. Inspect the complete registration
contact, including native head direction, equipment, limb positions and the coverage overlay. After passing,
run `accept_detail.py JOB`, then `variants_detail.py JOB`. Inspect all three native palette previews and the
mask overlay before `accept_variants.py JOB`. Run `refresh_progress.py` to refresh verified stage counts.
All commands here are relative to this directory unless a repository-root path is shown.

Masks use enhanced pixels and a documented material-support field to exclude thin blade highlights from
sleeve recoloring. `mask_protection.json` retains two explicitly reviewed blade exclusions. A zero spill
score alone does not establish a visual pass. Revisit affected acceptance hashes after any repair.

Do not rerun `prepare.py` or the parent `process.py` on new batches: the compact queue is already prepared.
The detail scripts import parent `process.py`, `calibrate.py`, `tone.py` and `materials.py`; retain these dependencies.

Final work still required: integrate all refined masters and three trial masters into a coherent deterministic
export; export 2× base/mask atlases and native placement, animation and palette metadata; inspect all animation
directions, variants and edge contacts; run the offline viewer and full coverage checks; seal the family and
refresh `remaining_inventory.json`. Until then, `m432` remains partial. Native originals and gameplay assets
remain outside this staging work.

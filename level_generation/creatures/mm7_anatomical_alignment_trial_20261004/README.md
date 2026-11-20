# MM7 Dragonfly, Spider and Goblin alignment trial

This is an isolated placement trial on existing restored artwork, prepared on 2026-10-04 using
[the anatomical workflow](../ANATOMICAL_PLACEMENT_WORKFLOW.md). **All three families remain partially aligned;
none has new complete acceptance.** Source artwork and gameplay assets were not changed.

Open the [shared reviewer](http://127.0.0.1:8881/). Its state is
[`review_state/frame_fixups.json`](review_state/frame_fixups.json); the retained proposal snapshot is
[`normalized_state/frame_fixups.json`](normalized_state/frame_fixups.json). Reviewer edits affect only this session.
[`alignment_status.json`](alignment_status.json) records exact coverage, hashes, revisions and review limits.

| Family | Native bank | Annotated poses | Passing candidates | Flagged, initial fit retained | Initial fit only |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dragonfly A, m186, IDs 226–228 | 125 | 40 | 35 | 5 | 85 |
| Spider A, m402, IDs 400–402 | 124 | 40 | 34 | 6 | 84 |
| Goblin A, m246, IDs 271–273 | 124 | 48 | 33 | 15 | 76 |
| Total | 373 | 128 | 102 | 26 | 245 |

The annotated scope is every pose of the eight-frame walking cycle at all five stored rotations of each
family, plus all eight Goblin front attack poses. Standing and other bindings that reuse these bitmap names
inherit the same placement. Other hit, fidget, attack, death, corpse and unused bitmaps received the initial
**Match family height & bottom** fit only. Their initial fit is not anatomical alignment or acceptance.

## What was tried

- **Dragonfly:** calibrate a shared body scale from visible head-to-terminal-body spans, then align visible
  eye/head X and Y. Use a visible upper body plate when the head is hidden. Thorax or tail junction checks
  remain independent; wing tips and the lowest limb do not control height. Walk views 0, 1, 2 and 4 have
  eight passing candidates each. View 3 has five flagged poses, including two with an occluded head.
- **Spider:** distinguish the abdomen from legs using the existing material mask and visually checked
  body boundaries. Align abdomen X and the native ground plane Y, using a shared scale per walking view.
  Check visible eyes separately in views 0–2; use visible back/body features in rear views. Views 3 and 4
  have eight passing candidates each. Eye/body discrepancies flag six other poses.
- **Goblin:** use corresponding head/profile/rear-head X, stance contact Y and a shared anatomical scale
  per walking view. Exclude weapon reach and helmet crest from size evidence. Check the actual visible
  waistband rather than a colour centroid contaminated by bracers, sword or crop clipping. Walking view 1
  has eight passing candidates; nine walking poses are flagged. In front attack, match the selected native
  planted boot's heel X and contact plane Y, changing the foot when the native phase changes. Only two of
  eight attack fits pass the independent head/vest checks; six retain their initial placement.

Manual point readings are approximate, with about two native pixels of uncertainty. A five-native-pixel
independent residual gate identifies candidates needing follow-up; passing it does not accept artwork.
Flagged poses may involve uncertain or occluded landmarks as well as generated proportion differences.
Their exact names, residuals and reasons are in [`blocked_frames.json`](blocked_frames.json).
Mixed clips still contain initial and anatomical fits and may jiggle. They are not completed alignments.

## Evidence and review

The final compiler inputs and per-pose evidence are retained together:

- [Dragonfly plan](normalized_candidate/mm7_m186/placement_plan.json),
  [evidence](normalized_candidate/mm7_m186/frame_fixups.evidence.json),
  [fixed-coordinate comparisons](mm7_m186/contacts/).
- [Spider plan](normalized_candidate/mm7_m402/placement_plan.json),
  [evidence](normalized_candidate/mm7_m402/frame_fixups.evidence.json),
  [fixed-coordinate comparisons](mm7_m402/contacts/).
- [Goblin plan](normalized_candidate/mm7_m246/placement_plan.json),
  [evidence](normalized_candidate/mm7_m246/frame_fixups.evidence.json),
  [fixed-coordinate comparisons](mm7_m246/contacts/).

All 128 annotated poses were visually inspected against native and initial-fit art on a common fixed canvas
at two physical pixels per native pixel. These are **static pose comparisons**. Timed playback, every other
action/transition, and full material-detail, alpha-edge, palette and mask reacceptance remain outstanding.
Earlier `draft_*`, `proposal/`, `reviewed_proposal/` and `final_candidate/` directories are superseded
diagnostics. Mask normalization left every displayed colour pose and compiled transform identical.

The [reviewer validation](reviewer_validation.json) checked all three family responses and 58 PNG responses,
including 13 material-mask channels. Colour PNGs match the selected files byte for byte; decoded mask
coverage matches exactly. These delivery checks do not constitute palette or mask visual acceptance.

The bank retains all 373 original bitmap names, every native palette and unused art. Native timing, aliases,
mirrors, per-frame native scaling and pivots remain in the selected manifests. Placement uses the shared
checkpoint's uniform scale and integer physical offsets, with its existing bottom anchor; a semantic heel
or head constraint is encoded through the compensating translation. All palette/mask consumers use the
same frame transform. Custom thorax, body-plate and foot landmarks stay explicitly named in the evidence,
without inventing viewer landmark types or hidden eyes.

[`inputs.json`](inputs.json) pins the selected manifests and restored art, plus 138 source files checked
unchanged. Dragonfly's older descriptor schema was normalized only in this session's
[`review_package`](mm7_m186/review_package/); its colour atlas, previews and masters are byte-identical
copies, and its descriptor animation records are preserved. Spider also uses an isolated
[`review_package`](mm7_m402/review_package/). Their grayscale mask containers were explicitly normalized
to RGB masks: original coverage equals the R channel exactly, with G/B zero. The selected source masks
remain unchanged. [`mask_normalization.json`](mask_normalization.json) records every conversion and hash;
new artifact versions were compiled from an explicit copied seed, preserving previous checkpoint versions.
No shared code, skills, global ledgers or runtime
assets were edited during this trial. The approved MM6 adaptation recipe was also checked unchanged.

This alignment pass did not regenerate detail. Existing minimum generated sampling remains Dragonfly
**1.686×**, Goblin **1.484×**, and Spider **2.117×**; their physical exported masters are 2×.

To reopen the reviewer from repository root:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm7_anatomical_alignment_trial_20261004/review_collection.json \
  --state-dir level_generation/creatures/mm7_anatomical_alignment_trial_20261004/review_state \
  --port 8881
```

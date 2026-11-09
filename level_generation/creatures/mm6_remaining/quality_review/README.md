# MM6 anchoring and actual generated detail review

This review qualifies the earlier complete/validated handoff. Installed coverage and 2x runtime packaging
are complete; exhaustive anatomical motion consistency and the current minimum 2x generated-detail gate
are **not** established for that installation. No creature artwork or gameplay binding was changed here.

## What the previous anchor review established

The ground-anchor audit measured all 3,481 frame names across 60 packages in logical coordinates. It checked
vertical pivots, canvas offsets and lowest visible alpha at several thresholds, including all actions.
Its visual review selected two poses per family plus eight foot close-ups; it explicitly did not claim every
animation was watched in-game. The 31 goblin front-frame vertical discrepancies were subsequently corrected.

That audit does not establish stable foot/head/torso landmarks across all frames or pixel-consistent horizontal
motion. Most shared processing aligns each frame using a body-band horizontal center and lowest opaque point,
with a common batch scale; death/corpse frames can use individual bounds-based scales. Those operations preserve
useful placement proxies but cannot distinguish every anatomical change, staff tip or asymmetric moving limb.
Native timing/mirrors and correct crop metadata alone do not certify generated motion.

## Actual generated sampling

The read-only [audit.py](audit.py) inspected all 60 installed package manifests and retained registration records.
All 596 installed file hashes still match the installation record. All packages use the 2x runtime tier.
For common raw-to-2x registration scale `s`, generated sampling is `2/s`; `s > 1` means export enlargement.
The reused goblin front uses inverse logical scale; Genie's separately registered endpoint components are
measured independently. Preserved native Cactus sparse/empty endpoints are counted separately.

- **3,114 frame names below 2x generated sampling**, across **56 families**.
- **362 frame names at or above 2x**.
- **5 intentionally preserved native endpoints**, including two empty frames.

Frame names include native aliases; these are not counts of independent AI requests. Sampling is raster density
in the accepted registration, not proof of recovered detail or anatomical accuracy. Archer is approximately
1.30–1.55x; Cover Dragon approximately 0.85–1.09x. Merchant, Monk, Rat and Spider are the four families whose
measured generated frames all meet the sampling minimum; that is not an animation-quality certification.

[Per-family table](SAMPLING.md), [all-frame numeric results](audit.json).

## Remaining quality work

To certify the user's requested standard, compare every native sequence with the installed reconstruction at
the same pivot, timing and scale, identify actual anatomical contact/stance landmarks and correct demonstrated
drift without removing intended native motion. For undersized generations, re-batch the affected native action/view
with measured foreground crops and overlapping poses, then measure returned sampling before acceptance.
Interpolation alone cannot meet the generated-detail minimum. This is a newly documented repair scope, not
authorization to regenerate or replace accepted art during this read-only review.

The requested insufficiency inventory is now [prepared and linked to the main completion gate](../redo_2x/INVENTORY.md).
See the [redo workflow](../redo_2x/WORKFLOW.md); no replacement generation has started.

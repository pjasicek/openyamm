# MM6 creatures — installed; insufficient detail queued for redo

The current task is **inventory prepared, generation not started**. All 60 families remain installed and usable,
but **56 families / 3,114 frame names are insufficient** for actual 2x generated detail. Main inventory and the
MM6 progress ledger now reflect that deficiency; historical acceptance does not override it.

- [Redo inventory](redo_2x/INVENTORY.md), [machine-readable jobs](redo_2x/inventory.json),
  [per-frame CSV](redo_2x/insufficient_frames.csv).
- [Replacement workflow and acceptance gates](redo_2x/WORKFLOW.md).
- [Sampling/anchor findings](quality_review/README.md).
- [Existing installation](INSTALLATION.md), [progress ledger](progress.json).

The earlier all-frame vertical-bound scan does not certify every animation's anatomical X/Y stability.
Four families pass the measured sampling threshold; exhaustive animation-landmark certification remains separate.
For the redo, retain sufficient frames/native aliases and palette reuse, re-budget coherent action/view batches,
measure actual raw-to-logical sampling, and validate all reconstructed sequences before acceptance.

The goblin ground-contact finding is resolved: 31 reused front frames have corrected vertical placement, without new image generation. Runtime palette lookup support now covers one/four material luminance LUTs and Hydra's RGB displacement LUT while sharing atlas pages. Cactus's runtime export explicitly retains the native actor bottom-anchor behavior. See the installation document for validation, native shared-ash behavior and reproduction.

Original BMPs, raw generations, prompts, rejected checkpoints, accepted art and deterministic settings are retained. Native descriptors, animation IDs/timing/mirrors/scales, gameplay behavior and unrelated enhanced content are preserved. All MM6 maps use the new references in ordinary repository runs; restart the game to refresh cached sprites. Existing isolated playtest snapshots are separate copies.

The installed artwork is retained during this inventory step. Stage replacements under each project's `redo_2x/`;
repacking requires new review and acceptance. Follow the linked workflow before refreshing completion or installing.
Prior completed/staged-only handoffs and acceptance files are historical checkpoints.

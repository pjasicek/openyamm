# MM8 Centaur HD masters

This brief covers image generation only within references_hd; complete creature production is tracked in the parent progress file. Use built-in imagegen, no nested Codex worker.

Authority: ../references/standing_five_views.png, reconstructed losslessly from 160 hash-verified original indexed BMPs and native palette 533. ../references/native_tiers.png shows harness palettes 533 green, 534 violet and 535 burgundy. Native view 2 faces image right and exposes the quiver on the anatomical right side.

Deliver unresized transparent 1536x1024 returns: 00_three_quarter.png, 01_front.png, 02_back.png, 03_left.png (face points image left), 04_right.png (face points image right). Generate the primary first; freeze after passing native comparison. Use primary plus native authority for every other view. Use primary_prompt.txt as the identity and pose specification. Bow, arrows and right-side quiver are separate required components.

Gate every image: exact four horse legs/two human arms, four single hooves, two five-digit hands, clear tail, continuous human/equine torso, native harness/bracers/material coverage, consistent proportions and pose, correct left/right, complete unclipped figure, real alpha and requested canvas. One targeted corrective generation per failed view. Record generation ID, exact prompt, input/output SHA256, output path and selected/rejected reason in generation_runs.json. Collect selected_views_review.png. No Meshy before the five-view gate.

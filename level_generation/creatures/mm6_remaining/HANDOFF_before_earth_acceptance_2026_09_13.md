# MM6 restoration continuation

Continue the already-authorized all-native-family restoration using the creature-restore and imagegen skills. Stage only; do not install into gameplay or overwrite originals. Reuse validated families. progress.json is authoritative; refresh remaining_inventory.json using inventory_remaining.py after acceptance, then run prepare.py ledger.

## Current status — 2026-09-13

Latest update: Earth walk_2 succeeded on attempt 1 of the newly authorized five-attempt budget. All 59 Earth frames now have generated artwork; final processing/validation is in progress. See retry_3_2026_09_13.json. Earlier checkpoint details below are historical until final acceptance.

59 of 60 MM6 families are validated. Genie and Fire Elemental are now complete, with accepted 2x atlases/masks, native palette metadata and offline viewers. Everything remains staged; nothing was installed into gameplay.

The user authorized two rounds of clearer restoration prompts after the historical output-moderation failures. The first round restored 23 missing frames and completed Genie after final repairs. The second restored Fire walk_0 and attack (11 frames) and completed Fire after material-mask/LUT correction. Exact prompts, input paths and service results are retained in retry_2026_09_13.json and retry_2_2026_09_13.json and each family's prompts/retry*/ folders. The first concurrent Earth round lost two exception details in orchestration; recorded serial follow-ups establish the known outcomes.

Only Earth Elemental remains: mm6_ert has 53 of 59 unique images generated. Missing batch walk_2 contains six right-facing side-walk frames. The native reference references/walk_2.png, accepted raw/standing.png and all other successful sheets are physically present. Current processing/masks are drafts pending full-family coverage and final validation.

Latest Earth walk_2 rejection: request f6d297e8-d358-4a7b-b1b9-05acc024cc69; HTTP 400 moderation_blocked at the output stage, category other. The service returned no output image and no precise causal explanation. The complete response and exact submitted prompt are in mm6_ert/prompts/retry_2_2026_09_13/walk_2.result.json and generation_failures.json. Do not claim a known trigger or falsely describe the benign native rock-construct reference as prohibited. Do not blindly repeat rejected jobs or bypass safeguards; no separately billed API/provider fallback is authorized.

Genie review repaired omitted late-death jewelry and finger-gap matte residue; see mm6_djn/review_notes.md. Fire review repaired flattened variant shadows and orange flame edges selected by the core mask; see mm6_fie1/review_notes.md and materials.py. Both corrections are deterministic after accepted imagegen checkpoints, with honest runtime-support limitations.

## Resume remaining families

1. Read the family's README.md, config.json, batches.json, generation.json and failure records. The original references and accepted raw/standing.png are physically present. Inspect them before any newly authorized generation attempt; revised prompts are in prompts/retry_2026_09_13/. Preserve exact submitted wording and actual reference hashes.
2. Record a successful returned image with mm6_peasants/record_family.py using bare family ert and the exact submitted prompt at prompts/<batch>.txt. Version previous prompts before replacement. Never overwrite accepted successful sheets.
3. Run the family's process.py. Earth packages through mm6_peasants/package_family.py ert. Build the shared offline viewer. Current partial extraction/masks are drafts, not final acceptance.
4. Inspect all native unique frames, unused ertfib0, native actions/mirrors/timing/scale/placement, all palette variants and mask overlays, and worst-edge contacts. For reference, accepted Fire preserves its native Lit/Transparent and NULL-corpse semantics. Correct demonstrated defects before acceptance.
5. Write truthful review notes, mark visual review complete, and create acceptance.json with manifest/review hashes and installed=false. Refresh inventory and ledger; add verified source coverage to coverage_audit.json. Manifest existence alone does not establish completion.

## Other important retained decisions

Cactus has 89 source names / 76 unique images. Its last three nonempty decay endpoints (261, 25 and 2 pixels) are exact native 2x; two source names share a genuinely empty frame. The other 72 unique images are AI-restored. Palette 955 lives in engine/terrain; source names are uppercase mCAC and Center anchored. Do not fill empty endpoints. The preparer now explicitly labels native empty slots; the earlier overfilled Cactus output is rejected and retained.

Hydra uses a documented RGB displacement LUT plus R8 mask for its five differently colored heads; a single-luminance recolor cannot reproduce it. Genie uses separate skin/jewel luminance LUTs plus RGBA material masks. Runtime support remains separate from asset staging.

The temporary disk-space blocker cleared; no restoration raw art or checkpoints were deleted by this agent to free it. Keep the final count honest: the blocked Earth family remains unfinished despite all accessible work being complete.

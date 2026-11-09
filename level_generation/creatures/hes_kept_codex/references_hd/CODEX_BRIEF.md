# Kept HD masters

Integrator ruling: requests/P1.md, “Integrator answer to the Kept builder (2026-10-23, openyamm-30)”.
Two new bodies, no villager body reuse. The male is shared by collared A/B/C and the freed man; the female is the
freed woman. These are original Hesper characters, so the approved concepts take the native-sprite authority role.

## Scope and inputs

Built-in image generation only for the art; save unresized returns here. No Meshy submission or builds.
Authority under design/kreegan_world/concepts/monsters/:
- kept_freed.png: male face, clean issued clothes, short shirt, loose trousers, wrapped boots.
- fam_kept.png: the SAME male; ragged dusty patched workwear. Exclude separately modelled collar/tools/armour.
- kept_freed_candidate_2.png: female body/face, clean clothes, tied-back dark hair and boots.
- fam_kept_candidate_2.png: supporting female identity only, not the freed clothing.
For every subsequent view attach its accepted three-quarter master as input 1.
For the ragged male also attach the matching clean view: clothing treatment may change, anatomy/pose may not.

## Deliverables

Three five-view sets in male_freed/, male_ragged/, female_freed/. Each is a single full figure on true alpha,
1024x1536 portrait, no shadow/floor/text, head/hands/boots all clear of edges:
00_three_quarter.png; 01_front.png; 02_back.png; 03_left.png; 04_right.png.
03_left shows the creature's LEFT side (nose points image left); 04_right shows its RIGHT side (nose image right).
The front three-quarter shows the front and creature's left side, nose toward image left.
Neutral symmetrical A-pose, arms 35 degrees from vertical, five open separated digits per hand, straight legs with
a gap, level soles. Side cameras rotate around the SAME pose, do not lower arms or turn the head separately.

Faithful high-definition late-1990s Might and Magic painterly modelling reference: clear textile/leather/skin detail,
soft even studio light, neutral albedo, near-orthographic camera at chest height slightly above for 00; level for 01-04.
Male: lean human adult, cropped dark hair, angular tired face, plain short ivory notch-neck shirt, belt, dark loose
patched trousers and wrapped brown work boots. Female: the approved strong-featured adult, dark bun, simple ivory
short notch-neck shirt with rolled cuffs, belt, loose dark patched trousers and wrapped boots. Retain dignity.
Ragged variant: same male body and garment volume, ragged edges, visible rough patches/repairs, ash dust and dirt;
the original warm ash-beige shirt. Clean version is washed simple issued cloth, not tailored villager dress.
No long coats, ornament, jewellery, added armour, weapons, collar, glow, spare anatomy, pedestal, captions or framing.
The collar/plate/pick/club already exist as separate props and will be fitted after the new source-frame rigs.

Plan separate 1K head textures for both bodies with matched neck seams and head turnarounds derived from accepted
masters before head retexturing. Do not spend on texture jobs until rig/geometry gates pass and uploads exist.

## Gate and records

Inspect every view for identity, palette, five digits, proportions, matching pose, correct sides/asymmetry,
unclipped margins, actual alpha and exact canvas. Freeze accepted 00 before making the other four. At most one
targeted corrective regeneration per view; retain rejected returns and record why. Never resize a selected master.
Store prompt, input hashes, original returned path, selected flag, review reason and output hash in
generation_runs.json. Make selected_views_review.png for inspection only; it must never be sent to Meshy.
Record selected hashes and actual gate limitations in ../creature_3d_progress.json.

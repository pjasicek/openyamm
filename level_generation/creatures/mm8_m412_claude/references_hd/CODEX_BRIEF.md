# MM8 m412 Pirate Warrior — HD references

Follow CLAUDE_HD_MASTER_REFERENCES.md. Image work is restricted to this references_hd directory; no Meshy or builds in the image stage.

Native authority: ../references/identity.png and ../references/native_a_v0.png, derived from preserved original BMPs. See ../references/sources.json for input hashes. The body is unarmed in its right hand; the cutlass is a required separate prop. The anatomical left hook and right eyepatch must remain on the correct sides.

Deliver five unresized 1024x1536 transparent images: 00_three_quarter.png, 01_front.png, 02_back.png, 03_left.png, 04_right.png. Generate the primary first, inspect it, then use it for identity in the other views. Creature-left profile shows the left hook arm closest to camera and the nose toward image left; creature-right profile shows the normal right hand closest and nose toward image right. Keep the same A-pose and proportions in every view. No ground, shadow, labels or backgrounds.

Prompt: 00_three_quarter.prompt.txt. Every view must pass native likeness, palette, asymmetry, five right digits/no left digits, no cutlass, full silhouette, pose consistency and alpha/canvas checks. Keep actual returns and hashes in generation_runs.json. Do not submit Meshy until all five pass. Head turnaround follows the selected body.

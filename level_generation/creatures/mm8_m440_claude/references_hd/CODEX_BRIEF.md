# Ogre Warrior HD modelling references

Use the original m440 five-view native sheet as anatomy/equipment/palette authority.
This reference-generation stage writes only into references_hd; no Meshy submission until all five views pass.
Generate one unarmed body per transparent image, neutral A-pose, 1024×1536 portrait:
00_three_quarter.png, 01_front.png, 02_back.png, 03_left.png, 04_right.png.
Generate 00 first, then use it together with the native sheet for the other views.
The club is a required separate component, never omitted from final assembly.

Preserve the massive brown body, short powerful legs, black helmet, crossed studded leather harness,
shoulder rings/spikes, green frontal cloth and wrist wraps, chainmail skirt, metal bracers/greaves and bare feet.
Back: crossed harness and dark chainmail, no invented green rear cloth.
Anatomical left profile looks toward image right; anatomical right profile looks toward image left.
Four fingers plus thumb and five toes are modelling inferences; native low-resolution hands do not settle every digit.
Keep the native tusked blunt face, equipment asymmetries and overall proportions.

Check identity and palette against native views, true alpha, canvas, margins, digit counts, pose,
consistent proportions and equipment on each view. Record prompts, input/output hashes and actual returns
in generation_runs.json, and make selected_views_review.png only from inspected selected masters.
Large head detail: prepare head-only turnaround from selected body masters before head retexture.

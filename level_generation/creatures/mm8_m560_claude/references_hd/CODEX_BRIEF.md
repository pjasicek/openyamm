# MM8 m560 Wyvern HD masters

Image generation stage only; output under references_hd. Full project continues after this gate.
Use built-in imagegen. No Meshy until all five masters pass visual review against original sprites.

Inputs: ../mm8_m560/references/native_variants.png (top row palette 561 identity; other rows palette evidence),
../mm8_m560/references/native_w_v2.png (original profile flight anatomy),
../mm8_m560/references/native_w_v0.png (original front wing motion).
Cyan/black are backgrounds, never creature colours. Native BMP hashes verified in references/native_inventory.json.

Deliver five unresized RGBA 1536x1024 returns, one complete creature each: 00_three_quarter.png,
01_front.png, 02_back.png, 03_left.png (left side visible, muzzle toward image left),
04_right.png (right side visible, muzzle toward image right). Use selected 00 as the identity reference for 01–04.
Pose identical in all views: flying, horizontal torso, long S-neck raised with level forward muzzle;
wings spread broadly in a shallow V, two bent hind legs hanging separately, long tail extended clear behind.

Identity: mottled moss green scales, paler green segmented underside, dark charcoal-green upper neck/skull,
slender crocodilian muzzle, two small red eyes, ivory teeth, one midline row of pale dorsal spines along neck/back/tail,
bat-like ochre/orange membranes with branching dark green reticulation and green finger struts, pale wing-tip claws,
exactly two hind legs with separated pale talons. No front walking legs, no separate arms, no head horns,
no armour, no extra limbs, no thick short dragon neck, no broad arrowhead tail tip.
Native digit counts/spine counts are limited by thumbnail resolution; preserve visible structure without inventing
extra ornament. Even soft studio lighting, near orthographic, generous margins, transparent background,
no ground/shadow/scenery/labels. Faithful detailed modelling reference, not new creature design.

Check each image: identity/palette; S-neck and tail length; two legs/two wings; separate claws; complete silhouette;
same pose/proportions; correct side; real alpha; exact landscape canvas. Store raw returns, prompts, input/output
hashes and selected/superseded decisions in generation_runs.json; assemble selected_views_review.png after approval.

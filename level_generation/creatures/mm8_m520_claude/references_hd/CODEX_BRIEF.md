# MM8 Cyclops m520 — HD references

Faithful reconstruction of the original MM8 Cyclops, not a redesign. Native PNGs are direct paletted BMP conversions at native resolution; all 162 BMP and three palette hashes verified. Palette 521 is the body-reference base. Palette 522/523 recolour the necklace discs, belt and wrist bands blue/red; skin remains ochre tan.

Generate one 1024×1536 transparent full-body image per view: 00_three_quarter, 01_front, 02_back, 03_left, 04_right. Freeze the primary before generating other views. Same upright A-pose, arms 35 degrees from vertical, separated fingers, visible limb gaps, flat planted feet; near orthographic camera, soft even lighting, no floor, shadow, text or cropping.

Identity: bald dome, ONE central eye under a heavy brow, projecting broad nose below it, broad jaw and small visible teeth, dark brown hair around the sides/back reaching the neck with long sideburns. Bare muscular thick torso, long muscular thighs, broad hands, tan ochre skin. Three round brown discs across the neck/chest. Simple narrow right upper-arm band, wrapped wrists, brown belt with small rivets, ragged dark fur/leather loincloth, bulky strapped fur boots. No weapon or boulder in the body reference. The native attack boulder is a separate animated component. No horns, tusks, shoulder armour, stone skin or added decorations. Finger count is ambiguous in the small source: infer four fingers plus thumb; feet are enclosed by boots.

Large head/face requires separate bust references at 1254 square, front, three-quarter, profile and back. Preserve the primary's face exactly while resolving eyelids, central iris, brow, nose, mouth and hair. Do not add a second eye or paired eye sockets.

For side views, creature left profile faces image left; right profile faces image right. Preserve the right upper-arm band asymmetry. Generate each from the selected primary plus the native matching view. Validate silhouette, colour, face/one eye, limb/digit count, accessories, pose agreement, full silhouette, true alpha and actual dimensions. Record prompts, hashes, output paths and selection in generation_runs.json; failed views remain recorded, never uploaded.

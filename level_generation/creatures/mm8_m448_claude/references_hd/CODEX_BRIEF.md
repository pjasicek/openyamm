# MM8 Ratman HD modelling references

Image generation only in this stage. Native m448 originals are the identity authority.
Inputs: `../source/identity_native.png` (five native views), `../source/a_v2_0_native.png` (side action anatomy and sword). Magenta is background. No restored image is a modelling input.

Generate five separate, unresized 1024 x 1536 transparent PNGs: `00_three_quarter.png`, `01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`. One full creature per image, no floor, shadow or text. Generate the three-quarter master first; freeze it after review and use it as identity input for all remaining views. Left side shows the creature's anatomical left side, nose toward image left; right side nose toward image right.

Preserve the lean hunched rat humanoid: long tapered dark brown muzzle, dark nose, small dark eyes, two round ears, grey-brown fur, ragged grey sleeveless shirt with diagonal CLOTH folds (no diagonal leather strap), green trousers, brown belt/hip pouch, brown shin/ankle wraps with exposed clawed toes, long tapering bare brown tail. Native finger counts are partly occluded; use three long fingers plus thumb as a modelling inference, verify against the close native views. Keep the tail distinct and clear.

Same relaxed A-pose in every view, arms 35 degrees from vertical, separated open fingers, spaced feet. Remove the sword only for body reference generation; it remains a required separate runtime prop. Near-orthographic camera, soft even studio light, subdued native colour. Do not add armour, spikes, extra limbs, jewellery, a cloak, a shoulder strap or weapons. Do not turn the narrow rat head into a wolf head.

Before selection inspect identity, proportions, digits, ears, clothing and tail continuity, viewpoint, silhouette/margins, true alpha and dimensions. One targeted correction for a failed view. Record actual prompts and input/output hashes in generation_runs.json. Save selected_views_review.png after all five pass. No Meshy spend until references pass.

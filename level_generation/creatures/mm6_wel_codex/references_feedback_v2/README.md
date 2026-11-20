# Water Elemental feedback references

These are the selected built-in imagegen returns used for water_v2. They are preserved before UV projection,
landmark registration or atlas packing. [receipt.json](receipt.json) records their SHA-256 hashes.
No Meshy job was submitted for these corrections.

## Poseidon

Output: [poseidon_front.png](poseidon_front.png).
Input reference: `assets_dev/engine/icons_x2/6trident5.png` (MM6 item 2037, Poseidon).
The generated image guided the authored 972-triangle mesh and supplies the blade/shaft texture atlas.

Exact prompt:

> Use case: stylized-concept. Create a high definition game prop reference from the supplied MM6 Poseidon trident item sprite. A single complete trident, straight-on orthographic front view, centered upright, entire weapon including bottom cap visible. Plain neutral mid-gray background, broad soft even lighting with no cast shadow. Preserve the exact identifiable design: a tall central silver/icy-steel spear blade, two shorter outward-splayed sharp silver tines connected by angular wing-like silver shoulders at the head, dark steel central socket. Purple lacquered shaft with ornate gold bands and subtle gold vine inlay, silver bottom cap. Three sharp points only; the head is an angular sculpted steel weapon, not a thin wire fork. Slim usable shaft, no extra spikes. Reconstruct beveled edges, restrained etched metal and worn purple enamel in clear high quality detail. Front-back symmetric functional weapon suited to a low polygon game mesh. Avoid perspective, text, watermark, characters, backgrounds, glow, magic effects. Portrait canvas; head about one-third of overall height, shaft about two-thirds. Maintain the source silhouette and material palette.

## Face projection

Output: [face_projection.png](face_projection.png).
Inputs: `review/feedback_v2/head_clay_front.png` as the geometry guide and
`review/feedback_v2/head_albedo_front.png` as the colour reference.
`scripts/feedback_textures.py` registers the output's eyes/nose/mouth landmarks to the sculpt and projects only
the frontal facial region into the retained head UV atlas. Original side/back, ears, hair and crown maps remain.

Exact prompt:

> Use case: precise-object-edit. Image 1 is the exact geometry/camera guide to paint, image 2 is only its existing color and character reference. Paint image 1 as an unlit/albedo texture projection for the same stern male sea elemental. Preserve Image 1's exact framing, all geometry contours, feature placement, dimensions, crown and hair outlines. Precisely align the painted SINGLE nose to the existing sculpted nose in image 1 (its tip is around x323 y418 on the 650px input), and SINGLE mouth to the subtle sculpted lips directly below at around x326 y459. The old color reference has nose and mouth too low: do NOT reuse those misplaced positions. Maintain pale warm gray-green weathered skin, light green eyes, gold-blond beard and moustache, copper crown, original ears, angry brow. Paint a realistic blond moustache surrounding the aligned mouth and connect into beard. Match the color richness of image 2, but use NO directional shadows, no specular reflections, no ambient occlusion or artificial facial highlights; diffuse albedo only suitable for game PBR shading. Flat neutral gray background. Absolutely no duplicate nostrils, second nose ridge, second mouth or additional forehead crown band. Do not change viewpoint, face geometry or silhouette. Square image same crop as image 1, 1024px.

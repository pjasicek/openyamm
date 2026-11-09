# Front idle style choices — second direction study

**User selected A — faithful rendered design.** Use `A_faithful_render.png` as the identity and rendering-style
authority for subsequent work. Preserve its face, proportions, hair, clothing, materials and lighting across poses.

Three separately generated 1024×1536 source masters, using the built-in image tool. No enlargement or
downsampling was applied. The native MM8 troll reference canvas is 256×256, with front standing bounds
137×148. Each new creature fills most of a 1536-pixel-tall image, comfortably exceeding 2× native detail.

- **[A — faithful rendered design](A_faithful_render.png):** brighter blue vest, broader original-style face.
- **[B — MM8 brute](B_mm8_brute.png):** heavy build, thick neck, quieter colors and substantial modeled forms.
- **[C — grounded MM7 direction](C_mm7_grounded.png):** leaner torso, longer limbs, restrained material palette.

The references are the original MM5 design, correctly paletted MM7/MM8 native sprites and the restored MM7
goblin. The earlier 160-frame adaptation was not used as the rendering-style reference. Exact prompts,
reference paths, returned dimensions, hashes and generation times are recorded in `generation.json` and `prompts/`.

Option A is the approved visual direction. During the authorized [full production](../master_a/README.md),
light-background alpha compositing confirmed that A's apparent backdrop is hidden RGB outside its transparent
silhouette, rather than a visible sprite halo. The exact original A is retained as front idle authority.
This three-option study remains intact; subsequent generation, registration and export live under `master_a/`.

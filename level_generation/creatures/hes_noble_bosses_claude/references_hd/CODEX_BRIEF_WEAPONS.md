# Codex brief: flat weapon paintings for the Noble bosses

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_noble_bosses_claude/references_hd/weapons/`.
No other files, builds or Meshy. Use your built-in image generation tool; PIL only to check sizes and alpha and to
turn a plain flat background into true transparency.

Each painting becomes a 3D weapon by inflating its silhouette (thin blades, round hafts) and projecting the painting
onto both faces. So each is a **flat, strictly side-on, orthographic view** of the whole weapon, **vertical with the
tip/head at the top**, centred, filling the canvas height with a small margin, on a transparent background. Even soft
studio light, no cast shadows, no glow halo or bloom spilling outside the object (glowing parts are painted as bright
emissive surfaces with hard edges), no motion blur, no text. Painterly-realistic game materials like the concept.

| File | Weapon | Design authority (attached) | Canvas |
|---|---|---|---|
| `vhorrax_courtesy.png` | Vhorrax's Courtesy, a plasma saber | input 1 `boss_vhorrax.png`: the isolated saber study (bottom left) and the saber in his hand | 512 × 1536 |
| `coil_spear.png` | The Coil Spear, a halberd | input 2 `boss_coil_keeper.png`: the isolated study (bottom left); input 4 item art for construction | 512 × 1536 |
| `conductor_baton.png` | The Conductor's Baton, a staff | input 3 `boss_conductor.png`: the isolated study (bottom left); input 5 item art for construction | 512 × 1536 |

Details:
- **Courtesy:** slightly curved dark structural blade with dark scale-ridged spine, a narrow incandescent orange-white
  cutting edge along the convex side, a gilded open guard with backswept bone/gold prongs, a wrapped resin grip and a
  gilded pommel prong. Blade length about three times the hilt length.
- **Coil Spear:** long dark resin haft wrapped in ivory and gold bands, straight spear point with a glowing **deep
  electric violet** core channel (white-hot centre), two crescent bone blades at its base, a bone-and-gold butt spike.
  Haft about 4 cm thick relative to a 1.5 m length.
- **Conductor's Baton:** long dark resin shaft with ivory-and-gold collars and fine glowing **violet-white** channels,
  a hollow two-pronged bone-and-gold crown holding a gold-wound white orb glowing violet-white at the top, a bone and
  gold butt spike.

Checks before saving: the exact canvas size, true alpha (background fully transparent), the whole weapon inside the
canvas, vertical, strictly side-on (no perspective), no halo outside the silhouette. At most one corrective
regeneration per weapon. Record prompts, input sha256 and outputs in `weapons/generation_runs.json`.

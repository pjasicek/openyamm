# MM7 bat — staged native restoration

Open [viewer.html](viewer.html) directly for native/restored playback. It embeds every native palette, derived
appearance, mask overlay, direction and descriptor scale; it works without a server.

All **116 native unique frames** are restored: 40 flight poses, 35 attack poses, 35 reaction poses, five death
poses and one corpse. Five stored views and native mirrors supply eight directions. Descriptor 205 uses green
palette 159 at scale 1; 206 uses blue-violet 160 at 1.099991; 207 uses red 161 at 1.199997.
Native action aliases, repeated frames, raw lengths, 125/187.5 ms timing, loop/hold behavior and flags remain in
`descriptor_animations`. The native 256×256 logical canvas and bottom-center pivot (128,256) remain unchanged.

Seventeen accepted built-in imagegen sheets supply base artwork once. Nineteen calls include rejected oversized
identity v1 and a front reaction v1 with a duplicate head; identity v2 and reaction v2 correct these defects.
Exact submitted prompts, source/reference hashes, raw outputs and checkpoint choices are in generation.json.
The unused identity_0..4 reference crops derive from rejected standing_v1; accepted action calls use standing_v2,
except corrected n_0_v2, which uses tilted_head_identity.png. Rejected material is retained only for provenance.

Connected-pose extraction retains thin wings crossing nominal sheet divisions. Each batch uses one common scale
calibration against native bounds, inverse reference-window placement and recorded native-baseline translations.
No individual silhouette stretching is used. Raw rectangles, common factors and offsets are in registration.json.
A fixed 0.82 RGB multiplier and masked membrane grade [0.82,1.10,1.32] retain the native dark material appearance.
Magenta unmixing estimates fine alpha; warm ears/bones stay protected and green fringe neutralization is disabled.

Enhanced-art R8 masks select green wing membranes. Deterministic RGB matrices fitted to native palette entries
64–207 derive palettes 160/161. Base 159 uses a byte-exact bypass. Alpha and zero-mask pixels stay byte-identical.
Fur, teeth, eyes, pink bones and ears remain protected. Subtle native pink-vein palette shifts are intentionally
kept with protected pink bone detail; fine fur and vein interpretation is not pixel-identical to original art.

The 2× export has one 2048×3581 RGBA8 base page and matching R8 mask: **36,669,440 decoded bytes (34.97 MiB)**.
Previews and embedded viewer images are offline review artifacts, excluded from runtime memory. Four-pixel crop
padding, three-pixel invisible RGB extrusion, premultiplied filtering and exact crop origins preserve placement.

Review covers every native/base comparison, all 348 appearance/frame combinations with mask overlays, native
sequence ordering, light/dark wing contours and browser captures for mirrored blue flight and red death.
All source coverage/hash, crop reconstruction, atlas extraction, alpha, mask and timeline checks pass validation.json.
The residual-magenta audit finds zero contour candidates above 32/255 in both cleaned and exported frames.

Reproduce processing from repository root (reuse accepted generation.json; no new artwork needed):

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m158 --tone 0.82
python3 level_generation/creatures/mm7_m158/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m158
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m158
```

Review modified artifacts again and renew acceptance hashes if processing changes. Sources and gameplay remain untouched.

# MM7 gargoyle — validated, staged only

All 124 native frames are restored: five standing views, 40 flight/walk, 40 claw attack, 30 hit, four frontal fidget, four falling and one corpse. Every native image is referenced. Twenty-six selected base sheets use built-in imagegen; all exact prompts, references and 32 raw outputs remain in generation.json. One output moderation rejection of the nonsexual stone-monster falling sheet is recorded in generation_errors.json; the identical request succeeded on retry.

Base palette 235 preserves the slate-gray stone body, tiny red eyes and green bat-wing membranes. Enhanced-art R8 masks derive blue 236 and red 237 through fixed native ACT RGB fits over green entries in 10–141. Body, horns, claws, wing struts, tail and eyes remain protected. No alternate palette art was generated. The pale membrane highlight in the rear attack sheet initially retained green; variants.py includes its lower-chroma coverage, with before-repair contacts retained under review/checkpoints/. All corrected frames were reviewed. Base is an exact bypass and variant alpha is unchanged.

Native descriptor bindings 262/263/264 use groups m235/m236/m237 with scale 1.099991 and Center flags. Logical canvas is 256×256, bottom pivot (128,256), physical masters 2×. All frames last 125 ms. Standing holds sa; flight/walk uses wa..wh; attack and shoot share aa..ah; hit uses na..nf. These actions retain five stored views and mirrors 5–7. Death uses na0 nb0 nc0 da0 db0 dc0 dd0, corpse holds xa0, and fidget uses fa0 fb0 fc0 fd0 fc0 fb0 fa0. Death/corpse/fidget retain Image1 reuse in all directions.

Processing uses tone 0.80, matte core tolerance 24, warm contour protection, connected pose extraction, common anatomical scale per batch, native baseline registration and premultiplied Lanczos resizing. Generated sheet dimensions are recorded per attempt; generated detail differs from 2× runtime export size. Native, raw, cleaned and aligned masters, processing settings and placement records remain staged.

Three shared RGBA8-base/R8-mask pages measure 2048×3907, 2048×4072 and 2048×395. Decoded base plus masks including packing uses 85,749,760 bytes (81.78 MiB); tight crops use 75,522,995 bytes. Palette variants share this allocation.

All 124 native/restored pairs and 372 native palette combinations were visually reviewed in ordered contacts, covering full native animation sequences. Light/dark edge contacts and all-frame cleaned/final extraction audits show no confirmed matte fringe. Browser captures verify blue mirrored flight, red Image1 death and the repaired red rear attack membrane. validation.json passes source hashes, exact crop reconstruction and atlas extraction, native timing/flags, mask weights, base bypass and unchanged variant alpha. review/acceptance.json pins reviewed artifacts. Surface detail is an interpreted restoration. No gameplay installation or original edits were made.

Reproduce offline from retained raw sheets, in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m234 --tone 0.80
python3 level_generation/creatures/mm7_m234/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m234
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m234
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m234
python3 level_generation/creatures/mm7_m234/review_variants.py
```

Open viewer.html locally for native/restored animation, palette, mirror and mask comparison. Reuse this accepted checkpoint; rerun only affected stages and renew acceptance after changes.

Sampling repair replaces four undersampled sequences with twelve overlapping four-pose sheets, preserving 92 accepted native frames and replacing 32. Every exported frame now has at least 2.014529 generated pixels per native pixel. Revisions of wh3 and late oblique attack restored the native downward wing stroke and forward claw follow-through. All 32 replacement poses, 96 palette appearances and masks were reviewed; final browser captures verify mirrored blue af1 at 125 ms and playing red rear flight.

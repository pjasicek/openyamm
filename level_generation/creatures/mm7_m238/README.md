# MM7 genie — validated, staged only

All 112 native frames are restored: 35 flight/standing poses, 35 casting poses, 30 recoil, five frontal fidget, six disappearance and one lamp corpse. The five unused m238wf0..4 images are retained without adding them to playback. Eighteen selected sheets and all 23 built-in imagegen outputs, exact prompts and references remain in generation.json. Targeted edits removed two invented held lamps, corrected one recoil hand pose, removed two invented recoil sparks, and restored native disappearance layout and smoke occlusion.

Base palette 239 preserves cobalt skin, dark blue hair, blue-white mist, gold trim and green cloth. Enhanced-art R8 masks derive violet 240 and red 241 through fixed native ACT fits over green entries in 213–251. Garment, collar, cuffs and green earrings recolor; skin, hair, gold, lamp and mist remain protected. Cyan-cloud mask leakage found during review was corrected by requiring G > 1.10B seeds and a G-B coverage ramp. No alternate palette art was generated; base bypass is exact and alpha is unchanged.

Descriptors 265/266/267 bind m239/m240/m241 groups at scale 1.099991 with Center. Logical canvas 256×256, bottom pivot (128,256), 2× physical export. Every frame lasts 125 ms. Standing and flight/walk share wa wb wc wd we wg, retaining five stored views and mirrors 5–7. Attack/shoot share aa..ag, hit uses na..nf. Death uses na0 da0 db0 dc0 dd0 de0 df0; corpse holds xa0; fidget uses fa0..fe0. Death/corpse/fidget use Image1 reuse in all directions. The small lamps retain native size, height changes and tilt, including the dd0 cloud and lamp in one frame.

Processing uses tone 0.85, magenta core tolerance 8, warm protection, material edge hue repair, connected pose extraction with one shared anatomical scale per batch, and native baseline registration. Disappearance uses its exact fixed grid to retain the disconnected cloud/lamp arrangement. repair_effects.py reuses an immutable cleaned checkpoint, repairs blue-purple mist fringe against healthy cyan-blue enhanced pixels at unchanged luminance, restores pale casting sparks inside authored rectangles that exclude jewelry, and restores the brighter native smoke ramp. Repairs precede premultiplied Lanczos resizing and preserve alpha and placement. Before-repair contacts and extraction checkpoint are retained. Generated sheet dimensions are recorded per attempt; generated detail differs from 2× export size.

Two shared RGBA8-base/R8-mask pages measure 2048×4047 and 2048×68. Decoded base plus masks including padding is 42,137,600 bytes (40.19 MiB); tight crops use 37,869,110 bytes. All native palettes share this allocation.

All 112 native/restored pairs and 336 palette combinations were reviewed in ordered contacts across full native sequences. Mask overlays, corrected cloud variants and light/dark edge contacts were checked. Browser captures verify mirrored violet casting and red Image1 disappearance. validation.json passes source hashes, exact crop reconstruction/extraction, timings/flags, mask weights, base bypass and variant alpha; cleaned and final atlas edge audits have zero candidates above 32. review/acceptance.json pins reviewed artifacts. Surface detail is an interpreted restoration. No original edits or gameplay installation.

Reproduce offline in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m238 --tone .85
python3 level_generation/creatures/mm7_m238/repair_effects.py
python3 level_generation/creatures/mm7_m238/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m238
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m238
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m238
python3 level_generation/creatures/mm7_m238/review_variants.py
```

Open viewer.html locally. Reuse the accepted checkpoint; rerun only affected stages and renew acceptance after changes. The effect-repair checkpoint is tied to the documented extraction settings and selected raw sheets; a future extraction change requires a new checkpoint, preserving this one.

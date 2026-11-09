# Cover dragon restoration review

Accepted all 55 unique native images: 49 referenced and six unused fire-attack poses. Ten generated sheets retain native six-frame front idle/flying reuse, five stored flying directions, biting attack, hit and progressive disintegration/ash. Native timings, mirror aliases, per-palette sequences and anchoring are preserved.

Reviewed every native/raw sheet, final base and mask contacts, five-view identity variants and worst-edge light/dark contact. Offline viewer captures after the last mask correction cover blue 699 mirrored walk view 6 frame 2 and gold 700 death frame 4. Corrected unused attack sheet restores missing mouth flashes in the last two frames. Corrected bone mask and explicit neutral native palette indices remove purple/blue horn contamination; final horns remain pale neutral in all variants. Rejected output and its exact prompt are retained.

Four enhanced-art masks separate orange hide/wing, gold belly/effects, neutral horns/claws and mauve mouth. Fixed native-usage-weighted sigma=4 luminance lookup curves derive blue 699 and gold 700 from orange 698, with transparent index zero excluded. Base gain .84; final ash has zero mask. Base bypass and protected pixels are exact. Wing veining and scale detail are more defined than native; the earliest death stage has less fine fringe fire and later flames have a slightly darker center. Long wings may exceed the default viewer pane zoom, but atlas images are unclipped.

Hash provenance, native source coverage, timing/placement, mask weight sums, unchanged variant alpha, exact crop/atlas reconstruction and zero-mask protection pass. Zero residual magenta candidates across cleaned, exported and atlas-extracted art. Decoded shared base plus RGBA masks: 324,666,224 bytes (309.63 MiB), excluding previews. Staged only, no gameplay installation or GPU performance claim. multi_mask_luminance_lut_v1 requires matching runtime support or deterministic variant baking.

Reproduce with process.py, package.py, ../mm6_peasants/build_viewer.py cdr1 and ../mm6_remaining/identity_contact.py cdr1. Rebuilding clears visual acceptance.

## User review 2026-09-24: flight arm consistency

Standing/walk/fidget reuse the flight masters. In view 0, frame 1 is the good reference; frame 3 upper arms look smaller, frame 4 much larger, frames 5–6 shift apparent muscle mass toward the shoulders. Check native shading against anatomical volume before targeted regeneration; other actions are reported OK. Review all stored flight views.

Staged the 2026-09-24 arm refinement in `consistency_repair_20260924/redo_2x/`: regenerated front flight c0/d0/e0/f0 (frames 3–6), inherited by standing/walk/fidget. Inspected the other 24 stored flight-view body crops; all 51 other cleaned/aligned/mask frames remain byte-identical. Additional imagegen passes corrected high c0/d0 hands and slimmed d0 upper/lower arm swelling. Final forehand Y differences are approximately -2.32/+2.08 logical pixels, within manual joint-surface uncertainty; this is not a volumetric guarantee across poses. Native timing/aliases, exact atlas placement, three palettes and 2x exports pass. Measured sampling minimum 2.422x. Built-in imagegen prompts/raw attempts and limitations are retained with `review/decision.json` and hash-bound `review/acceptance.json`. The original package and viewer edits are preserved.

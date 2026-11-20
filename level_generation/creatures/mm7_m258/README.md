# MM7 Griffin restoration

Restores all 135 unique native frames, including 25 frames not referenced by current descriptors.
Descriptors 280–282 use native palettes 259 (teal/olive), 260 (purple/silver) and 261 (red/black).
All 41 selected built-in imagegen sheets supply genuine RGBA. Exact prompts, references, original
output locations and hashes are retained in generation.json and prompts/submitted/.
Minimum measured generated detail is 3.035587634027286 pixels per native pixel; exports are 2×.

The native family contains five standing poses, 35 flight, 35 attack, 35 recoil, 20 collapse and five
corpse poses. Flight, attack and recoil retain stored views 0–4 and mirrored aliases 5/6/7→3/2/1.
Standing/walk/fidget share flight; attack/shoot share attack. Death uses the exact native sequence
na0, nb0, da0, db0, dc0, xa0, dd0. Corpse uses xa0. Image1 death/corpse aliases and all unused stored
art remain exported. Timings are 125 ms, native scale 1.299988, logical canvas 256×256,
bottom-center pivot (128,256), and original flags retained in descriptor animations.

Two atlas pages (2048×4006 and 2048×1927) share matching RGB8 masks. Decoded memory including padding
is 85,055,488 bytes (81.12 MiB): base RGBA8 48,603,136 and masks 36,452,352 bytes.
The self-contained viewer.html compares original palette sprites with the staged atlas and supports
all actions, mirrors, native scales, three palettes, mask overlays and frame stepping.

## Processing and review

Tone is fixed at .80. Genuine alpha bypasses matte keying; only documented near-invisible disconnected
components and three reviewed gutter tails are removed. All raw images remain untouched.
flight_alignment.json preserves verified native/enhanced beak landmarks, original hashes and 17 integer
whole-frame translations. align_flight.py checks exact inverse pixel recovery; no resizing or body-part edits.
Enhanced RGB masks cover teal plumage/tail tuft, olive flight feathers and warm fur/gold. Fixed native
ACT fits derive palettes; palette259 is an exact bypass. Small talon seed islands are excluded, and two
side-recoil beak regions are reassigned from feathers to gold. Brown fur remains unchanged in palette260;
palette261 applies its native warm shift. All variants preserve base alpha and protected unmasked pixels.

Reviewed all 135 native/base pairs, all 405 enhanced palette appearances and masks, 16 ordered native
sequences, actual 2× detail and worst edges on light/dark backgrounds. Final browser checks include
playing mirrored purple flight, red side recoil and held front collapse. Corrected beaks were rechecked.
Source hashes, complete coverage, raw boundaries, exact crop/atlas reconstruction, matching mask placement,
base bypass, variant alpha and native timings pass. Residual contour candidates above32: zero.
Enhanced feather/anatomical detail is an interpretation; fixed material ramps approximate native ACT colors.

## Reproduce

Do not rerun prepare.py: source/batch planning is already frozen. After a demonstrated change run, in order:

1. Local process.py, then align_flight.py, then variants.py.
2. ../mm7_m514/package.py --project level_generation/creatures/mm7_m258 from repository root.
3. Local finalize_metadata.py, then ../mm7_m514/build_viewer.py with the same --project.
4. ../mm7_ambient/review_contacts.py with that --project; local review_sequences.py and review_variants.py.
5. Review affected visuals and browser playback, then renew review/acceptance.json hashes.

Run stages sequentially: packaging writes invisible RGB padding back into aligned files.
Everything is staged under level_generation/creatures/mm7_m258; no native assets or gameplay installation changed.

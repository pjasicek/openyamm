# Leather fighter visual acceptance

Accepted staging: descriptors 538–540, 59/59 native unique images (58 referenced plus unused fgtfib0), palettes 733/734/735. Eleven built-in imagegen batches, retained raw outputs and exact submitted prompts. Full fgt prefix scanned, including fgtf standing names and all other action stems.

Reviewed every native/raw sheet, final all-base and all-mask contacts, all three standing palette rows, worst edges on light/dark backgrounds, and offline viewer mirrored walk view 6 palette 734 frame 3 and death palette 735 frame 3. Native fall preserves the detached mace's flight and final resting position. Six-frame walks, attack/recoil poses, idle and five-frame death followed by held corpse preserve native bindings, timing, mirrors and bottom-center placement. The unused idle image is restored without being added to playback.

Enhanced cloth coverage derives navy/red variants from native-used luminance LUTs; a restrained leather coverage channel follows the small native leather color change. Black hair, pale face, steel, gold trim and scarf remain largely protected. Base artwork gain .84 retains native tonal weight; base palette is an exact bypass. Masks are authored on enhanced pixels, not resized native anatomy.

Source/palette/raw provenance hashes, unclipped extraction, exact crop reconstruction and atlas extraction, unchanged variant alpha, zero-mask invariance and native sequences all pass. Residual matte candidates above 16 are zero in cleaned/exported/atlas-extracted stages. Decoded base+RGBA mask atlas memory including padding: 74,506,280 bytes (71.05 MiB); offline baked variants excluded.

Limitations: boots have more explicit seams/fasteners and shoulder caps are more clearly polished than the native blur. Minor per-frame cloth folds change with generation, while pose and anchoring follow the original. 2× denotes physical export resolution; generated sheets provide about 430 pixels of standing figure height. Offline contact and viewer pose checks do not establish GPU performance. Requires LUT-aware loading or deterministic variant baking for gameplay; not installed.

Rebuild with process.py, package.py, then ../mm6_peasants/build_viewer.py fgt from the repository root using full paths. Rebuild resets visual acceptance; review affected output before reaccepting.

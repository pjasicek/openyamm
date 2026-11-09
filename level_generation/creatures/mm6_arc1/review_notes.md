# Archer review — 2026-09-11

Accepted staged restoration: 58 unique native images, including unreferenced arc1atk; all 57 referenced images covered.
The native attack reuses arc1fia0 from fidget and repeats arc1atm with distinct timings. Both bindings are preserved.

Reviewed all generated sheets against native pose authorities, all-frame dark contact and light mask overlays,
standing palette contacts, collapse/attack/walk comparison strips, and magnified contour patches. The offline viewer
was checked at mirrored walk view 6 / palette 662 / frame 3 and front attack palette 661 / frame 4.
Full action orders, hold/loop modes, native mirror aliases, timing, scale and per-palette sequences are in manifest.json.
The review uses native-ordered contacts and explicit viewer frame steps; no real-game installation or performance claim.

A fixed RGB gain of 0.80 restores the original dark tonal weight across every action and view. The initial RGB
checkerboard output was rejected as transparency, then background-replaced with magenta. Raw versions and prompts
remain available. Alpha is estimated, not generator-supplied. The generic matte's seven-pixel cap removed parts of
thin bowstrings; process.py restores strongly supported dark-line pixels outside that cap from the raw images.
The corrected close-up and final atlas viewer show the string continuous. This repair is specific to this archer's
magenta matte and protected non-magenta materials, and must not be applied blindly to other families.

No confirmed visible magenta fringe, missing cells or clipped extraction boundaries remain. Cropped reconstruction,
base/mask atlas extraction, unchanged variant alpha, protected zero-mask pixels, exact base bypass and original-source
hash checks pass. All three edge-audit stages report zero candidates above the calibrated 16/255 threshold.

Accepted approximation: reconstructed face, leather markings, hair and boot detail vary slightly between action
sheets. No extra poses, changed animation timing, invented views or per-variant AI redraws. Physical output is 2x;
raw sheet dimensions are recorded and do not establish 2x newly generated detail throughout.

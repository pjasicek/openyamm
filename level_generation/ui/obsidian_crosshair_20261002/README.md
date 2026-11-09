**D was selected and integrated on 2026-10-02.** The gameplay crosshair now uses soft ivory RGB 255/250/224 and a complete one-screen-pixel charcoal outline, keeping its center open. It measures 18 × 18 pixels at 1600 × 900 and 14 × 14 pixels at 800 × 600. See the [native screenshots](native/index.html) and [validation record](native/validation.json).

Five proposal options are preserved in the [interactive preview](index.html): the previous game crosshair, three crosshairs generated with built-in imagegen, and the simpler ivory cross authored as native vector geometry.

My recommendation is **D, ivory outline**, at approximately 18–20 screen pixels in the 1600 × 900 reference. It retains the current open cross shape, changes the cream face to the HUD's soft ivory and adds a complete charcoal contour. It remains easy to locate over dark foliage, bright clouds and detailed stone. Keeping the current crosshair is also a reasonable choice.

The three generated concepts match the pale-brass and obsidian materials, but their bevels and pointed tips lose contrast at small sizes. A is the quietest decorative option. B is an open diamond. C returned as a connected compass ring rather than the requested split ring, and occupies more of the view. These are design concepts; the returned raster art contains very faint alpha specks outside the visible emblem and is not accepted for runtime installation.

All generated PNGs are preserved unchanged in [art](art/receipt.json), alongside SHA-256 hashes, original output paths and bounds used only for preview display. [D's vector source](art/d_ivory_outline.svg) provides exact symmetric geometry. [Exact submitted prompts and reference paths](generation_prompts.json) record the three built-in imagegen calls.

The preview reproduces the existing crosshair from `game/ui/GameplayHudOverlaySupport.cpp:1192`: at 1600 × 900, it has six-pixel arms, a two-pixel gap and stroke, RGB 255/255/180, and a one-pixel offset dark shadow. Each comparison sample draws the same native screenshot crop. The current footprint stays at 16 pixels plus its shadow; the new designs can be adjusted from 16 to 30 screen pixels. The scene and portraits are existing native captures; no scene art was generated or retouched.

Reviewed browser captures:

- [Same-size comparison, 16 px](comparison-16px.png)
- [Recommended comparison, 20 px](comparison-20px.png)
- [Larger comparison, 24 px](comparison-24px.png)

Open `index.html` directly. Select an option, adjust size and move the pointer across the scene to compare visibility. The enlarged preview shows the actual small rendered pixels. These browser captures preserve the original proposal; subsequent native integration is recorded below.

The shared renderer in `game/ui/GameplayHudOverlaySupport.cpp` now draws D with its existing eight solid quads: four contours followed by four ivory faces. The center, HUD scaling and mouse-look activation remain shared across indoor and outdoor gameplay. A minimum two-pixel arm gap keeps the contour from closing the aiming center at small resolutions. No raster asset or new texture-loading path is needed.

`cmake --build build --target openyamm -j25` passed. Two isolated native runs on NVIDIA/OpenGL 3.3/SDL Wayland exited successfully. All six engine-captured screenshots were reviewed at 1600 × 900 and 800 × 600. Pixel checks confirm the exact selected colors, full outline bounds and clear central 2 × 2 pixels in every shot. The fixed save and ordinary user settings were read through isolated copies. No aiming-speed measurement was performed.

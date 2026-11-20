# Original study background, 2026-10-04

The main menu returns to the candlelit scholar study from
[the original restored title](../../../../assets_dev/engine/icons_x2/title.png).
The built-in image generation tool adapted that scene for a menu on the right: the scholar, writing desk,
skull and hourglass stay clear of the controls, and the old painted title is replaced by stone.
OpenYAMM, its subtitle and all button labels remain live text in the accepted fonts.

[Native main menu](captures/16x9/main-menu.png) · [4:3 view](captures/4x3/main-menu.png) ·
[Before charcoal shading](captures/before-shading.png) · [Generation prompt](prompt.txt)

[backdrop.png](backdrop.png) is the exact returned artwork, installed as
`assets_dev/engine/hud_x2/menus/omenu_title_backdrop.png`. The original restored title and frozen dusk design
remain preserved. [generated_art.json](generated_art.json) records source, output and runtime hashes.

The main-menu layout moves its eleven title/action elements 504.5333 logical pixels to the right. Their sizes,
vertical positions, typefaces, state graphics and action ids retain their existing values. Home-page status text
fits below the moved panel; the Pause status keeps its existing position.

The user's brightness follow-up adds a 24% charcoal veil (`#080d11`, alpha 61/255) over pre-game artwork before
any live controls or lettering are drawn. This softens the warm highlights while retaining the original candlelit mood.
Gameplay-backed menus keep their existing dimming treatment.

`tour-16x9.yml` and `tour-4x3.yml` replay mouse navigation with `debug.menu_input_tour_path` through the native
menu controller. Use the authorized isolated launcher with a private save, as described in
[Desktop game runs](../../../../tools/RUN_GAME.md). [validation.json](validation.json) records the checks.

# MM7 marked-detail corrections — 2026-10-04

[Corrected map](antagrich.png) · [detail comparison](detail_comparison.png) · [game size](game_size.png)

The original `antagrich.bmp` supplies the Pit emblem, Steadwick entrance and Nighon stair references.
The Pit is a sculpted gray gargoyle/demonic visage with horned batlike sides, claw tips and an open fanged mouth.
The castle approaches use connected masonry and perspective-aligned stone steps.

Built-in imagegen performed the redraw: [map prompt](prompt.txt), [tool arguments](tool_args.json),
[map master](raw.png), then [localized Pit prompt](pit_prompt.txt), [arguments](pit_tool_args.json)
and [Pit master](pit_raw.png). The second pass corrects the first pass's malformed nose, eyes and teeth.
The retained [first pass](first_pass.png) records that intermediate result.

The final export is opaque RGB at 1280 × 960, with the original 640 × 480 logical canvas. Only the three
recorded local regions are composited into the retained map; every pixel outside them is unchanged.
The [manifest](manifest.json) records hashes, bounds, masks and both generations. Six matching destination crops
and hover images are under [buttons](buttons/); native dimensions, hit rectangles and seam borders are preserved.

Inspected both generated masters, corrected face, castle approaches and game-size export. The angular nose,
separate eyes, upper fangs and lower teeth are readable; the approaches connect to their masonry landings.
Static locality and button checks pass. The user approved deployment in the follow-up. Both backgrounds and all twelve destination highlights are
accepted and installed in `assets_dev/engine/icons_x2/`; [acceptance.json](acceptance.json) records this revision.

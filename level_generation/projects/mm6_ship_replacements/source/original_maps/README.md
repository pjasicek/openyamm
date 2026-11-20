# Original MM6 port maps

These 28 files preserve the exact map, scene, lighting and bake-recipe inputs used to prepare the approved ships.
They were copied before installation into `assets_dev` on 2026-09-29. Hashes are pinned in `../ships.json` and
`../../build/report.json`; `base_maps_root` explicitly selects this directory for subsequent builds.

This is authoring source outside runtime mounts. Do not replace it with the installed ship maps: doing so would
append the ships a second time and lose the original comparison/restore inputs.

# Castleview–Kalindra environment delivery

This package contains the MM5 outdoor environment, a reviewed Linux OpenYAMM executable and an exploration save.
Doors, entrances and interactive props report named placeholder status text. NPCs, monsters, encounters, rewards,
services and connected indoor maps are intentionally absent.

In the repository, run `./level_generation/projects/mm5_castleview_kalindra/play.sh` from the repository root.
It prepares the accepted release in the project's ignored `local_playtest/` directory on first use and preserves
that installation on later launches. Settings and saves live under `local_playtest/playtest/`, outside `/tmp`.
Initial settings come from the repository's `settings.ini`, with only the isolated asset root and MM5 startup
selection overridden (main menu, no automatic save, MM5 world/map). Later launches preserve playtest changes.
To copy the repository preferences again, run `python3 level_generation/projects/mm5_castleview_kalindra/configure_playtest.py`.

The installer requires the existing OpenYAMM development asset base with MM7/MM8 donor worlds. It verifies the
recorded registries, scripts and referenced artwork, then creates an isolated composition with its own settings and
saves. Three appended registries belong to that composition's `engine/`; the MM5 world owns geography, art and Lua.
The supplied base remains unchanged. Keep the base available while using the installed map.

After extracting `mm5_castleview_runtime.zip`, run from the extracted `mm5_castleview` directory:

```sh
python3 install_delivery.py --base-assets /path/to/OpenYAMM/assets_dev --destination /tmp/mm5-castleview-play
/tmp/mm5-castleview-play/play-mm5.sh
```

Choose **Load Game → castleview_start**. This is the calibrated level-25 exploration party with 50,000 gold and
40 food, not the future campaign starting balance. Subsequent saves stay in the new installation's `playtest/saves`.
Use a new destination for another installation; the installer never replaces existing saves or settings.

`manifest.json` records runtime file hashes, donor dependencies and native counts. `registrations.json` lists the
appended map, navigation and terrain rows. The executable needs the same Linux system libraries as this OpenYAMM
build. Editable geometry, authoring scripts, design data, calibration links and visual evidence are retained in
`level_generation/projects/mm5_castleview_kalindra/`; see `REBUILD.md`, `GOAL.md` and `PROGRESS.md` there.

The project records final archive/install hashes and review results in `delivery/latest.json` and `COMPLETION.md`.
Historical candidates remain separate; use the release linked there for the accepted environment.

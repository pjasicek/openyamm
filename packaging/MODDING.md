# Changing the game's files

A release keeps its content in content packs: the zip files in `assets/packs/`, listed with their sizes in
`assets/index.json`. On every start the game compares each pack's size with the index. When a pack is missing or
has a different size, it treats the content as damaged and downloads that pack again, whatever
`check_for_updates` says. An update also replaces every pack whose size differs. A pack you edit is therefore
overwritten at the next start.

There are two ways to change files that last:

| | `mods` folder (recommended) | `keep_modified_packs=on` |
|---|---|---|
| What you change | copies of single files, next to the packs | the packs themselves |
| Updates | keep working; your files stay | off until you switch it off |
| Undo | delete the file from `mods` | `keep_modified_packs=off`: the game downloads the original packs again |

Both apply to the downloaded releases for Windows, Linux and macOS. Development builds that use `assets_dev/`, and
Android, ignore them. "The game folder" below is the extracted folder on Windows and Linux, and
`~/Library/Application Support/OpenYAMM` on macOS, where the app installs itself.

## The `mods` folder

Put a file into a folder named `mods` in the game folder (the folder with `settings.ini`, `saves/` and
`openyamm.log`). Use the same path the game uses for it: the file then replaces the game's own, and the packs stay
untouched.

The path is the pack's `mount` in `assets/index.json` followed by the file's path inside the pack. `engine.core`
mounts at `/engine`, so `data_tables/house_data.txt` inside it becomes:

```
OpenYAMM/
  settings.ini
  assets/...
  mods/
    engine/
      data_tables/
        house_data.txt
```

A pack mounted at `/engine/models` puts its files under `mods/engine/models/`, and a world's files go under
`mods/worlds/<world>/`, for example `mods/worlds/mm6/`.

- Only `mods/engine/` and `mods/worlds/<world>/` are used; anything else in `mods` is ignored, except named mods:
  folders with a `mod.yml` that `mods/enabled.yml` switches on, as the Map Studio installs them
  ([Named mods](../devdocs/NAMED_MODS.md)). Your loose files are read in front of named mods.
- Use the exact file names from the packs, including lower and upper case.
- Only files the game reads as they are can be replaced: text tables, Lua scripts, YAML files, sounds and music.
  Textures and models are cooked files in the packs, so a mod has to replace the cooked file, not the PNG or GLB
  it came from.
- Updates and the start check never look into `mods`. After an update the game still uses your copy, even when
  the new version changed that file. If something breaks after an update, update your copy or delete it.

At every start, `openyamm.log` lists the files from `mods`:

```
Mods: engine/data_tables/house_data.txt replaces the game's file
Mods: 1 file from C:/Games/OpenYAMM/mods
```

`is a new file` means the game has no file at that path. Check the path when you meant to replace one.

## Editing the packs: `keep_modified_packs`

Use this when you want to change the pack zips themselves and give up updates for as long as you do.

1. Download the release and start it once, so it downloads its content. The installation is then complete.
2. Close the game and open `settings.ini` in the game folder with a text editor. Add these lines, or add
   `keep_modified_packs=on` below an `[updates]` line that is already there:

   ```ini
   [updates]
   keep_modified_packs=on
   ```

3. Edit the packs in `assets/packs/`. Keep each pack's file name, keep it a valid zip, and leave
   `assets/index.json` as it is. Packs whose size changed then still load.
4. Start the game. `openyamm.log` says
   `Content: keep_modified_packs is on; the game neither checks, restores nor updates its packs`.

While it is on:

- The game does not check or restore the packs. A broken zip that you made shows up as an error when the game
  reads it.
- A missing pack stops the start with a message naming it. Put it back, or switch the setting off as below.
- The game does not look for updates. Settings → Updates → Check Now says that updates are off, and the start
  question about updates does not appear. `check_for_updates` makes no difference.
- The game saves the setting as `keep_modified_packs=true`. Settings → Defaults does not reset it.

To return to normal, set `keep_modified_packs=off` or delete the line. At the next start the game downloads the
original version of every pack you changed and then updates as usual. Keep copies of your edited packs if you
want them back.

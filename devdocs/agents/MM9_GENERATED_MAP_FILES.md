# MM9 generated map files

Moved from the root `AGENTS.md` on 2026-11-24 (unchanged). The root keeps a one-line rule and points here.

- MM9 map Lua (`assets_dev/worlds/mm9/events/maps/<stem>.lua`, headed "... convert.py writes this file") is generated
  too: each map's converter in `level_generation/projects/mm9r_<map>*/` (`convert.py`, and `citylua.py`,
  `regionlua.py`, `council.py` ... where the project has them; the regions' projects are `mm9r_<map>_blv`, whatever
  the header says) writes it on every conversion, and promotion copies it over `assets_dev`. Never edit only the
  installed file. Change the converter, then build the map into a scratch folder (`convert.py --scratch <dir>`), check
  that `<dir>/runtime/<stem>.lua` differs from the installed file by your change alone, and install it into
  `assets_dev` and the map's review root (`output/mm9_rework/isleofashes_blv_root` for the regions, Bootcamp and the
  Afterworld, `output/mm9_rework/assets_dev` for the rest). A converter-wide change goes in
  `level_generation/projects/mm9r_common/`. `tools/mm9_import_discovery/check_mm9_map_lua.py` lists the scripts that
  differ from their review root (an edit in one place only); run it before and after MM9 map Lua work. The same holds
  for the scene files the converters write (`<stem>.scene.yml`, `.blv`; a region's scratch scene lacks the `terrain`
  block, which its convert.py adds only when installing). The hand-written MM9 Lua is
  `worlds/mm9/events/common/mm9_common.lua` and `worlds/mm9/behaviors/*.lua`: edit those directly.

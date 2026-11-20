# MM7 Water Elemental m210: attack carried over from MM8 m500 (attacks-2, 2026-11-11)

The re-animated Attack of `mm8_m500` (see `../mm8_m500_attack_claude/README.md`) carried to the MM7 copy by
re-running `mm7_m210_claude/scripts/build_glb.py` (binary chunk identical to the new MM8 GLB, MM7 palettes 501-503)
and installing `export/mm7_m210.glb` with `tools/install_model.py --world mm7`. glb_diff against the claimed GLB:
only the Attack channels. Bindings unchanged (impact 0.875). Motion ratio 0.19 -> 0.81. Checks: `review/finish.txt`.
Backup: `work/before_attacks/`.

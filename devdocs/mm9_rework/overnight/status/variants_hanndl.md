# Variant Hanndl (owner variants-b, 2026-11-02)

- Finding: the "arm piece" is PeasantM6's (Annud's) bell-cuff flare (11 extra vertices per forearm, up to 11 cm); Hanndl.abc
  has fitted sleeves. Built from Annud's body/rig/weights/clips with the sleeves narrowed onto the forearm (+ stub tuck).
- Installed `assets_source/worlds/mm9/models/mm9_hanndl.glb`; bound `MM9 260 Hanndl` (row 260 in mm9_npc_actor_rows.tsv, 9260),
  with cower and the 17 HANNDL.abc scene clips his scripts play.
- Meshy: 20 credits (body 4K retexture 10, head 4K retexture 10).
- Regression mm9_actor_models_build_every_binding PASS (198 descriptors on 86 models). Final gates: see the README.
- Final (lined) install sha256 99c719f1...; collar and belt rims lined (neck cap + rim_lining, DM2's scripts), clips grafted
  unchanged from the accepted build. Regression binding PASS (204 descriptors on 90 models). Lease released.

# Re-light: Chasm of the Dead (`chasmofthedead`)

**State: DONE (2026-10-31 05:06).** Lightmap-matched bake and MM9 model lighting installed; record in
`level_generation/projects/mm9r_chasmofthedead/README.md` "Baked lighting".

- Profile: direct 0.9 -> **0.41**, ambient 2.4 -> **0.46**, sky 0.7 -> **0.12**, `max_lighting` 4 -> **1**, bounce 6.
  Recompose only. Old profile: `work/profile_capture_matched.yml`. Zones: the existing `dat_lightmaps.py` (ten named).
- Per-zone ratio before -> after: entry_tomb 4.77 -> 1.00, pillar_hall 4.37 -> 0.95, hall2 5.37 -> 1.13, canyon_floor
  4.42 -> 1.10, canyon_rim 2.93 -> 1.50 (the sky faces in the box; walls x0.78), pool_hall 4.23 -> 0.93, octagon
  4.35 -> 0.92, mummy_hall 4.67 -> 0.96, south_corridor 4.75 -> 1.05, crypt 4.33 -> 0.97. Tombs bluer than before
  (B/R 1.28-1.64, MM9 1.39-1.87).
- Screen (56 views): capture 101.4, unbaked 52.2, old 98.7, **new 24.9**. Darkest `20-m09_tunnel` 15.3 (tunnels read
  nearly black by eye; no floor added since none is under 12).
- Props: **`model_lighting: true`** (rebuild; BLV identical): props under x0.6 of their view old 8 (black dais, urns,
  sarcophagus), model 0; relative brightness capture 1.17, old 1.58, model 1.43.
- Scenarios chests, doors_exits, pivot, scripted pass after the rebuild.
- `stale_bakes.py --check`: not listed. Sheet (looked at): `mm9r_chasmofthedead/review/lighting_v05_compare.jpg`,
  `_p01-p10`.
- Not checked: no real MM9 screenshot; the 4 capped lights do not reach models.

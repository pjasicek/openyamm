# Re-light of the five pre-overnight MM9 dungeons (2026-10-31)

Calibrating the maps built before the overnight run to MM9's DAT lightmaps (texture x lightmap x1) instead of the old
import capture. Order: templeofhonk, anskramkeep, drangheimprison, chasmofthedead, lichlab. Shared helpers (new, read
only on the converter): `level_generation/projects/mm9r_common/relight_fit.py` (fit the profile scales from saved passes
per zone and room), `relight_zones.py` (k-d zone boxes), `relight_tour.py` (one lighting tour run), `relight_views.py`
(per-view numbers and sheets), `relight_props.py` (old path against model_lighting), `relight_table.py` (ratio table).

| Map | State | Zone ratios before -> after | Darkest baked view | Props | Sheet |
| --- | --- | --- | --- | --- | --- |
| templeofhonk | done | 1.69-2.06 -> 0.90-1.07 | 44.2 (NW corridor) | old path (model lighting 0.74 vs 1.15) | `mm9r_templeofhonk/review/lighting_v03_compare.jpg` |
| anskramkeep | done | 1.11-1.47 -> 0.84-1.11 | 17.6 (gate switch) | old path (model lighting draws furniture black) | `mm9r_anskramkeep/review/lighting_v06_compare.jpg` |
| drangheimprison | done | 1.08-1.33 -> 0.96-1.06 (+ teal floor tint) | 15.4 (lower stairs) | model_lighting: true (1.40 vs old 1.81, no dark props) | `mm9r_drangheimprison/review/lighting_v07_compare.jpg` |
| chasmofthedead | done | 2.93-5.37 -> 0.92-1.13 (rim 1.50: sky faces) | 15.3 (tunnel) | model_lighting: true (old path: 8 views of black props) | `mm9r_chasmofthedead/review/lighting_v05_compare.jpg` |
| lichlab | done | 0.96-1.28 -> 0.78-1.09 (pods 0.78) | 16.6 (east wing) | model_lighting: true (old path: 14 views of dark props) | `mm9r_lichlab/review/lighting_v05_compare.jpg` |

Per-map records: `relight_<map>.md` here.

All five done (2026-10-31). Every map: `--recompose` of the saved passes (no Cycles bake), old profile in the project's
`work/profile_capture_matched.yml`, `stale_bakes.py --check` does not list it, scenarios pass after the model-lighting
rebuilds. No map needed the player-light floor (every baked view is over luma 15). Prop lighting: Temple of Honk and
Anskram Keep keep the old path (model lighting drew their furniture darker); Drangheim Prison, Chasm of the Dead and the
Lich Lab now use `model_lighting: true` (the old path drew props black under their darker bakes).

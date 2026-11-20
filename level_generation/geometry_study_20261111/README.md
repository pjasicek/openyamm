# Building geometry study (New Sorpigal, 2026-11-11)

What a geometry upgrade of MM6–MM8 BModels could realistically look like. Exploration only: nothing is installed.

- `tour.yml`, `captures/`: the user's 11 poses on `oute3.odm`, captured with the engine screenshot tour.
- `briefs/`, `run_concepts.sh`, `concepts/`: Codex image edits of views 01, 03, 05, 07, 08 in two tiers:
  A (modular, ~1.5–4k triangles per building) and B (hand-modelled hero, ~8–15k).
- `compare/`: Now / A / B stacked per view. `page/`: the review page
  (https://claude.ai/artifact/SA4wRGFvmbU6uMPV52SzAg).

Findings: New Sorpigal's 90 BModels total 8,322 triangles (MM9 Arslegard, interiors included: 37,841).
Recommendation: tier A, generated from the surface material class/height maps (window/door/timber locations) plus
roof/edge passes, drawn as a visual mesh over the original faces, which stay for collision, events and picking.
Suggested pilot: `HseR3W` (view 03) and the tavern porch (view 01).

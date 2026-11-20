# Grass height, density and transition coverage

The accepted v4 placement adds smooth density patches, occasional 1.8× taller clumps, and working grass on the
grassy portions of all twelve dirt/grass transition tiles. Existing four-shape artwork, wind, fade distance,
console toggle and optional settings switch are retained. The normal build and separate ground-cover trial are refreshed.

## Missing transition grass

The authored masks and terrain texture orientation agree: north is at the top, white is grass, black is dirt.
The previous loader read the blue component of grayscale PNGs. The bimg R8 conversion supplies intensity in red
and zero in blue/green, so all grass coverage became zero and all inverted stone coverage became 255.
Reading red fixes both cases. The focused regression test loads all twelve real masks through the engine loader
and verifies that each produces grass with roots inside its grassy portion.

Short grass now uses a four-unit root footprint with probabilistic acceptance through the grassy side of the blend.
Taller clumps and stones keep full-width clearance, including neighbouring cells. Tall clumps also have increased
building clearance. The pure dirt and road areas remain clear of grass.

## Distribution and cost

- Base grass attempts: 50 per cell before exclusions; stones: 10.
- Smooth world-space density variation: 0.8, noise spacing: 768 units. No independent square density steps.
- Taller-clump chance: 0.08, modulated toward denser patches; height scale: 1.8 with existing size randomization.
- Optional per-rule density multiplier and a 128×128 cell-centred density mask support authored local suppression.
  The shipped map uses procedural variation without an extra density image.
- Full-map instances: **81,072**, versus **79,781** before (+1.6%); instance bytes: **5,188,608**.
- Occupied cell/kind patches: **3,416**. Grass and stone ranges are grouped separately so populated mixed tiles
  remain compatible with contiguous draw merging. Patch count is not draw count.
- Placement, mask sampling, density and height choice run once on load/first enable. No additional per-frame
  algorithm, shader work, texture layer or instance data field was introduced. Larger silhouettes can still cost
  more GPU pixel work. The existing 20 Hz stationary cache and immediate camera invalidation remain.

The retained `placement_audit.txt` was produced by a temporary native placement test, removed after diagnosis.
At cells x=43..47, y=85 immediately south of the town road, the final masks now permit 25/35/34/32/25 grass instances
respectively. These transition cells previously received no grass. Road cells at y=84 receive no decorations.

## Visual review

- [Meadow before](grass_variation_before_moved.png) and [v4 meadow](grass_v4_meadow_moved.png): taller silhouettes,
  uneven patches, retained short grass base. Scripted walking also checked grounding and distance coverage.
- [Before the channel correction](grass_variation_edges.png) and [corrected transitions](grass_v4_edges.png):
  grass follows the green portions of the near transition tiles; the dirt path stays clear.
- [Final production build](grass_v4_final_edges.png) repeats the town-edge check after grouping mesh kinds for merging.
- Intermediate `grass_variation_after*` images predate the channel correction and final density rebalance.
  They are diagnostic captures, not the accepted configuration.

Screenshots use the approved Xvfb capture wrapper and are visual evidence only. Their software-renderer FPS is
not a hardware performance measurement. Camera coordinates and binary hashes are retained alongside each capture.

## Verification

Normal development build passed. Fourteen focused cases passed (135,521 assertions), including real authored masks,
soft blend acceptance, material exclusion, deterministic density/height variation, bounded population, density-mask
suppression, cell/kind grouping, taller bounds, the existing culling/cache tests, and alpha mip coverage.
See `unit_tests.log`. Temporary placement diagnostics were removed from the final test source.

Desktop on/off results and final binary/content hashes are recorded in `validation.json`; raw timing records are
`desktop_on.json` and `desktop_off.json`. These are separate timed launches with normal simulation, not isolated
GPU timer measurements or a controlled same-process benchmark.
On the RTX 3060 Ti these runs reported 2,114.65 FPS enabled and 1,643.93 disabled. The reversed ordering makes this
pair unsuitable for estimating decoration cost; it is not evidence of a speedup. Both runs loaded the requested
camera, completed, and exited with code 0. No claim of unchanged GPU time follows from the population budget.

Run `./level_generation/terrain/mm6_ground_cover/play.sh` and restart an already-running trial to load the new content.
The peasants enhanced launcher was not modified. Density/height configuration changes require a map reload or restart;
the console on/off toggle intentionally retains the current placement.

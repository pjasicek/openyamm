# MM6 Wyrm retopology pilot (2026-10-13)

Pilot only, not installed: can procedural retopology bring the installed Wyrm (`mm6_drr1_claude/`, owned by the
Codex session `codex-wyrm-20261013`; 14,413 triangles, its decimation stopped there because 12,972 faceted) much
lower without visible loss, keeping its rig, clips and textures? Method: [guidelines section 8](../../GAME_ASSET_MODELLING_GUIDELINES.md).
Source: snapshot of `mm6_drr1_claude/export/mm6_wyrm.blend` (`work/source_snapshot.blend`).

## Round 2 (after user review): adaptive isotropic remesh, one continuous surface

User review of round 1 (h1000): holes and mismatched texture patches at the spine bases and in the chest, a wrong
mouth/throat bake, collapsed toes with floating claws. Cause: original protrusion pieces layered on top of a smooth
remesh. User priority: no feature changes; more triangles are fine; re-texturing afterwards is fine.

Round 2 remeshes the whole body as one surface with MeshLab's curvature-adaptive isotropic remeshing
(`scripts/remesh_ml.py`: adaptive edge length, feature edges above 35 degrees kept, every vertex within a maximum
distance of the source surface), no layering; small separate source pieces unreduced.

| Variant | Triangles | vs source | Open edges (source 231) | Deformation mean / p99 / max |
|---|---:|---:|---:|---|
| `a14` (1.4 % edge, 0.15 % max distance) | 9,130 | 63 % | 210 | <= 0.03 / 0.62 / 3.4 mm |
| `a18` (1.8 %, 0.18 %) | 8,071 | 56 % | 212 | <= 0.02 / 0.51 / 2.2 mm |

Spines, throat barbel, belly plates, feet, toes and claws match the source in close renders (`review/a14`, `review/a18`);
no new holes. Viewer: `review/viewer/` (original, a14, a18; all clips).

## Round 1 result (superseded)

| Variant | Triangles | vs source | Notes |
|---|---:|---:|---|
| source (installed LOD0) | 14,413 | 100 % | Meshy Smart Topology after cleanup |
| `v450` | 4,932 | 34 % | body reads the same; face slightly softer |
| `h1000` | 6,994 | 49 % | denser face (Un-Subdivide only away from Head/Jaw), whole spike bases kept |

Renders: `review/<tag>/` (source vs retopology in Standing/Attack/Walking, three-quarter/side/head, wireframes).
Deformation (`scripts/deform_check.py`, every 2nd frame of all eight clips, distance of each deformed retopology
vertex to the deformed source): mean 0.04-0.10 mm, 99th percentile < 1 mm, max 3 mm (Death/Dead) on a 1 m model.
The transferred weights follow the source in every clip; no vertex is unweighted.

## Pipeline (`scripts/retopo.py`, `scripts/remesh_im.py`)

1. Split the source: main body; small separate pieces keep their geometry, UVs, weights and textures.
2. Export the body triangles; Instant Meshes (PyNanoInstantMeshes in a separate venv; pure quads, align to
   boundaries, two smoothing/reprojection steps, deterministic). Blender's QuadriFlow refused even a verified
   manifold, consistently wound voxel mesh ("needs to be manifold"), so it was dropped.
3. Import, weld, fill remesher holes up to 12 sides; optional Un-Subdivide away from `REA_FINE` bone regions.
4. Shrinkwrap (Target Normal Project) onto the source.
5. Protrusions: source faces more than 10 mm from the new surface (horns, back spines, tail spikes), grown two rings,
   are kept as original geometry with their UVs and textures, reduced to 55 %; a normal map cannot restore them.
6. Material per face from the nearest source face; triangulate; weights by Data Transfer (Nearest Face
   Interpolated), limit 8, normalise.
7. New UVs per material (Smart UV Project), bake base colour (Diffuse colour) and tangent normals from the source
   (selected to active, 5 mm extrusion, 15 mm rays: longer rays reached the neighbouring leg, shorter missed the
   inner thigh).

## Findings and open work before a production switch

- The method works: two to three times fewer triangles with the same silhouette and texture in all clips.
- Thin protrusions must stay geometry (first attempt lost the horns, spines and tail fan).
- Remaining defects: the chin barbel (a separate source piece) fragments when reduced (keep such pieces unreduced,
  about +600 triangles); Smart UV Project fragments the bumpy body into many islands (texel use is poor; a seam-based
  unwrap or UV transfer from the source with island handling would be better).
- Not yet rebuilt for the new mesh: region mask and tier ramps, metal/roughness, burn maps, the head-material merge,
  LODs and the runtime build/install. All are re-bakes or reruns of existing tools on the new UVs.
- Installing it needs coordination with the Wyrm's owner (`codex-wyrm-20261013`).

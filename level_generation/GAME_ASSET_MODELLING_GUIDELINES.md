# Game asset modelling guidelines (topology, normals, UVs, materials, LODs)

Distilled from official sources (read 2026-10-13, list at the end; retopology section 8) and mapped onto the OpenYAMM model runtime
(`engine/render/MODEL_RENDERING.md`). Use it for every hand-built or cleaned-up mesh: creatures, props, decorations
and attachments. Meshy returns and decimations are checked against the same rules. Where the engine forces a
different choice, the deviation is stated here, not silently made per asset.

## 1. Triangle budget and distribution

- **Fewest triangles for the required quality.** "Use the fewest number of triangles possible to get the quality
  required" (Arm 2.0); "only have as much geometry as necessary" (Khronos 1.0, Geometry). Budget by visual complexity
  and by how many copies are on screen at once (Arm 2.1; Android); this repository's ceilings are in the creature
  playbooks (~5k rigid, ~5–8k clothed humanoids, 15k hard ceiling).
- **Spend triangles on the silhouette.** "Focus on big shapes and forms that contribute to the silhouette of the
  object instead of the detail" (Arm 2.3); "edges are removed that do not contribute to the silhouette" (Arm 2,
  figure 2). Round silhouettes get their segments; flat or straight spans get none: a straight cylinder wall needs
  only its top and bottom rings.
- **Fine detail goes into textures and normal maps, never triangles.** "Do not model intricate details using high
  density triangle meshes and use textures and normal maps for fine detail" (Arm 2.3); "small surface geometric
  details should be baked into normal maps" (Khronos 1.0). Rivets, seams, panel lines, grilles, scratches: texture.
- **Fewer triangles where the camera rarely looks; delete what is never seen** (Arm 2.3, Android): undersides resting
  on the floor, interiors hidden by other parts, inner faces of closed housings.
- **No micro triangles.** Triangles "smaller than 1 to 10 pixels" still cost vertex work and bandwidth; keep
  triangles "above 10 pixels in area" at normal viewing distance (Arm 2.4, Android). Check thin rods, small balls and
  bevel strips at the distance players actually see the asset, and give them fewer segments.
- **No long thin triangles.** Keep triangles "close to equilateral"; thin slivers are more expensive and "shiny
  material on an object with long thin triangles" flickers (Arm 2.5, Android). Narrow bevel lips on large rings are
  the usual source: keep them only where they read at game distance, and drop them in LODs.
- **No high-valence vertices.** "Avoid single vertex points that have a large number of edges connected to them
  (i.e. high valence vertices with 10+ edges)" (Khronos 1.0). Close discs and lathe apexes with an inner ring and a
  strip-triangulated cap instead of a 32-spoke fan; sphere poles use at most 8 segments.

## 2. Topology and triangulation

- **Author in quads, triangulate last and deliberately.** "Quads ... are recommended for source models, using
  triangulation only for final asset optimization" (Khronos 1.0); Unreal ranks "model the mesh with only tris" and
  "triangulate in the 3D app" above exporter/importer triangulation ("Automatic triangulation can lead to undesirable
  results"). glTF stores triangles only (Khronos 2.0; Blender glTF add-on). Generators triangulate quads explicitly
  (shorter diagonal) so export and engine see the same triangles.
- **No n-gons** in sources (Khronos 1.0: "not recommended because there can be some ambivalence as to how they get
  drawn").
- **Clean, tidy topology where it deforms; perfect edge flow is not required on rigid parts** (Arm 4.2). Rigid
  hard-surface parts bind 100 % to one bone each; never split one connected shell between bones that move apart.
- **No holes, gaps or non-manifold geometry on visible surfaces; separate parts for separate components** (Khronos
  1.0: "We do not advise creating a very complex model from a singular mesh"). Open shells are fine only where another
  part hides the opening.
- **Anything whose back is visible needs thickness or a back face** (Khronos 1.0), including surfaces seen through
  glass.

## 3. Normals, hard edges and bevels

- **Define hardness with smoothing/sharp edges or custom normals, and export them** (Arm 4.1; Android; Blender
  `sharp_edge`). In generated meshes a hard edge is a vertex split between smooth sections; curved surfaces stay
  smooth.
- **Bevels instead of knife edges; face-weighted normals keep large faces flat.** "Bevel all product edges ... There
  are no perfectly pointed edges in everyday life" (Khronos 1.0); "face-weighted normals can be used to improve the
  look of rounded edges such as bevels" (Khronos 2.0). Blender's Weighted Normal modifier (Face Area mode, Keep Sharp)
  or Bevel > Harden Normals does this for authored meshes; generated lathe profiles get the same result by making a
  small bevel its own smooth section between hard edges.
- **Hard edges split vertices, and so do UV seams.** "A vertex must be split if it has multiple normals, UV
  coordinates or vertex colors" (Unity); "vertices are split on export if they contain more than one of each type of
  mesh data" (Khronos 2.0); "Discontinuous UVs and flat-shaded edges may result in moderately higher vertex counts"
  (Blender glTF). Put hard edges and UV seams on the same edges, so each costs one split, and a baked normal map does
  not show seams there ("UV islands split and can reduce the quality of a normal map when we bake", Arm 4.1).
- **No shading errors or black polygons** (Khronos 1.0): consistent outward winding, no overlapping faces,
  recalculated normals. The OpenYAMM cook back-face-culls opaque double-sided creature materials, so inverted
  faces disappear in game rather than render black: check winding numerically before export.
- **Normal maps: OpenGL convention (+Y up, glTF) and MikkTSpace** (Khronos 1.0). OpenYAMM derives the tangent frame
  from screen derivatives and needs no TANGENT attribute (`MODEL_RENDERING.md` §1); Meshy maps (+Y down) are flipped by
  `tools/prepare_actor_glb.py`.

## 4. UVs and texel density

- **One consistent texel density for the whole asset**, deliberately lower for hidden or rarely seen parts (Khronos
  1.0: "each piece of the model gets the same amount of visual texture space"). Record the density in texels per metre.
- **All UVs inside 0–1, no accidental overlap, little wasted space** (Khronos 1.0/2.0). Deliberate overlap is allowed
  for identical repeated parts and mirrored halves (Khronos 2.0: "there are cases where it may be beneficial"), but
  not where the parts need different baked lighting or wear.
- **Seams on natural breaks or hidden areas; few, large, contiguous islands** (Khronos 1.0).
- **Padding against mip bleeding.** Touching islands bleed "made worse by MIP mapping" (Khronos 2.0, no number given).
  Repository rule: at least 8 texels between islands on 2K maps (4 on 1K), and colour/masks dilated into the gutter
  (`CLAUDE_CREATURE_TEXTURES.md`).
- **No visible stretching**: check with a checker/grid texture (Khronos 1.0).
- **Measured targets for Meshy-textured meshes** (repository, 2026-10-30): atlas use 55 % or more (70 % ideal), density
  spread p90/p10 <= 1.3, at most 3 % of the surface on islands under 8 triangles, stretch p90 <= 1.5, measured with
  `level_generation/creatures/claude_shared/texture_quality.py`. Lay the UVs with `claude_shared/uv_atlas.py`, have Meshy
  paint at 4K and downsample once. Recipe and pitfalls: [texture quality pass](creatures/claude_shared/TEXTURE_QUALITY_PASS.md).

## 5. Materials and textures

- **Metal/roughness PBR; base colour without baked lighting; ORM packing R = occlusion, G = roughness, B = metallic**
  (Khronos 1.0/2.0; Blender glTF). Use factors instead of textures for single values (Khronos 1.0).
- **Base colour between sRGB 30 and 243**, most surfaces well inside it (Khronos 1.0, with a measured table: iron
  196,199,199; aluminium 245,246,246; copper 250,208,192; charcoal 30; fresh snow 243).
- **Metallic is binary**: "Pixels should be either white (metal) or black (non-metal). Gray values should only be
  used for anti-aliasing" (Khronos 2.0). Engine note: indoor OpenYAMM lighting has weak environment reflection, and
  fully metallic texels have no diffuse term, so very dim rooms can render pure metal too dark (Patrol Unit). Check
  in game; if a partial-metal value is needed, record it per asset as an engine-driven deviation.
- **Power-of-two textures; 1K or 2K for base colour, ORM and emission; ORM may be smaller than base colour; PNG
  sources** (Khronos 1.0). Repository sizes are in `CLAUDE_CREATURE_TEXTURES.md` (2K base, 1K normal/MR/mask).
- **Few materials per model**; a second material only for a different shader (Unity: "Keep the number of materials
  on each model as low as possible"). In OpenYAMM each material is one draw per LOD.
- **Transparent parts get their own material and their own mesh** (Khronos 1.0). For OpenYAMM creatures that means a
  separate mesh node: `tools/build_actor_lods.py` merges shadows only over opaque materials. Blended triangles keep
  their authored order, which is their draw order (`MODEL_RENDERING.md` §3).
- **Self-lit surfaces** (screens, glowing liquid, energy): OpenYAMM supports `KHR_materials_unlit` with a base
  colour texture, and a constant `emissiveFactor`; there is no emissive texture and no time-animated material on
  skinned actors (their material clock is fixed at zero). Animate such surfaces with bone-driven geometry instead.

## 6. Skinning, scale and orientation

- **One skinned mesh, few bones, few influences** (Unity: one Skinned Mesh Renderer; "linear blend skinning with a
  maximum of four influences per vertex"; extra bones cost little when unanimated). Rigid parts use one influence.
- **1 unit = 1 metre, origin at the bottom centre, transforms applied** (Khronos 1.0/2.0; Unity; Unreal pivots).
  OpenYAMM creatures face −Y in Blender (glTF +Z, the Khronos front) and use `yaw_offset` in `actors.yml`.
- **A shape swap hides the unused mesh, not just its bones.** A creature that turns into something else on death
  (gargoyle body → 36 rubble pieces) keeps both meshes; bones scaled to almost nothing still draw, skin and shadow
  every triangle. The renderer skips only a mesh whose own node matrix is singular, so run
  `tools/model_hide_collapsed_meshes.py <export.glb> --write <keyed.glb>` and install the keyed copy: it keys each
  mesh node's scale to 0 wherever all its bones are collapsed (report only without `--write`). Attachments such as
  remains props are skipped already when their socket node is scaled to exactly 0 (Wyrm).

## 7. LODs

- **About 50 % fewer triangles per level** (Arm 3.1, Android, Unreal LOD group defaults `LODPercentTriangles=50`);
  too little reduction gains nothing, too much makes switching visible. "Do not use very dense triangles on lower
  LOD" (Arm 3.1).
- **Preserve the silhouette and remove flat-area polygons first** (Arm 3: "focus on the silhouette"; "Remove polygons
  on flatter areas and use mipmap as LOD for texture").
- **Test each LOD at its switch distance**, not up close (Arm 3.1). OpenYAMM switches colour LODs down at
  450/180/72 projected pixels (500/200/80 with 10 % hysteresis) and picks shadow LODs on their own.
- OpenYAMM creatures and props: follow the [LOD playbook](creatures/LOD_PLAYBOOK.md) (far-LOD ladder, own far textures
  by UV correspondence, shadow LODs, gates, in-game checks, reruns after any LOD0 change). `tools/build_actor_lods.py`'s
  0.5/0.18/0.06 ratios give LOD1 only; its LOD2/LOD3 are replaced by the playbook's ladder.
- **Skip LODs for assets that are already simple** (Arm 3; Android).

## 8. Retopology and high-to-low baking

On-demand procedure with everything learned on the Wyrm (remesh ladder and stop rule, hole detection and repair,
retexture, colour repairs): [creature retopology playbook](creatures/RETOPOLOGY_PLAYBOOK.md). Not a default step.

Retopology builds a new, clean low mesh over a dense or messy source (a Meshy return, a sculpt) instead of collapsing
the source's own triangles. The source stays as the bake source; the new mesh gets the rig weights, new UVs and
baked maps. It is the route for "far fewer triangles without visible loss", because the lost shape returns as
normal-map shading.

**Tool choice (official docs).**
- Blender's built-in remeshers (Properties > Data > Remesh). *Voxel* gives "uniform topology and has no inner
  (self-intersecting) geometry": use it to clean a copy into a manifold input, not as final topology. *Quad*
  (QuadriFlow) is slower and "doesn't clean up intersecting geometry"; options Use Mesh Symmetry, Preserve Sharp,
  Preserve Mesh Boundary, target by Ratio / Edge Length / Faces, Seed. The manual does **not** recommend either for
  "final topology for deforming meshes" or for "reducing the face count of an otherwise clean mesh" (Decimate is
  meant for that). Treat any automatic result on a deforming creature as a candidate that must pass the deformation
  gates, never as accepted by default. Both ignore modifiers and shape keys.
- QuadriFlow command line: "We take a manifold triangle mesh ... and generate a manifold quad mesh"; non-manifold
  input goes through its Manifold converter first; `-f` face count, `-sharp` keeps sharp edges (off by default),
  `-sat` removes flips for a watertight result.
- Instant Meshes command line (field-aligned; Modo's auto-retopology since 10.2): exactly one of `-f` faces,
  `-v` vertices or `-s` edge length; `-c <degrees>` crease angle (off by default), `-d` deterministic,
  `-S <iter>` smoothing and reprojection steps (default 2), `-b` align to open boundaries, `-r`/`-p` field symmetry
  (4 = quads). Edge flow can be steered only with its GUI brushes, not from the command line.
- Quad Remesher (Exoside, paid Blender add-on), whose user guide gives the clearest density and edge-flow practice:
  *Adaptive Size* (default 50 %, "well suited for many cases") makes quads smaller on curvature and bigger on flat
  areas; *Adaptive Quad Count* off respects the target count, on respects shape; *vertex-colour density* paints
  0.25x-4x edge length per region; *guides* force edge loops along material boundaries, hard edges, normal creases or
  hard edges detected by angle (> 30 degrees). "Adding badly defined guides can confuse the algorithm."

**Density and edge flow.** Spend quads on curvature and on what players look at (head, hands, weapon); keep flat
areas coarse. Without a density-painting tool, remesh regions separately at their own density and join them along
natural seams (the head-graft and bridge-loft tools in the creature playbooks). Put loops where the mesh bends: Unity
asks to "consider how the vertices and triangles of the model distort as it animates" and to refine "polygon detail
where you need it (such as the underarms)". Guide loops with material or face-set boundaries around joints, eyes and
mouth when the tool supports guides. Clean the input: "cap holes, weld vertices, and remove hidden faces" (Unity).

**Fit, weights, UVs (Blender).**
- Shrinkwrap the new mesh onto the source: *Target Normal Project* is the smoothest ("ignores flat shading", slower);
  *Nearest Surface Point* is the fast default; *Offset* keeps a distance.
- Transfer skin weights with the Data Transfer modifier from the original skinned mesh: Vertex Groups, mapping
  *Nearest Face Interpolated*, and **Generate Data Layers** ("the transfer may not work otherwise"). Then limit
  influences (engine maximum 8; Unity's guidance is four) and normalise. Rigid parts (claws, props) keep one bone.
- New UVs after the remesh (the old islands do not apply); UV islands split at every hard edge (section 3).

**Baking (Blender Cycles; Marmoset's baking guide for practice).**
- Bake *Selected to Active*: rays go "from the low-poly object inwards towards the high-poly object". Use a cage
  (Cage Extrusion) that "extend[s] just far enough to cover the highest points of the high poly"; a smoothed
  (averaged) cage avoids gaps at hard edges and is "recommended for most purposes". Without a cage, set Max Ray
  Distance. Avoid hard splits on the low mesh during the bake ("they will lead to non-smooth normals").
- Normal: Tangent space (Blender default, MikkTSpace). OpenYAMM derives the tangent frame from screen derivatives
  instead (`engine/render/MODEL_RENDERING.md`), so keep low-poly normals smooth and bevel or add sides where the low
  mesh turns sharply, and check baked shading in game. Triangulate the low mesh before baking so baker and engine
  share the same triangles (otherwise "x-shaped smoothing errors").
- Base colour: the *Diffuse* bake with only *Color* enabled gives the surface colour without lighting.
  Margin: *Extend* or *Adjacent Faces* against mip bleeding at seams. Bake in 16 bit, ship 8 bit.
- Limits: a normal map "can't alter the silhouette" (keep enough sides on curved silhouettes); "details smaller than
  1 pixel will not be recorded properly"; holes in the high mesh bake errors (cap them); bake intersecting parts
  (a held weapon on a hand) in separate groups so they do not project onto each other.

**OpenYAMM creature procedure (headless, scripted).**
1. Keep the accepted skinned LOD0 and its textures as the bake source.
2. Make a manifold copy (voxel remesh at a fine voxel size) as the remesher input only.
3. Remesh per region (body, head, hands, props) to a target count with Instant Meshes or QuadriFlow (crease angle on,
   deterministic), join the regions; or use Quad Remesher with density paint and guides if licensed.
4. Shrinkwrap to the source, transfer weights (Nearest Face Interpolated), limit to 8 and normalise; rigid parts
   keep their single bone.
5. Unwrap, then bake base colour, normal and AO from the source (cage, margin); rebuild region masks and ramps from
   the baked base (`CLAUDE_CREATURE_TEXTURES.md`).
6. Triangulate, run the export/LOD/region-variant build, the deformation gates on every clip, textured same-camera
   comparisons (front, side, close-ups, extreme poses) and an in-game capture. Accept the lowest count whose results
   show no visible loss; report the reduction curve.

Pilot findings (MM6 Wyrm, `level_generation/creatures/mm6_drr1_retopo_claude/`: 14,413 -> 4,932-6,994 triangles,
same silhouette and texture, sub-millimetre deformation error over all clips):
- Blender's QuadriFlow refused a verified manifold, consistently wound mesh; Instant Meshes (PyNanoInstantMeshes in a
  separate venv) worked first time. Its pure-quad output is one regular subdivision of the target (about 4x faces).
- Thin protrusions (horns, spines, spikes, toes) vanish at a uniform body density and a normal map cannot restore a
  silhouette. Do **not** layer kept original pieces over a smooth remesh: the user review found holes, mismatched
  texture patches at their bases and floating claws. Use one continuous, curvature-adaptive remesh instead: MeshLab
  isotropic remeshing (pymeshlab `meshing_isotropic_explicit_remeshing`, `adaptive=True`, `featuredeg` about 35,
  `checksurfdist` with a small `maxsurfdist`) kept every feature at 56-63 % of the Wyrm's triangles. Feature
  preservation outranks the triangle count (user, 2026-10-13); re-texturing the result afterwards is acceptable.
- Bake rays: start a few millimetres outside the low surface and keep the reach short (5 mm extrusion, 15 mm); longer
  rays hit the neighbouring leg, shorter ones miss concave areas such as inner thighs.
- Un-Subdivide on a selection only partly reverses Instant Meshes' subdivision (singularities break the grid); for
  real per-region density, remesh regions separately or use a density-painting remesher.

## 9. Validation before hand-off

Triangle and vertex count after export (vertex splits included); winding/normal check with no inverted or black faces;
no degenerate, micro or sliver triangles at game distance; UVs in 0–1 with padding and a checker render; texel density
recorded; base colour range 30–243; transparent parts on their own node; GLB re-imported in isolated Blender; in-game
capture at the real viewing distance (Khronos: test on the target, "Performance must be tested on-device").

## Sources

- Khronos 3D Commerce, *Real-time Asset Creation Guidelines* 1.0 (2020) and 2.0 summary (2025):
  https://github.com/KhronosGroup/3DC-Asset-Creation ,
  https://github.com/mlimper/3DC-Asset-Creation/blob/main/asset-creation-guidelines/RealtimeAssetCreationGuidelines.md ,
  https://registry.khronos.org/3DCommerce/AssetCreation
- Arm, *Geometry best practices for Unreal Engine* (102695, issue 01, 2021):
  https://documentation-service.arm.com/static/615efb57e4f35d2484679d98
- Android developers, *Optimize geometry*: https://developer.android.com/games/optimize/geometry
- Unity manual, *Creating models for optimal performance*: https://docs.unity3d.com/Manual/ModelingOptimizedCharacters.html ;
  *Preparing your model files for export*: https://docs.unity3d.com/Manual/models-preparing.html
- Unreal Engine 5: *FBX Static Mesh Pipeline*, *FBX import options reference*, *Creating and using LODs*, *Static
  Mesh automatic LOD generation*: https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine ,
  https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine ,
  https://dev.epicgames.com/documentation/en-us/unreal-engine/static-mesh-automatic-lod-generation-in-unreal-engine
- Blender 5.2 manual: normals and sharp edges, Smooth by Angle, Weighted Normal, Bevel (Harden Normals), glTF 2.0
  add-on: https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html ,
  https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html ,
  https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html
- Retopology and baking: Blender manual *Remeshing / Retopology*
  (https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html), *Shrinkwrap*, *Data Transfer*
  (https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/data_transfer.html), *Cycles Baking*
  (https://docs.blender.org/manual/en/latest/render/cycles/baking.html); QuadriFlow (https://github.com/hjwdzh/QuadriFlow);
  Instant Meshes (https://github.com/wjakob/instant-meshes); Exoside *QuadRemesher 1.3 user documentation*
  (https://www.exoside.com/quadremesherdata/QuadRemesher_1.3_UserDoc.pdf); Marmoset *Toolbag baking tutorial*
  (https://marmoset.co/posts/toolbag-baking-tutorial/); Unity *Preparing humanoid characters*
  (https://docs.unity3d.com/Manual/UsingHumanoidChars.html); Unreal *FBX Skeletal Mesh Pipeline*.
- Not reachable on 2026-10-13: Polycount wiki (*Face weighted normals*, *Normal map*, *Topology*, *Limb topology*);
  Arm's HTML documentation portal and Maxon's ZBrush help (JavaScript-only pages); Adobe Substance baking pages
  (HTTP 403). No reachable source gave numeric loop counts for joints, so those are judged by the deformation gates.

> **Current objective update:** runtime 3D. Follow `RUNTIME_3D_PLAN.md`; the 199K version
> mentioned below is an intermediate. No new Meshy remesh operation is currently requested.

> **Superseded after review:** the returned remesh lost essential facial and armor geometry.
> Do not texture or rig remesh 01. A locally reduced 199,268-triangle billboard candidate is in
> `reduction_200k/`; ear cleanup, body/plate UVs and rig validation remain. See its README.

# Step 2 — remesh the locally repaired source

## Upload this file

`repaired_master/mm6_goblin_repaired_master.glb`

Use **Upload** at the top right of Meshy's asset list (visible in screenshots 2028/2029).
Import it as a 3D model. Select that imported asset, not either original generated goblin.
The source has the first candidate's body, corrected rear skull/teeth and two added upper-back plates.

## Remesh

1. Open **Remesh** on the imported model.
2. **Target Polycount → Fixed**.
3. **Topology → Quad**.
4. Enter **5,000** as the first polygon/face-count trial. This is an approximate 10K-triangle body experiment
   if the field counts quad faces; actual exported counts must be measured. It is not a proven final budget.
5. Check the displayed cost and run **one** remesh. Preserve the repaired dense master.
6. Download the remeshed **GLB** and send its path. Also export **FBX if available** to preserve editable quad
   topology; GLB triangulates surfaces. A screenshot of the resulting topology/face count is useful.

Keep this as an untextured topology candidate. Before any texturing or rigging, I will compare the returned mesh
with the dense master at 128/256/512-pixel review sizes, inspect face/finger/ear/armor preservation and joint regions,
and finish the left-ear jewelry cleanup on the editable mesh. We will raise the count if visible shape or deformation
requires it. The separate sword gets its own geometry budget; the approximately 10K guide target remains provisional.

## Known limits

The high mesh is a shape source, not production accepted. It has no rig or textures. Small extra jewelry on the left
ear is still present; removing the fused jewelry directly from the dense master damaged the ear in an experiment,
so that edit was rejected and the original intact ear restored. Hands require rig/grip work later. Back plates/rivets
are separate closed objects intersecting the body slightly; verify the remesh retains their silhouette and placement.

Meshy's external-model post-processing and Remesh workflow are documented here (checked 2026-09-23):

- https://docs.meshy.ai/en/webapp/guides/platform/asset-management
- https://docs.meshy.ai/en/webapp/guides/3d-model/remesh

The earlier screenshot 2020 shows the Fixed/Adaptive and Quad/Triangle controls. The live form's count unit and
returned measured triangles take precedence over the approximate quad conversion. Free generation retries do not
establish that remesh is free; read the operation's actual quote.

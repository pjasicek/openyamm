# Step 1 — generate the MM6 Goblin source mesh

**Current input:** baseline MM6 Goblin, BGoblin A / 550, unarmed relaxed A-pose.
**Expected result:** one source body master suitable for inspecting likeness and anatomy. It is not yet rigged or
production accepted. No Meshy generation has been submitted by the agent.

## Upload

Extract `mm6_goblin_step01_upload.zip`. Upload these four separate PNGs, not the review contact sheet:

| Meshy slot | File | What it shows |
| --- | --- | --- |
| Main | front.png | Front; pouch and earrings on viewer left |
| Left | left.png | Anatomical left; nose points left; no near-side pouch/earrings |
| Back | back.png | Back; pouch and earrings on viewer right |
| Right | right.png | Anatomical right; nose points right; near-side pouch/earrings |

The same files are in `references/`. All are 1024×1536 and retain the same approximate physical scale.

## Meshy settings and operation

1. Open **3D Model → Image to 3D**.
2. Select **Standard / High Detail**, using the available Meshy 7 family model that supports Multi-View.
   This means the ordinary detailed generation route, distinct from Smart Topology.
3. Turn **Multi-View ON** and fill Main, Left, Back, Right as above.
4. **Image Enhancement OFF**: preserve the reviewed reference design.
5. Use **ordinary geometry resolution**; leave **Ultra OFF** for this first experiment.
6. Preserve the shown **A-pose**. If the interface requires a Pose choice, use A-Pose and check its preview;
   do not choose a combat pose or force the head down.
7. If Texture is independently optional, leave it **OFF** for the shape check. Otherwise retain the included textures.
   Keep Split off for this initial multi-view body candidate. The sword is absent deliberately.
8. Check the live credit quote, then generate **one** candidate. Record the displayed model/version, settings and job ID.
9. Inspect front, both sides, back, above and below. Download the original source **GLB** before further processing.

There may be no general text field in this panel. The images supply the design; do not spend on a separate Text-to-3D
job. `prompts/meshy_optional.txt` is only for a descriptive field if the actual interface offers one.

## Inspect and return

Return the downloaded GLB and a screenshot of the settings/job page (or list the settings and job ID).
Include texture files if supplied separately. Use the actual exported format if GLB is unavailable.

Check face/ears/rear skull, lean body, complete open hands/thumbs, separated legs and correct right-side equipment.
Watch for fingers fused together, bracers fused across wrists, shoulder armor closing the armpits, a downward head,
or a torso replaced with full armor. Neutral/clay viewing helps reveal geometry problems.

## What happens next

I inspect the actual mesh and compare it with these references. Once the master passes the shape check, the next
operation is Remesh. The guide's first experiment is about **10,000 final triangles including equipment**, roughly
5,000 quads only if that is the unit the live control actually counts. We will reserve room for the sword and measure
rather than assume the exported count. Preserve the dense master for comparison and potential billboard rendering;
raise the working count if silhouette or bending tests justify it. Rigging follows topology and material preparation.

## Verified documentation

Checked 2026-09-23:

- [Meshy Image to 3D](https://docs.meshy.ai/en/webapp/image-to-3d): Standard, enhancement and pose controls.
- [Meshy Multi-View](https://help.meshy.ai/en/articles/12634481-how-to-use-multi-view): main plus three additional images;
  Multi-View and Smart Topology cannot currently be enabled together; use Remesh afterward.

Exact labels can differ between accounts/releases. Use the screenshot of the live controls to resolve discrepancies.
No fixed credit price is promised here.

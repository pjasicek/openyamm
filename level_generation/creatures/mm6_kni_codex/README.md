# MM6 KnightPlate — Codex batch

**Review round 3:** body **8,403 / 5,172 / 2,110 / 697 triangles**; accepted sword unchanged at
**1,985 / 1,131 / 451 / 180**. Combined LOD0 **13,085 -> 10,388 (-20.61% this round)**.
Body LOD0 saves 24.30% versus round 2 and 34.43% versus the unreduced accepted body.

Start with [HANDOFF round 3](HANDOFF.md#review-round-3), the [comparison gallery](review/round3/README.md),
[reduction curve](review/round3/reduction_curve.png) and [gate summary](review/round3/gate_summary.json).

All eight silhouettes pass IoU .99. LOD0–2 use the permitted perceptual alternative (SSIM .940/.896/.917);
LOD3 passes SSIM .972. Exact scores and the agent's visual judgment are recorded, not called new user acceptance.
Two strict baseline findings remain: accepted Attack elbow-plane deviation and coarse LOD3 G4 p99 2.89x.
No new rig failure was accepted. Skeleton, clips, tiers, props and integration/actors.yml remain exact.

## Unattended decisions

- Reduce in ~10% steps with protected face/helmet, fingers/hands, deformation loops, outline and contact regions.
  Stop LOD0 at 8,403: the next 7,564 step fails silhouette; a ~6.1k alternative lost internal armour form.
- Reproject base colour, region mask, engine-packed MR and tangent detail from the accepted unreduced mesh onto
  the accepted atlas layout. Preserve skin weights and all original animation/skeleton arrays in packaging.
- Compare lower LODs to their own accepted unreduced LOD at switch/hysteresis size (~485/195/78 px actor),
  continuing round 2's reference method. Retain round-2 LOD3 geometry when another cut worsens its baseline G4.
- Keep shared base/mask/MR and exact tier ramps. Use normal-only LOD maps shared across tiers to preserve steel
  highlights; LOD3 uses its accepted normal filtered to 256. This adds 5.25 MiB RGBA8 before mips (~7 MiB with mips);
  the body GLB grows to 11,373,020 bytes. Triangle reduction is not a texture-memory or measured runtime-speed saving.
- The closed helmet originally has no separate head atlas; retain that layout and its 1K primary maps.
- Preserve the accepted 1,985-triangle sword byte-for-byte and all bindings/impact timing. Do not repair the
  pre-existing Attack finding because the user explicitly requires unchanged clips.

## Selected files

| File | Purpose |
|---|---|
| export/mm6_kni.glb | Reduced/rebaked body; 58 joints, eight clips, three variants, four colour/shadow LODs |
| export/mm6_kni_sword.glb | Byte-identical accepted round-2 sword |
| integration/actors.yml | Unchanged descriptor, socket, event and scale bindings |
| work/round3/rebaked_l*.blend | Selected body geometry sources |
| textures/round3/ | Shared body maps and lower-LOD normals |
| review/round3/ | Native-size comparisons, measurements, rig gates, hashes and captures |
| references_hd/sword_round1/ | Accepted standalone sword design, prompt and provenance |

All clips/LODs checked at 48 Hz. Body/head/cloth/blade/hand-furniture penetration is zero; maximum hidden
grip/cuff contact .359136 mm is below 2 mm. Palm matrices and blade timing are preserved.
[Bindings](review/round3/check_bindings.txt): no BAD. [Viewer](review/round3/viewer_check.json): 24/24, no errors.
[Export audit](review/round3/export_validation.json) proves skeleton/clip/ramp/prop/binding invariance.
Current [front](review/clips_front.jpg), [side](review/clips_side.jpg) and
[three-quarter](review/clips_three_quarter.jpg) sheets cover all eight roles.

To open the [interactive viewer](review/viewer/index.html), serve the project parent directory:

```sh
python3 -m http.server 8915 --bind 127.0.0.1 --directory /home/pjasicek/github/OpenYAMM/level_generation/creatures
```

Open http://127.0.0.1:8915/mm6_kni_codex/review/viewer/.
Browser review GLBs bake tier colours; only export/ files are runtime candidates.

## Ownership and next step

Identity mm6:kni, owner codex-batch-kni. **30/100 credits spent, zero round 3, 70 remaining.**
Lease released and local server/Blender/browser stopped at handoff. No commit, game launch/build,
runtime install, shared edit or sprite-project write. The orchestrator should replace **only the body**
relative to installed round 2 and perform native validation. Actor descriptors need no change.

Historical [round 2](HANDOFF.md#review-round-2), [round 1](HANDOFF.md#review-round-1),
[weapon design](review/round1/sword_design.png), [weapon close-up](review/round1/sword_closeup.png).

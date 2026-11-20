"""Publish round-3 evidence and handoff without changing runtime bindings or accepted clips."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
read=lambda n:json.loads((R/n).read_text())
dump=lambda n,x:(R/n).write_text(json.dumps(x,indent=2)+'\n')
visual=read('visual_metrics.json');audit=read('export_validation.json');body=read('body_gate_summary.json')
counts=[8403,5172,2110,697];before=[11100,5980,2314,697];original=[12815,6467,2314,754];sword=[1985,1131,451,180]
stats=[{'lod':lod,'body_before':before[lod],'body_after':counts[lod],'body_original':original[lod],'sword_unchanged':sword[lod],'combined_before':before[lod]+sword[lod],'combined_after':counts[lod]+sword[lod],'min_iou':min(v['min_iou']for v in visual if v['lod']==lod),'min_ssim':min(v['min_ssim']for v in visual if v['lod']==lod)}for lod in range(4)]
contact=[]
for lod in range(4):
 row={'lod':lod}
 for tag in ['sword','blade_only','hand_furniture']:row[tag+'_max_mm']=max(v['depth_m']*1000 for v in read(f'g6_{tag}_l{lod}.json').values())
 contact.append(row)
assert max(x['blade_only_max_mm']for x in contact)==0
assert max(x['hand_furniture_max_mm']for x in contact)==0
assert max(x['sword_max_mm']for x in contact)<2
assert all(x['min_iou']>=.99 for x in stats)
assert read('anatomy.json')['baseline_identical']
assert read('viewer_check.json')['switched']==24 and not read('viewer_check.json')['failed']
assert audit['actors_yml']['changed'] is False and audit['mm6_kni_sword']['byte_identical_to_round2']
visual_review={'criterion':'IoU >= 0.99 in all eight views; SSIM >= 0.95 OR side-by-side perceptual review at native actor size','reviewer':'Codex agent, not new user acceptance','selected':True,'numeric_ssim_all_lods_pass':False,'perceptual_alternative_lods':[0,1,2],'observation':'Accepted silhouette, face/helmet, hand shape, armour ornaments, colour tiers and overall material appearance retained. Local steel-highlight and fine-texture pixel differences remain under close scrutiny; no material change to the creature look at the stated display sizes. This is a visual judgment, not pixel equality or a blind perception study.','rejected':'6.1k outline-preserving body lost internal armour form. LOD3 projected normal visibly altered distant highlights; retained accepted source normal filtered to 256 px instead.','renders':'comparison_l{lod}_{tier}.jpg; native-size individual PNG pairs comparison_l{lod}_{tier}_{view}.png','sizes_actor_height_px':[[min(v['reference_actor_pixel_heights']),max(v['reference_actor_pixel_heights'])]for v in visual if v['tier']=='a']}
dump('visual_review.json',visual_review)
gate={'technical_complete':False,'authorized_reduction_work_complete':True,'no_new_rig_regressions':True,'visual':visual_review,'counts_and_metrics':stats,'body':body,'contact':contact,'palms':read('palms.json'),'blade':read('blade_gate.json')['impact'],'motion_trace_flags':sum(len(x['flags'])for x in read('g6_trace.json').values()),'elbow_baseline_identical':True,'absolute_baseline_findings':['Attack elbow plane deviation 13.734583 degrees left / 26.146133 right; 8/73 and 30/73 samples exceed 5 degrees. All accepted clip samples retained exactly.','LOD3 G4 p99 2.89x / maximum 3.11x, unchanged from accepted baseline. Candidate 678 triangles raised p99 to 2.90 and was rolled back.'],'bindings':'PASS no BAD line','viewer':'PASS 24/24 switches; zero console errors','normal_map_tradeoff':{'additional_rgba8_MiB_before_mips':5.25,'additional_rgba8_MiB_with_full_mips_approx':7,'body_glb_before_bytes':10008296,'body_glb_after_bytes':audit['mm6_kni']['bytes']}}
dump('gate_summary.json',gate)
table='| LOD | Body round 1 | Body round 2 | Body now | Sword unchanged | Combined now | Min IoU | Min SSIM |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for x in stats:table+=f'| {x["lod"]} | {x["body_original"]:,} | {x["body_before"]:,} | {x["body_after"]:,} | {x["sword_unchanged"]:,} | {x["combined_after"]:,} | {x["min_iou"]:.6f} | {x["min_ssim"]:.6f} |\n'
gallery='| LOD | Blue-violet A | Rust B | Pale-gold C |\n|---|---|---|---|\n'
for lod in range(4):gallery+=f'| {lod} | [Eight views](comparison_l{lod}_a.jpg) | [Eight views](comparison_l{lod}_b.jpg) | [Eight views](comparison_l{lod}_c.jpg) |\n'
method="""# Round 3: silhouette reduction and rebake

The selected body has **8,403 / 5,172 / 2,110 / 697 triangles**. The accepted round-2 sword is byte-identical.
IoU passes in every view. LOD0–2 use the revised rule's **perceptual alternative**, not a numerical SSIM pass.
The full absolute rig checklist retains two accepted baseline findings; no new rig regression was accepted.

"""
method+=table+'\n'+gallery+"""
Individual PNG pairs preserve native pixel size; open at 100%, not fit-to-window or zoomed.
The JPG sheets arrange all eight native-size pairs for convenient browsing.
The raw high/low RGBA renders and [per-view CSV](visual_metrics.csv) are retained.
[Visual review](visual_review.json) records the agent judgment and its limits.

## Measurement and reference

LOD0 uses a ~700 px actor (698–705 px across azimuths). LOD1–3 use runtime switch/hysteresis projected body
diagonals 550/220/88 px, giving actor heights 483–487 / 194–196 / 78–79 px.
Eight azimuths at 45-degree intervals, the same slightly elevated orthographic camera and Standing at time zero.
Each LOD is compared with its **matching accepted unreduced round-1 LOD**. This continues the round-2 reference
method; it is not a claim that all coarse LODs equal full LOD0. No switch distance or actor descriptor changed.

Final PBR comparisons use Cycles CPU, four threads, 16 samples, seed 1729, denoising, fixed broad studio lights
and Standard colour management. Both sides use the accepted engine tier ramps, MR red specular/green roughness,
and their respective tangent normals. This is an offline material approximation, not native bgfx evidence.
The sword is omitted from these body-only comparisons because its entire exported file is unchanged.

Silhouette IoU thresholds alpha at 128. RGB SSIM uses a foreground union crop, Gaussian sigma 1.5, five-pixel
mask dilation, the same grey composite, and no empty-background dilution. Exact implementation:
[reduction_metrics_round2.py](../../scripts/reduction_metrics_round2.py).
Workbench silhouette sweeps use 16-sample AA. Small differences from final Cycles IoU are rasterization differences.

## Reduction curve and stop decisions

[Plot](reduction_curve.png), [all candidates CSV](reduction_curve.csv), [JSON](reduction_curve.json),
[original silhouette sweep](silhouette_curve.json), [rebake probes](bake_candidate_probe.json),
[lower-LOD curve](lod_curve.json), [final lower-LOD selection](lod_selection.json).

Protect helmet/face, hands/fingers, shoulder/elbow/knee/hip deformation regions, outline and grip contact.
Weld duplicate seam positions, then protected dissolve/collapse in approximately 10% steps; retain skin weights
and the accepted chart layout. New texture pixels are projected onto that layout. No fixed 50% LOD ratios.

Balanced LOD0: 11,529 -> 10,376 -> 9,338 -> 8,404 -> 7,564 triangles. Minimum IoU at 8,404 is .990679;
the next step falls to .988316. One degenerate triangle is removed at export, yielding 8,403.
An aggressive outline-only alternative reached about 6.1k and retained the outline, but lost internal armour
shape and failed visual review after baking. More strongly locked joints/head also concentrated damage elsewhere.
These alternatives are retained as rejected evidence, not claimed production reductions.

LOD1 uses 5,172 after bracket refinement; 5,106 fails silhouette. LOD2 uses 2,110; the 10% 2,082-step fails
silhouette. LOD3's 678 candidate passed outline but increased G4 p99 from 2.89 to 2.90; restore accepted round-2
697 geometry. Its original normal map, filtered and renormalized to 256 px, also avoids the rejected projected
normal's visible shading error. LOD3 now passes numerical SSIM .972225.

The accepted round-2 sword is already 1,985 triangles and keeps bevels, fullers, guard, wrapped grip and pommel.
Round 2's 1,959 candidate failed silhouette. Round 3 explicitly protects the accepted prop: no further sword edits.

## Texture rebake and cost

[bake receipt](bake.json), [LOD1 normal](normal_bake_l1.json), [LOD2 normal](normal_bake_l2.json),
[LOD3 source-normal selection](normal_lod3_selection.json).

Component-isolated selected-to-active Cycles projection prevents rays hitting neighbouring armour parts.
Cage extrusion .03 m, max ray .1 m, 16 px padding; OpenGL +Y tangent normals.
Base colour 2048, region mask/MR/main normal 1024. Base, region mask and MR remain shared across all LODs/tiers;
each tier still uses its exact accepted ramps. The closed helmet originally had no separate head material/atlas:
no artificial head set was introduced or downscaled. Existing 1K map resolution is retained.

**MR red is the engine specular mask, green roughness, blue metallic.** Preserve that packing; do not replace red
with conventional ORM occlusion. Region B/A remain inactive zero. PNG optimization is lossless with pixel assertions.

LOD1/2 have normal-only re-bakes at 1024/512. LOD3 retains the accepted source normal at 256 because its geometry
is unchanged from round 2. All these maps are shared by tiers. Reusing the LOD0 tangent bake at different topology
caused visible broad-highlight errors, hence the normal-only material clones. The runtime GLB has seven images
and twelve material records: three unchanged base materials plus normal-index-only clones for lower LODs.
This costs **5.25 MiB additional RGBA8 storage before mips (~7 MiB with full mip chains)**. It reduces geometry,
not texture memory: body GLB grows from 10,008,296 to 11,373,020 bytes. No runtime performance claim was measured.

## Animation and contact validation

All eight roles, four LODs, 48 Hz; 576 samples per body LOD. [Gate summary](gate_summary.json),
[body results](body_gate_summary.json), [palms](palms.json), [elbows](anatomy.json),
[accepted baseline elbows](anatomy_baseline.json), [posture](posture.json),
[blade impact](blade_gate.json), [motion trace](g6_trace.json).

Body/head/cloth penetration 0 mm; blade and guard/pommel-to-hand penetration 0 mm on all clips/LODs.
Current worst hidden grip/cuff overlap is **0.359136 mm** in Death at LOD0, below 2 mm (accepted baseline 1.717193 mm).
Palm frame delta is zero; grip anchor <.000415 mm. Trace flags zero. Impact remains .71875 s,
speed 31.451575 m/s, target dot .861332, signed edge +.654087 and edge share .661776.

G4 p99/max LOD0–3: 1.81/3.08, 1.91/3.36, 1.74/2.36, 2.89/3.11. G5 maxima:
2.722825 / 1.522875 / 1.310609 / 1.151729, all below 4.5.

**Absolute findings remain, not silent passes:** Attack elbow-plane deviations 13.735° left/26.146° right
(8/73 and 30/73 samples >5°) match the accepted baseline exactly. Other roles pass. LOD3's baseline G4 p99 2.89
is above the approximate 2x guideline. The explicit instruction to preserve clips prevents correcting Attack here.
Technical-complete remains false; authorized reduction work is complete with these findings disclosed.

[Bindings](check_bindings.txt): no BAD line. [Viewer check](viewer_check.json): 24/24 tier/clip switches,
zero browser errors. [Export validation](export_validation.json): exact skeleton, animations, inverse binds,
tier ramps, sword and actor descriptors; unit normals, finite data and normalized weights.
The final LOD3 texture correction does not change geometry or animation; sampled rig reports remain applicable,
and export/bindings were rechecked after packaging it.

## Reproduction and review assets

Selected Blender sources: work/round3/rebaked_l0.blend through rebaked_l3.blend.
Source snapshots and experimental candidates remain in work/round3. The accepted production masters are untouched.

Scripts, in dependency order: silhouette_round3.py; bake_round3.py and bake_components_round3.py;
tier_maps_round3.py; lower-LOD selection/restore; bake_lod_normals_round3.py; preserve_lod3_normal_round3.py;
package_round3.py; finish_round3.py; verify_round3.py; compose_round3.py.
Use the repository workspace lease guard and run_creature_blender.sh wrapper with --threads 4.
finish_round3.py repeats packaging, final PBR renders and all rig/contact/clip checks from the selected data.
The final reports and [hash inventory](files.json) identify the exact delivered files.

Updated [front](../clips_front.jpg), [side](../clips_side.jpg), [three-quarter](../clips_three_quarter.jpg) sheets;
[Standing hands](hands_Standing.jpg), [Attack hands](hands_Attack.jpg), [Death hands](hands_Death.jpg);
viewer captures [A](viewer_a.png), [B](viewer_b.png), [C](viewer_c.png).
The agent inspected the comparisons, clip/hand sheets and viewer captures. This is not new user artistic approval.
Native installation, captures and game regression remain assigned to the batch orchestrator.
"""
(R/'README.md').write_text(method)
files_table='| File | Bytes | SHA-256 |\n|---|---:|---|\n'
for key in ['mm6_kni','mm6_kni_sword','viewer_a','viewer_b','viewer_c']:
 x=audit[key];files_table+=f'| `{x["file"]}` | {x["bytes"]:,} | `{x["sha256"]}` |\n'
files_table+=f'| `integration/actors.yml` (unchanged) | 2,383 | `{audit["actors_yml"]["sha256"]}` |\n'
handoff="""# MM6 KnightPlate handoff

**Review round 3 exported, 2026-10-12.** Body LOD0 **11,100 -> 8,403 triangles (-24.30% this round;
-34.43% from the accepted unreduced 12,815)**. Sword remains exactly 1,985 triangles.
Combined LOD0 is **13,085 -> 10,388 (-20.61%)**. Skeleton, clips, tier ramps, props and bindings are preserved.

**The full absolute checklist is not all-pass:** LOD0–2 use the allowed perceptual SSIM alternative, and the
accepted Attack elbow-plane/LOD3 G4 findings remain. Exact scores, visual judgment and baseline evidence are below.
Authorized reduction work is complete; this is not a claim of new user artistic acceptance.

## Review round 3

Only body/colour-shadow geometry, rebaked body maps, lower-LOD normal materials and review assets changed.
**Replace only `export/mm6_kni.glb`** relative to the orchestrator's installed round 2.
The sword and **integration/actors.yml are byte-identical**. No descriptor, attachment, launch, grip or timing edit
is required. All 58 joints, inverse binds and eight original clip arrays remain exact.
Existing `cast: Attack` aliases and Sword/SwordTip nodes are preserved.

Meshy **30/100 credits total, zero this round, 70 remaining**. No commits, game launches/builds,
runtime installs, shared-source changes or writes to the sprite-restore project. Lease released at handoff.

### Triangle reduction (rebake)

"""
handoff+=table+"""
Body shadow LODs have the same triangle counts as colour LODs. Combined counts are
**10,388 / 6,303 / 2,561 / 877**, previously **13,085 / 7,111 / 2,765 / 877**. No shield.

Protected ~10% reduction sweeps preserve helmet/face, hands/fingers, deformation regions, silhouette and grip.
The next 7,564-triangle LOD0 step fails IoU .988316. An outline-preserving ~6.1k attempt lost interior armour form
after rebaking and was rejected. Lower LODs were measured at switch sizes, not fixed half-count ratios.
LOD3 stays at its round-2 697 because the 678 candidate worsened an existing G4 finding.

LOD0 is judged at ~700 px actor height. LOD1–3 are ~485/195/78 px. Each lower LOD uses its own accepted unreduced
round-1 mesh as reference, preserving the existing distant appearance; this is not comparison of every coarse LOD
against full LOD0. All three tiers/eight views are measured.

**Numerical SSIM does not pass .95 for LOD0–2** (minima .940053/.896411/.916842).
The agent selected them under the rule's side-by-side perceptual alternative: silhouette, ornaments, tier identity
and overall armour appearance remain intact at the intended sizes. Small local highlight/texture differences
remain under close scrutiny. This judgment is explicitly recorded, not represented as pixel equality.
LOD3 passes .972225 after rejecting a visibly wrong projected normal and retaining its accepted normal detail.

- [Side-by-side gallery and full method](review/round3/README.md), including every tier/LOD/eight-view sheet.
- LOD0 [A](review/round3/comparison_l0_a.jpg), [B](review/round3/comparison_l0_b.jpg),
  [C](review/round3/comparison_l0_c.jpg); [native-size front pair](review/round3/comparison_l0_a_0.png).
- [Reduction plot](review/round3/reduction_curve.png), [curve CSV](review/round3/reduction_curve.csv),
  [per-view IoU/SSIM](review/round3/visual_metrics.csv), [visual assessment](review/round3/visual_review.json).
- Updated clips: [front](review/clips_front.jpg), [side](review/clips_side.jpg),
  [three-quarter](review/clips_three_quarter.jpg); hands [Standing](review/round3/hands_Standing.jpg),
  [Attack](review/round3/hands_Attack.jpg), [Death](review/round3/hands_Death.jpg).
- Viewer captures [A](review/round3/viewer_a.png), [B](review/round3/viewer_b.png), [C](review/round3/viewer_c.png).

### Rebake and material tradeoff

The accepted unreduced mesh supplies component-isolated base colour, region mask, MR and tangent normal detail.
The accepted UV chart layout is retained, with new pixels projected onto it. Base is 2K; mask/MR/main normal 1K.
MR keeps the engine's red specular/green roughness/blue metallic packing. No occlusion data overwrites specular red.
The original closed helmet had no separate head set; no new head atlas or resolution reduction was introduced.

All texture sets remain shared by the three tiers, using their unchanged ramps. Base/mask/MR also remain shared
across LODs. Normal-only maps at 1K/512/256 serve lower LODs; LOD1/2 are rebaked and unchanged LOD3 uses the accepted
normal filtered/renormalized to 256. Reusing LOD0's normal on different tangent frames visibly shifted highlights.
Nine lower-LOD material clones change only normal index/name. Seven images, twelve materials total.

**Cost:** additional normal storage is 5.25 MiB RGBA8 before mips (~7 MiB with full mip chains).
The body GLB grows from 10,008,296 to **11,373,020 bytes**. This optimizes triangles, not texture memory.
No runtime GPU speed or memory benchmark is claimed. [Bake receipts and details](review/round3/README.md#texture-rebake-and-cost).

### Gates and immutable baseline findings

All eight clips/four LODs checked at 48 Hz, 576 samples per body LOD. Body/head/cloth, actual blade and
hand-furniture penetration: **0 mm**. Maximum hidden grip/cuff overlap **.359136 mm**, below 2 mm.
Both palm matrices remain exact, grip anchor <.000415 mm, motion trace flags zero.
Blow is unchanged: .71875 s, 31.451575 m/s, target dot .861332, signed edge +.654087, edge share .661776.

G4 p99/max by LOD: **1.81/3.08, 1.91/3.36, 1.74/2.36, 2.89/3.11**.
G5 maximum **2.722825 / 1.522875 / 1.310609 / 1.151729**, all below 4.5.
Two absolute findings remain exactly as accepted: Attack elbow-plane deviation **13.735° L / 26.146° R**
(8/73 L and 30/73 R samples >5°), and coarse LOD3 G4 p99 **2.89x**, above the approximate 2x guideline.
The baseline elbow report is identical. Correcting it would violate the explicit keep-clips instruction.
No new rig failure was accepted; technical-complete remains false with authorized reduction work complete.

[Gate summary](review/round3/gate_summary.json), [body](review/round3/body_gate_summary.json),
[elbows](review/round3/anatomy.json), [baseline](review/round3/anatomy_baseline.json),
[palms](review/round3/palms.json), [blade](review/round3/blade_gate.json).
[check_bindings.py](review/round3/check_bindings.txt): **no BAD line**.
[Viewer check](review/round3/viewer_check.json): **24/24**, no browser errors.
[Export audit](review/round3/export_validation.json): exact nodes/clip arrays/inverse binds/ramps, finite data,
unit normals and worst weight sum error **1.192093e-7**. Sword and actors unchanged.

### Changed files and hashes

"""
handoff+=files_table+"""
[Complete artifact hashes](review/round3/files.json) cover maps, scripts, review evidence, documents and selected
Blender sources. Editable body: `work/round3/rebaked_l0.blend` through `rebaked_l3.blend`.
Accepted original masters and round-start snapshots remain preserved. New maps: `textures/round3/knight_*.png`.
[Measurement README](review/round3/README.md#reproduction-and-review-assets) lists the reproduction scripts.

Orchestrator next: review the disclosed visual/material tradeoff and immutable findings, integrate the body export,
then perform native material/contact/distance and regression checks. No assets_dev copy was made here.
Blender used one process with --threads 4; temporary HTTP server and review browser are stopped at handoff.

---

The following round-2/round-1 sections are historical. Their counts, hashes and integration instructions
are superseded by round 3 above.

"""
old=(P/'work/round3/baseline_HANDOFF.md').read_text()
handoff+=old[old.index('## Review round 2'):]
(P/'HANDOFF.md').write_text(handoff)
readme="""# MM6 KnightPlate — Codex batch

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
"""
(P/'README.md').write_text(readme)
progress=json.loads((P/'creature_3d_progress.json').read_text())
progress['gates_round_2']=json.loads((P/'work/round3/baseline_creature_3d_progress.json').read_text())['gates'];progress['stage']='complete_authorized_review_round_3';progress['substep']='handoff_with_baseline_findings'
progress['technical_complete']=False;progress['round_3_authorized_work_complete']=True
progress['artistic_acceptance']='Creature and sword accepted before round 3; reduction selected by agent under perceptual alternative, pending orchestrator native review.'
progress['completed_at']=datetime.now(timezone.utc).isoformat()
progress['budget_summary']['round_3_spent']=0
progress['selected_exports']=[{'path':audit[k]['file'],'sha256':audit[k]['sha256'],'bytes':audit[k]['bytes']}for k in ['mm6_kni','mm6_kni_sword']]
progress['integration_status']='round3_body_only_staged_for_orchestrator; sword and actors unchanged'
progress['next_action']={'owner':'batch_orchestrator','action':'Review HANDOFF round 3, perceptual SSIM alternative, added normal-map storage and unchanged baseline rig findings; integrate only the body, then native material/contact/LOD and regression checks. actors.yml unchanged.'}
progress['gates']={'summary':'review/round3/gate_summary.json','visual':'IoU pass all; LOD0-2 perceptual alternative, LOD3 numeric SSIM pass','geometry_contact':'pass all clips/LODs','bindings':'pass no BAD','viewer':'pass 24/24','elbow_absolute':'accepted baseline failure unchanged','G4':'LOD0-2 pass; LOD3 accepted p99 2.89 unchanged','G5':'pass all LODs','palms':'exact accepted frames and passing grip anchor'}
progress['known_limits']=['Lower LODs compared to matching accepted unreduced LOD, not full LOD0.','SSIM minima LOD0-2 below .95; agent visual alternative used, with local highlight/texture differences disclosed.','Extra LOD normal maps add 5.25 MiB RGBA8 before mips; body file grows to 11373020 bytes.','Native material/contact/LOD checks and installation remain orchestrator-owned.','Procedural runtime head look remains outside clip-only contact tests.']
progress['technical_notes']=['Review round 3 reduces body geometry and rebakes shared textures. Skeleton, inverse binds, animation arrays, tier ramps, accepted sword and actors.yml are exact.','Body colour/shadow triangles 8403/5172/2110/697; sword 1985/1131/451/180.','LOD0-2 use the explicit perceptual SSIM alternative. Baseline Attack elbow/LOD3 G4 findings remain disclosed; no new rig failure.','Normal-only LOD maps add 5.25 MiB RGBA8 before mips; no runtime performance claim.','No install/build/game/regression/commit under batch override.']
progress['review_round_3']={'counts':stats,'visual_report':'review/round3/visual_review.json','gates':'review/round3/gate_summary.json','handoff':'HANDOFF.md#review-round-3','actors_changed':False,'sword_changed':False,'credits_spent':0,'technical_complete':False,'authorized_work_complete':True}
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('Round 3 report, README, handoff and progress updated.')

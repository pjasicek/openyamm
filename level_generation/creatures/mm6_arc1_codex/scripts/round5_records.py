"""Record final R5 delivery and retain the unaltered shared-gate verdict."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round5'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read(P/'review/delivery_validation.json');g=read(R/'shared_final/gates.json');c=read(R/'shared_comparison.json');n=read(R/'native_pose.json');tex=read(R/'texture_sets.json');ssim=read(R/'texture_comparison/metrics.json');dist=read(R/'reduction/assembled_distance_metrics.json')
near=[x for x in g['gates']if x['lod'].endswith('colour0')]
def maximum(gate,rows):return max(x['worst']for x in rows if x['gate']==gate and x['worst']is not None)
feet=[x for x in g['gates']if '/colour'in x['lod']and x['clip']in ['Attack','Cast']]
m={'shooting_heel_toe_mm':maximum('rest_sole_height_mm',feet),'shooting_sole_tilt_deg':maximum('rest_sole_tilt_deg',feet),'near_grip_gap_mm':maximum('grip_gap_mm',near),'near_grip_penetration_mm':maximum('grip_penetration_mm',near),'bow_body_penetration_mm':maximum('prop_body_penetration_mm',[x for x in g['gates']if x['region']=='bow'])}
assert m['shooting_heel_toe_mm']<=10 and m['shooting_sole_tilt_deg']<=3 and m['near_grip_gap_mm']<=3 and m['near_grip_penetration_mm']<=3 and m['bow_body_penetration_mm']==0
(R/'selected_measurements.json').write_text(json.dumps(m,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);im=Image.new('RGB',(1600,980),'#34373c');draw=ImageDraw.Draw(im)
draw.text((20,15),f'Textures: 89.547 -> 53.125 MiB; minimum eight-view SSIM {ssim["min_ssim"]:.5f}',font=font,fill='white')
for j,angle in enumerate([0,2,4,6]):
 for k,label in enumerate(['original','compact']):
  x=(j%2)*800+k*400;y=55+(j//2)*460;pic=Image.open(R/f'texture_comparison/{label}_{angle}.png').convert('RGBA');pic.thumbnail((390,420));im.paste(pic,(x,y+28),pic);draw.text((x+8,y),f'View {angle}: '+label,font=font,fill='white')
im.save(R/'texture_comparison/comparison.jpg',quality=94)
files=v['files'];runtime=[k for k in files if k.startswith('export/')]
table='\n'.join(f"| [{Path(k).name}]({k}) | {' / '.join(map(str,list(files[k]['triangles'].values())[:4]))} | {files[k]['bytes']} | {files[k]['sha256']} |"for k in runtime)
oldbytes=sum((R/'baseline'/k).stat().st_size for k in runtime);newbytes=sum(files[k]['bytes']for k in runtime)
mem=sum(a['images_after']*a['dimensions_after'][0]*a['dimensions_after'][1]*4 for a in tex['assets'].values())/1048576;assert mem<=53.5
texturetable='\n'.join(f"| {name} | {a['images_after']} | {' x '.join(map(str,a['dimensions_after']))} | {a['texel_density_scale']} |"for name,a in tex['assets'].items())
faults='\n'.join(f'| {k} | {z} |'for k,z in c['failure_categories'].items())
audit=f'''# Review round 5 — shared audit

**{g['status']}**, {g['counts']}. R4 comparison: {len(c['new_failures'])} newly failing rows, {len(c['resolved_failures'])} resolved rows. Skeleton evidence repeats across LODs.

| Gate | Failing rows |
|---|---:|
{faults}

[Exact rows, limits and times](shared_final/gates.md) · [R4 comparison](shared_comparison.json).

Attack/Cast now belong to clips.rest to activate shared heel/toe and sole checks. That also evaluates rest free-palm and foot-yaw checks: new right-palm rows include the intentional drawing hand. Raw results are retained, not relabelled PASS. No threshold was relaxed.

All visible-LOD Attack/Cast soles pass. The left shadow3 sole remains 3.959 degrees against 3 (also inherited in Standing/Fidget). Near grip surfaces pass throughout; distant gaps and the inherited 68.056-degree palm cone remain. Other action anatomy, sleeves, drawn-arrow/body and head findings remain open.

Hit bow/body clearance is fixed. Left wrist roll 34.995 degrees, forearm 75.015, skin twist 89.206 and upper arm 46.907 pass. The forearm rolls axially while preserving the hand/bow frame; its skin-twist share is .4 inside Hit and .6 at the rest endpoints and elsewhere.

Closed-body intended-opening classification remains UNVERIFIED; distance silhouettes retain failures below .97. This is not all-gates technical acceptance.
'''
(R/'SHARED_AUDIT.md').write_text(audit)
native=(R/'native_measurements.md').read_text().split('\n\n')[0]
distance='\n'.join(f"| {x['lod']} | {x['clip']} | {x['pooled_iou']:.5f} | {x['pass']} |"for x in dist['rows'])
handoff=f'''# MM6 BArcher arc1 — batch handoff

## Review round 5

Carried bow corrected to the native bitmap: **front tip +18 degrees, azimuth 0, 72 degrees from vertical; string above/toward the arm, limbs below**. Wrist/grip forward offsets are 5.86% / 7.94% of body height. The closed fist stays beside the thigh in front projection. Standing bow-to-leg clearance: {n['round5']['bow_to_leg_clearance_m']*1000:.2f} mm.

Attack and its exact Cast copy use fixed flat ankle anchors, with pelvis height adjusted only where the source sway exceeds leg reach. Every visible LOD passes: heel/toe height <= {m['shooting_heel_toe_mm']:.3f} mm, sole tilt <= {m['shooting_sole_tilt_deg']:.3f} degrees, no floor penetration. Accepted Standing/Fidget feet and free arm remain.

**Technical acceptance remains pending: shared gates {g['status']}, {g['counts']}.** This delivers the scoped review correction with explicit open findings, not an all-gates PASS.

[Native comparison](review/round5/native_rest_comparison.jpg) · [Attack feet in viewer](review/round5/browser_attack_feet.png) · [Texture comparison](review/round5/texture_comparison/comparison.jpg) · [Shared audit](review/round5/SHARED_AUDIT.md) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).

### Files and integration

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{table}

All three runtime files changed. Every colour/shadow LOD retains R4 geometry, indices, normals and skin weights. UV/maps change for memory; body animation changes for carry/feet. Body shadows have the same counts as colour LODs. The 24-triangle moving string, 63 joints, eight clips, both bracers and all tier ramps remain.

**integration/actors.yml is unchanged**, SHA-256 {sha(P/'integration/actors.yml')}.
IDs 475/476/477 and scale/yaw/stride are unchanged. Cast exactly copies Attack under the distinct Cast name ({v['cast_exact_attack_copy']['channels']} channels). Events remain **1.200 s / Socket_Arrow_Release**, no palm_right.

Updated masters: work/rig_equipped.blend, rig_textured.blend, runtime_authoring.blend, and work/round2/lod0.blend through lod3.blend. Fitted masters retain source UV maps; runtime_authoring imports the final packed tier-A GLB. [Artifact hashes](review/round5/artifact_manifest.json) cover scripts, config, exports, viewer, sheets and masters. [Previous R4 handoff](review/round5/baseline/HANDOFF.md).

### Native measurements

{native}

Native visible landmarks have +/-2 px uncertainty; inferred hip +/-6 px at 256 px height. Azimuth is inferred from the end-on front view. Front-projection wrist mirror error is {n['round5']['mirrored_right_wrist_front_error_m']*1000:.2f} mm (lateral mismatch alone 3.81 mm). The 25-degree elbow bend places the fist slightly higher than the open free hand while attaining the forward target. Differences remain visible in the table.

Near grip across all clips: gap <= {m['near_grip_gap_mm']:.3f} mm; penetration <= {m['near_grip_penetration_mm']:.3f} mm. Bow/body penetration is zero throughout. Hit keeps the bow orientation steady while carrying outward; forearm axial rotation distributes strain without changing the held hand frame.

### Texture memory

| Asset | Shared images | Final dimensions per map | Linear density factor |
|---|---:|---|---:|
{texturetable}

**10 images before and after**, one shared set per asset across all LODs. RGBA8 base-level decoded memory: **89.546875 -> {mem:.6f} MiB**, below R3's 53.5 MiB. Full mip chains are approximately 4/3 of these figures. Total GLB bytes: **{oldbytes:,} -> {newbytes:,}**.

The explicit R5 memory cap takes priority over the older exact-density requirement. Tighter polygon packing alone could not fit full-density charts plus padding. Body maps use .75x linear resolution, bow .875x, arrow unchanged. Colour/normal/material maps use Lanczos; the region mask uses nearest sampling. Every map has **16 px dilated margins**, packed by conservative polygon occupancy on a four-pixel grid. UV triangle shape is preserved at the stated density. This is a documented density tradeoff.

Eight matched views at approximately 700 actor pixels: **minimum textured SSIM {ssim['min_ssim']:.5f} >= .95**, silhouette IoU 1.0. [Metrics](review/round5/texture_comparison/metrics.json) · [Packing](review/round5/texture_sets.json).

### Validation and retained faults

check_bindings.py **PASS, no BAD line**, including skin weights/materials. Viewer **24/24 switches, zero errors, eight captures**. All 71 read-only native hashes match. Exact Attack/Cast equality, rest boundaries, triangle caps and geometry preservation pass. Release direction remains 1.947 degrees from forward; socket/string timing is retained. [Delivery checks](review/delivery_validation.json).

Shared gates remain FAIL: distant grip gaps, inherited palm cone, action elbow/roll/cloth, drawn-arrow/head findings, and the farthest shadow sole remain. Intended body-opening classification is UNVERIFIED. Newly activated Attack/Cast rest-palm/yaw checks are preserved in the raw report. [Every gate](review/round5/shared_final/gates.md) · [R4 changes](review/round5/shared_comparison.json).

Triangle counts stay fixed as requested. The historical [near reduction curve](review/round2/reduction/curve.png) records body IoU .99461 / SSIM .96445; the next 8,555-triangle candidate failed at .9447 SSIM. Current equipped switch-size silhouettes:

| LOD | Clip | Pooled IoU | >= .97 |
|---|---|---:|---|
{distance}

[Distance sheet](review/round5/reduction/distance_sheet.jpg). No triangles were added to hide these failures.

### Reproduction and scope

Use the project lease and tools/run_creature_blender.sh, one background Blender with --threads 4. round5_motion.py authors and exports; snapshot the three runtime GLBs to work/round5/runtime_unpadded, then run round5_textures.py, round5_arrow_export.py and round5_viewer.py. round5_render.py runs gates and refreshes sheets/measurements. round5_final_audit.py refreshes the packed master and release/Hit evidence. Finish with round5_check_viewer.py, round5_validate.py, round5_sheets.py and round5_records.py. CPU Cycles avoids the host's Workbench crash.

Budget **40/100 credits, zero this round**. No game launch, build, installation, assets_dev/assets_source copy or commit. Installation/game checks belong to the orchestrator. Lease released at handoff.
'''
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text(f'''# MM6 BArcher arc1 — review round 5

Native bow carry corrected: string above, front tip +18 degrees, wrist/grip forward offsets 5.86% / 7.94% of height. Attack/Cast feet pass on every visible LOD. Memory: 53.125 MiB, ten shared images, 16 px margins. The documented density reduction passes the texture comparison at minimum SSIM {ssim['min_ssim']:.5f}.

**Shared gates remain FAIL; technical acceptance is pending.** [HANDOFF.md](HANDOFF.md) lists files, hashes, counts and remaining faults. actors.yml unchanged; budget 40/100 credits. Nothing installed or committed.

![Native versus round 5](review/round5/native_rest_comparison.jpg)

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) · [Shared audit](review/round5/SHARED_AUDIT.md) · [Texture comparison](review/round5/texture_comparison/comparison.jpg).
''')
now=datetime.datetime.now(datetime.timezone.utc).isoformat();progress=read(P/'creature_3d_progress.json')
progress.update(stage='review_round_5_handoff',status='needs_review',technical_completion='pending_shared_gate_findings',user_acceptance='review_round_5_pending',updated_at=now,next_action='Orchestrator reviews corrected carry/feet and remaining shared-gate and distance findings before installation.')
progress['selected_artifacts']={k:{'path':k,**z}for k,z in files.items()};progress['validation']={'report':'review/delivery_validation.json','status':g['status'],'shared_runner':v['shared_runner'],'viewer':'review/round5/check_viewer.log','viewer_switches':24,'skin_weights':'review/round5/check_bindings.log'}
progress['runtime']['installation']='round5_staged_with_open_shared_gate_findings';progress['stages']['animations_and_gates']='pending_shared_gate_findings'
progress['review_round_5']={'recorded_at':now,'credits_spent':0,'total_credits':40,'integration_actors_yml_changed':False,'shared_runner':v['shared_runner'],'changed_runtime_files':runtime,'measurements':m,'decoded_texture_mib':mem,'minimum_texture_ssim':ssim['min_ssim'],'handoff':'HANDOFF.md'}
progress['findings']=[{'id':'shared_runtime_gate_findings','status':'open','evidence':['review/round5/SHARED_AUDIT.md']},{'id':'distance_silhouette','status':'open','evidence':['review/round5/reduction/assembled_distance_metrics.json']},{'id':'density_tradeoff','status':'explicit_memory_cap_priority','evidence':['review/round5/texture_comparison/metrics.json']}]
progress['correction_ledger'].append({'finding':'Review round 5: native string/pitch, fist offset, shooting feet and memory','change':'Native upward bow/string, forward closed fist, flat shooting soles, compact shared maps','result':'Scoped visible checks pass; shared technical acceptance pending.'})
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
for path in [P/'source/ANIMATION_STUDY.md',P/'integration/playbook_notes.md']:
 path.write_text('## Review round 5\n\nNative side: forward tip +18 degrees, string ABOVE the limbs. Wrist/grip offsets 5.86%/7.94% of height. Shooting has fixed flat ankle anchors and reach-constrained pelvis. HANDOFF.md records memory tradeoff and unresolved gates.\n\n'+path.read_text())
paths=[P/k for k in files]+[P/'README.md',P/'HANDOFF.md',P/'gates.json',P/'integration/actors.yml',P/'source/ANIMATION_STUDY.md',P/'integration/playbook_notes.md',P/'scripts/viewer_manifest.py']+list((P/'scripts').glob('round5*'))+list((P/'review/viewer').glob('*.glb'))+[P/'review/viewer/manifest.json']+list((P/'work/round2').glob('lod[0-3].blend'))
paths += [x for x in R.rglob('*')if x.is_file()and 'baseline'not in x.relative_to(R).parts and x.name!='artifact_manifest.json']
paths += list((P/'review/clips').rglob('*'))+list((P/'review').glob('*sheet.jpg'))+list((P/'review').glob('hands_*.jpg'))+list((P/'review').glob('browser_*.png'))
manifest={str(f.relative_to(P)):{'sha256':sha(f),'bytes':f.stat().st_size}for f in paths if f.is_file()}
(R/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('R5 HANDOFF',g['counts'],'texture MiB',mem,'artifacts',len(manifest))

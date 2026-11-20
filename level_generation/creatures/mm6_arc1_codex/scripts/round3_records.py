"""Record R3 evidence; shared failures prevent technical acceptance."""
from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
read=lambda p:json.loads((P/p).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('review/delivery_validation.json');n=read('review/round3/native_pose.json');c=read('review/round3/shared_comparison.json')
shared=read('review/round3/shared_final/gates.json');baseline=read('review/round3/shared_baseline/gates.json')
g=v['lod_gate_maxima'];distance=v['distance_silhouettes'];files=v['files'];runtime=[k for k in files if k.startswith('export/')]
table='\n'.join('| ['+Path(k).name+']('+k+') | '+' / '.join(map(str,list(files[k]['triangles'].values())[:4]))+' | '+str(files[k]['bytes'])+' | '+files[k]['sha256']+' |'for k in runtime)
native_rows=[]
for label,key,mult,unit in [('Wrist lateral from hip','wrist_lateral_from_hip_per_height',100,'% height'),('Wrist forward from hip','wrist_forward_from_hip_per_height',100,'% height'),('Grip lateral from hip','grip_lateral_from_hip_per_height',100,'% height'),('Grip forward from hip','grip_forward_from_hip_per_height',100,'% height'),('Upper-arm front angle','upper_front_deg',1,'degrees'),('Forearm front angle','forearm_front_deg',1,'degrees'),('Upper-arm side angle','upper_side_deg',1,'degrees'),('Forearm side angle','forearm_side_deg',1,'degrees'),('Bow from vertical','bow_tilt_deg',1,'degrees')]:
 native_rows.append('| '+label+' | '+' | '.join(f'{n[t][key]*mult:.2f}'for t in ['native','round2','round3'])+' | '+unit+' |')
near=[r for r in shared['gates']if r['status']=='FAIL'and r['lod'].endswith('colour0')]
fault_table='\n'.join(f"| {key} | {c['baseline_failure_categories'].get(key,0)} | {value} |"for key,value in c['failure_categories'].items())
audit=f"""# Shared audit comparison — review round 3

Final **{shared['status']}**, archived R2 **{baseline['status']}**, using the same production intent configuration.
Final counts: {shared['counts']}. R2 counts: {baseline['counts']}.
New failing rows: {len(c['new_failures'])}; resolved rows: {len(c['resolved_failures'])}.
Counts include repeated colour/shadow LOD rows, not independent visible defects.

| Gate | R2 FAIL rows | R3 FAIL rows |
|---|---:|---:|
{fault_table}

The old project gate suite passing does **not** make this a technical-completion PASS.
Short puff sleeves use collision mode (containment: false), following the shared README/VALIDATION.
The 9 mm sole patch matches previous heel/toe selection. Elbow/palm axes come from the fitted rest skeleton.
Source-relative rotation/acceleration allowances are retained from library measurements.
No wrist, elbow, contact, cloth or penetration threshold was relaxed to make this pose pass.

The shared grip test samples seven points per triangle against actual prop surfaces; the project test samples
45 and uses a grip-cylinder penetration proxy. These are not equivalent contact certificates. Shared finger
gaps remain unresolved despite the legacy result below 3 mm. Inset shadows can fail physical foot/contact
tests. Arrow/body nock contact and retained action elbow/wrist findings also need review; they are not
dismissed as runner bugs. Exact clip, side, time, LOD, value and threshold remain in [gates.md](shared_final/gates.md).

This is a handoff with open faults, not a technical PASS or recommendation to install. Broader rewrites of
accepted Attack/Death/free-arm motions were not silently added to this pose revision.

| Near clip | Gate / region | Worst | Limit | Time (s) |
|---|---|---:|---:|---:|
"""
for r in near:audit+=f"| {r['clip']} | {r['gate']} / {r['region']} | {r['worst']:.4f} | {r['threshold']} | {r['time_s']} |\n"
(R/'SHARED_AUDIT.md').write_text(audit)
distance_table='\n'.join(f"| {l} | "+' | '.join(f"{next(r['pooled_iou']for r in distance['rows']if r['lod']==l and r['clip']==a):.5f}"for a in ['Standing','Attack'])+' |'for l in [1,2,3])
maxgap=max(x['grip_gap_mm']for x in g.values());maxpen=max(x['grip_penetration_mm']for x in g.values())
handoff=f"""# MM6 BArcher arc1 — batch handoff

## Review round 3

**Pose revision exported and reviewed; technical acceptance remains pending because the shared runner
reports FAIL.** [Full verdict](review/round3/shared_final/gates.md) ·
[Compared with R2](review/round3/SHARED_AUDIT.md) · [Delivery checks](review/delivery_validation.json).

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) ·
[Native comparison](review/round3/native_rest_comparison.jpg) · [Turnaround](review/turnaround_sheet.jpg) ·
[Hand close-up](review/hands_Standing.jpg).

The bow upper arm hangs closer to the torso, wrist beside the upper thigh. Hand and bow turn together,
retaining the exact closed fist-to-wrap attachment. Standing/Fidget use this rest; other clips blend from/to it.
Walking adds outward carry swing to clear the leg; Hit returns later to avoid the recovering calf.
The free arm, planted feet, bracer textures, near geometry and bow-shot Cast remain intact.
Cast is still an exact Attack copy under its distinct name ({v['cast_exact_attack_copy']['channels']} channels).
Both release at 1.200 s from Socket_Arrow_Release.

### Files, hashes and integration

| Runtime file | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{table}

Body and bow GLBs changed. Arrow is byte-identical to R2. Shadow counts equal colour counts.
The body includes the 24-triangle animated string, 63 joints, eight clips, three variants and four 2080×1024 atlases.
Near geometry, UVs, weights, materials and image pixels match R2. Far body/bow silhouette vertices were fitted;
topology/counts/contact areas remain. Maximum per-axis position changes versus R2 are 6 mm on far
colour body, 4 mm on its shadow and 8 mm on far bow. Exact changed attributes are in the delivery report.

**integration/actors.yml did not change**, SHA-256: {sha(P/'integration/actors.yml')}.
IDs 475/476/477, scale 106.382287, yaw −pi/2, stride 1.02417324 and run: Walking remain.
No palm_right binding returns. Installation belongs to the orchestrator; no assets_dev files were copied.

Changed masters: work/rig_equipped.blend, work/rig_textured.blend, work/runtime_authoring.blend and
work/round2/lod0.blend through lod3.blend. Motion/export/review scripts, gates.json, viewer assets,
sheets and records changed. [Artifact manifest](review/round3/artifact_manifest.json) records exact hashes.
The complete previous handoff and inputs remain in [R2 baseline](review/round3/baseline/HANDOFF.md).

### Native measurements

| Measurement | Native | R2 | R3 | Units |
|---|---:|---:|---:|---|
{chr(10).join(native_rows)}

At 256 px native body height, visible landmarks have ±2 px uncertainty; the estimated anatomical hip has ±6 px.
R3 3D elbow bend is {n['round3']['elbow_bend_3d_deg']:.2f}°; projected side bend is
{abs(n['round3']['forearm_side_deg']-n['round3']['upper_side_deg']):.2f}° versus native
{n['native']['elbow_bend_side_deg']:.2f}°. The native side bow is nearly horizontal; the explicit R3 request
takes precedence and retains a vertical bow. Standing sampled bow-to-leg clearance:
{n['round3']['bow_to_leg_clearance_m']*100:.2f} cm.
[Raw landmarks](review/round3/native_pose.json) accompany the annotated front/side sheet.

### Checks

Existing project gates rerun on every selected LOD/clip: maximum grip gap {maxgap:.3f} mm,
penetration {maxpen:.3f} mm, arm p99 stretch {max(x['arm_p99']for x in g.values()):.3f},
finger stretch {max(x['finger_max']for x in g.values()):.3f}.
Body/equipment contacts are zero under those legacy region/parity definitions.
Standing/Fidget near soles tilt at most 0.731°; heel/toe witnesses stay within 2.805 mm of the floor.
Walking retains about 9 cm swing lift, a planted support foot and near foot yaw within 10°.
[Contact/gait](review/round3/contact_gates.json) · [Feet/elbows](review/round3/anatomy_and_feet.json).

Release/draw, UVs, all-LOD head clearance, exact exported rest boundaries, source-relative acceleration and
export traces rerun. Attack/Cast time/value arrays remain identical. All 71 native input hashes match.
check_bindings.py passes with no BAD line, including all LOD/shadow weight sums and material extensions.
[Binding log](review/round3/check_bindings.log).
Viewer: 24/24 tier/clip switches, zero console/load errors. Seven browser captures and eight three-view
clip sheets refreshed; browser closed.

**Shared audit: {shared['status']}**, counts {shared['counts']}. The same config on R2 gives
{baseline['counts']}. [Fault breakdown](review/round3/SHARED_AUDIT.md) retains remaining elbow/wrist,
palm/contact, cloth and foot findings and exact times. Local PASS is not substituted for this verdict.
These unresolved findings prevent claiming the full batch done criteria. In near Standing, the shared
held-wrist flexion is 86.18 degrees (limit 70) and palm/grip angle is 68.06 degrees (limit 60).
There are three new failures versus R2: left-sleeve contact on shadow LOD3 in Standing/Fidget/Walking,
up to 6.33 mm (limit 2 mm); 24 wrist-roll failure rows were resolved. No threshold was relaxed.

### Triangle evidence

No triangles added. The R2 reduction/rebake curve remains applicable to unchanged near meshes/maps:
selected body IoU 0.99461, textured SSIM 0.96445; next 8,555-triangle body SSIM 0.9447 failed.
[Near curve](review/round2/reduction/curve.png) · [body](review/round2/reduction/body_side_by_side.jpg) ·
[bow](review/round2/reduction/bow_side_by_side.jpg) · [arrow](review/round2/reduction/arrow_side_by_side.jpg).

Current equipped silhouettes after reposing and far fitting:

| LOD | Standing pooled IoU | Attack release diagnostic IoU |
|---|---:|---:|
{distance_table}

Standing passes 0.97 at 550/220/88 px. Attack LOD2/3 remain below 0.97 and need explicit distance review.
[Current comparison](review/round3/reduction/distance_sheet.jpg) ·
[Measurements](review/round3/reduction/assembled_distance_metrics.json) ·
[Final small bow fit](review/round3/reduction/final_bow_fit.json).
Earlier fit trials are evidence, not selected inputs; current work/round2/lod*.blend files are authoritative.

### Reproduction and limits

Use the project lease for every write. Blender runs through tools/run_creature_blender.sh, background,
--threads 4, one process. round3_motion.py restores R2 actions and syncs the revised carry to current LOD scenes.
round3_verify_render.py exports, runs existing gates, renders and invokes the shared runtime runner.
round3_post.py runs viewer/bindings/smoothness and composes evidence; validate_delivery.py checks final exports;
round3_records.py writes this record. Do not rerun historical round2_assemble.py over current fitted LODs.
round3_prepare_final.py records the one-time far-fit step, not a necessary repeat on resume.

Budget: **40/100 credits total, 0 this round**. No purchases, game launches, builds, installation,
shared-project edits or commits. Runtime regression and GPU/game capture remain the orchestrator's work.
Lease released as final operation; user artistic acceptance pending.

Earlier rounds: [Review round 2](review/round3/baseline/HANDOFF.md),
[Review round 1](review/round2/baseline/HANDOFF.md).
"""
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text("""# MM6 BArcher arc1 — Codex project

Review round 3 pose revision is staged. **Shared runtime gates report FAIL; technical acceptance is pending.**
[HANDOFF.md](HANDOFF.md) has current files, hashes, triangle counts, native measurements and open faults.
Budget: 40/100 credits total, zero this round.

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) ·
[Shared verdict](review/round3/shared_final/gates.md) · [R2 comparison](review/round3/SHARED_AUDIT.md).

![Native and revised pose](review/round3/native_rest_comparison.jpg)

Bow wrist beside upper thigh, nearly straight arm, inward-facing vertical bow. The same closed fist/grip
follows Standing/Fidget and transitions. Walking clears the leg. Both bracers, flat idle soles, free arm,
near meshes/maps and exact Attack-copy Cast remain. The native side bow is nearly horizontal; explicit R3
vertical-carry instructions override that angle. Native hip estimates include their uncertainty.

Current body counts: 9531/5223/1904/620; bow: 2108/1150/420/193; arrow: 92/40/5/4.
Body/bow exports changed; arrow and integration/actors.yml are unchanged. No assets_dev installation.
Masters: work/rig_equipped.blend, rig_textured.blend, runtime_authoring.blend.
Current selected LOD scenes remain work/round2/lod0.blend through lod3.blend. That directory name records
their geometry origin; their actions/far fits are now R3. Old selected.json and round2_assemble.py are
historical and must not overwrite these scenes.

Use leased reproduction steps in HANDOFF.md. R2 snapshot: review/round3/baseline/.
Shared gates use gates.json: collision-mode puff sleeves, measured rig axes and source-relative smoothness.
Wrist/elbow/contact thresholds are not raised to force PASS. All 71 native hashes unchanged.
No purchases, game launches, builds or commits.

[Delivery validation](review/delivery_validation.json) · [Native landmarks](review/round3/native_pose.json) ·
[Contact/gait](review/round3/contact_gates.json) · [Distance sheet](review/round3/reduction/distance_sheet.jpg) ·
[Near curve](review/round2/reduction/curve.png) · [Visual review](review/round3/visual_review.json).
""")
progress=read('creature_3d_progress.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
progress.update(stage='review_round_3_handoff',status='needs_review',technical_completion='pending_shared_gate_findings',user_acceptance='review_round_3_pending',updated_at=now,next_action='Orchestrator reviews shared gate FAIL and pose; no automatic install recommendation')
progress['selected_artifacts']={k:{'path':k,**x}for k,x in files.items()}
progress['validation']={'report':'review/delivery_validation.json','status':v['status'],'shared_runner':v['shared_runner'],'viewer':'review/round3/check_viewer.log','viewer_switches':24,'skin_weights':'review/round3/check_bindings.log','visual_review':'review/round3/visual_review.json','gates':v['gates']}
progress['runtime']['installation']='round3_staged_with_open_shared_gate_findings'
progress['stages']['animations_and_gates']='pending_shared_gate_findings'
progress['review_round_3']={'recorded_at':now,'status':'pose_revision_exported_shared_gates_fail','credits_spent':0,'total_credits':40,'integration_actors_yml_changed':False,'shared_runner':v['shared_runner'],'changed_runtime_files':runtime[:2],'unchanged_runtime_files':[runtime[2]],'native_comparison':'review/round3/native_pose.json','handoff':'HANDOFF.md'}
progress['findings']=[{'id':'shared_runtime_gate_findings','status':'open','evidence':['review/round3/SHARED_AUDIT.md','review/round3/shared_final/gates.md']},{'id':'distance_attack_silhouette','status':'open_artistic_review','evidence':['review/round3/reduction/distance_sheet.jpg']}]
progress['correction_ledger']=[r for r in progress['correction_ledger']if not r['finding'].startswith('Review round 3:')]
progress['correction_ledger'].append({'finding':'Review round 3: bow hand away from hip','change':'Native-measured arm target, carry wrist/bow rotation, thigh clearance and shared audit','result':'Pose revision staged; shared audit FAIL retained.'})
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
for path in ['source/ANIMATION_STUDY.md','integration/playbook_notes.md']:
 f=P/path;old=f.read_text()
 if not old.startswith('> Review round 3'):f.write_text('> Review round 3 supersedes the carry/rest pose below. See [current handoff](../HANDOFF.md); shared runtime gates remain FAIL.\n\n'+old)
manifest={}
paths=[P/k for k in files]+[P/'integration/actors.yml',P/'gates.json']+list((P/'scripts').glob('*.py'))+list((P/'work/round2').glob('lod[0-3].blend'))
for path in paths:
 if path.is_file():manifest[str(path.relative_to(P))]={'sha256':sha(path),'bytes':path.stat().st_size}
(R/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('R3 handoff recorded; technical acceptance pending shared FAIL.')

"""Record selected R4 artifacts and the shared runner's unaltered verdict."""
from pathlib import Path
import json,hashlib,datetime,collections
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
read=lambda p:json.loads((P/p).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('review/delivery_validation.json');g=read('review/round4/shared_final/gates.json');c=read('review/round4/shared_comparison.json');n=v['native_measurements'];tex=v['texture_sets']['assets'];files=v['files']
runtime=[k for k in files if k.startswith('export/')]
filetable='\n'.join(f"| [{Path(k).name}]({k}) | {' / '.join(map(str,list(files[k]['triangles'].values())[:4]))} | {files[k]['bytes']} | {files[k]['sha256']} |"for k in runtime)
texturetable='\n'.join(f"| {name} | {x['images_before']} → {x['images_after']} | {'×'.join(map(str,x['dimensions_before']))} → {'×'.join(map(str,x['dimensions_after']))} | {x['bytes_before']} → {x['bytes_after']} |"for name,x in tex.items())
rgba=lambda x,key:x['images_after']*x[key][0]*x[key][1]*4
before=sum(rgba(x,'dimensions_before')for x in tex.values());after=sum(rgba(x,'dimensions_after')for x in tex.values())
oldbytes=sum((R/'baseline/export'/Path(k).name).stat().st_size for k in runtime);newbytes=sum(files[k]['bytes']for k in runtime)
near=[r for r in g['gates']if r['lod'].endswith('colour0')]
take=lambda gate,clips=None:[r['worst']for r in near if r['gate']==gate and (clips is None or r['clip']in clips)and r['worst']is not None]
measure={'near_grip_gap_max_mm':max(take('grip_gap_mm')),'near_grip_penetration_max_mm':max(take('grip_penetration_mm'))}
rest=[r for r in near if r['clip']in ['Standing','Fidget']and any(w in r['gate']for w in ['sole','heel','toe','floor'])]
bow=[r for r in g['gates']if r['gate']=='prop_body_penetration_mm'and r['region']=='bow'];measure['bow_body_penetration_max_mm']=max(r['worst']for r in bow)
measure['rest_feet']=rest
(R/'selected_measurements.json').write_text(json.dumps(measure,indent=2))
faults='\n'.join(f"| {key} | {value} |"for key,value in c['failure_categories'].items())
audit=f"""# Review round 4 — shared audit

**{g['status']}**. Counts: {g['counts']}; R3: {c['baseline_counts']}.
Compared by clip / LOD / region: {len(c['new_failures'])} newly failing rows, {len(c['resolved_failures'])} resolved rows.
Rows repeat skeleton evidence across colour/shadow LODs; they are not independent visible defects.

| Gate | Failing rows |
|---|---:|
{faults}

No contact, elbow, palm or wrist limit was relaxed. [Every raw row](shared_final/gates.md) retains exact
time, threshold, region and LOD. [Machine-readable comparison](shared_comparison.json).
Near grip surface gap is at most {measure['near_grip_gap_max_mm']:.3f} mm; penetration
{measure['near_grip_penetration_max_mm']:.3f} mm. Distant-LOD finger gaps and transition grip penetration
remain failures. The inherited palm-facing cone is about 68.06° against 60°, despite closed surface contact.
Other action-arm, cloth, foot and arrow/nock findings remain open. They are not silently waived.

Hit retains the library torso, free arm and legs. Its bow arm carries outward smoothly through recoil and returns
to the new rest. A tiny hidden Arrow scale of .001 was replaced by exact zero in all hidden portions, matching
the runner and engine's hidden-prop semantics. Release remains full-sized at 1.200 s.

| Near clip | Gate / region | Worst | Limit | Time s |
|---|---|---:|---:|---:|
"""
for row in near:
 if row['status']=='FAIL':audit+=f"| {row['clip']} | {row['gate']} / {row['region']} | {row['worst']:.4f} | {row['threshold']} | {row['time_s']} |\n"
(R/'SHARED_AUDIT.md').write_text(audit)
distance=read('review/round4/reduction/assembled_distance_metrics.json')
distance_table='\n'.join(f"| {level} | "+' | '.join(f"{next(r['pooled_iou']for r in distance['rows']if r['lod']==level and r['clip']==clip):.5f}"for clip in ['Standing','Attack'])+' |'for level in [1,2,3])
native_table=(R/'native_measurements.md').read_text().split('\n\n')[0]
handoff=f"""# MM6 BArcher arc1 — batch handoff

## Review round 4

The requested native carry is exported: left arm hangs at the relaxed right arm's height, with a small forward
elbow bend in side view; closed fist at the upper thigh. The bow points forward, **72° from vertical / 18° below
horizontal toward the front**, rear tip higher, string underneath. This supersedes the incorrect vertical-bow
instruction in rounds 2–3. [Approved sketch](review/round4/approved_target_sketch.png).

**Technical acceptance remains pending: shared gates report {g['status']}.** This is a staged pose correction
with explicit open faults, not a claim that the batch done criteria all pass.
[Shared audit](review/round4/SHARED_AUDIT.md) · [Raw gates](review/round4/shared_final/gates.md) ·
[Delivery checks](review/delivery_validation.json).

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) ·
[Native comparison with measurements](review/round4/native_rest_comparison.jpg) ·
[Turnaround](review/turnaround_sheet.jpg) · [Closed grip](review/hands_Standing.jpg) ·
[All clip sheets](review/clips/).

### Files and integration

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{filetable}

All three runtime files changed. Geometry, normals, indices and skin weights at every colour/shadow LOD
are identical to R3; UVs are translated by whole texels and normalized to the new atlas dimensions.
Body shadow counts equal colour counts. Body includes the 24-triangle string, 63 joints and eight clips.
Both bracers, relaxed right arm and foot motion are preserved. Cast is an exact Attack copy under its distinct
name ({v['cast_exact_attack_copy']['channels']} channels); launch remains **1.200 s / Socket_Arrow_Release**.
Hidden Arrow intervals now have exact zero scale; their exported quaternion keys are smoothed before/after visibility, preserving every visible keyed pose and both rest endpoints. Hit carries the bow outward during recoil to clear the leg.
The new rest is shared by Standing/Fidget and the Walking/Attack/Cast/Hit/Death boundaries.

**integration/actors.yml did not change**, SHA-256 {sha(P/'integration/actors.yml')}.
IDs 475/476/477, scale 106.382287, yaw −pi/2, stride 1.02417324, run: Walking and all event bindings remain.
No palm_right binding. Nothing was copied to assets_dev.

Changed masters: work/rig_equipped.blend, work/rig_textured.blend, work/runtime_authoring.blend,
work/round2/lod0.blend through lod3.blend. The runtime authoring master imports the final padded tier-A
review GLB; the fitted source/LOD masters keep their accepted source UV maps and use the runtime atlas
post-process at export. Updated scripts, viewer files, clip/hand/pose sheets and records are covered by
[artifact hashes](review/round4/artifact_manifest.json). Previous handoff: [R3 snapshot](review/round4/baseline/HANDOFF.md).

### Native versus round 4

{native_table}

Front-projection wrist mirror error is {n['round4']['mirrored_right_wrist_front_error_m']*1000:.2f} mm.
The bow wrist sits {n['round4']['wrist_forward_of_right_m']*1000:.2f} mm forward of the free wrist because the
native side pose has a slight forward elbow bend. Native landmarks are manual estimates: ±2 px visible,
±6 px inferred hip at 256 px height. Native azimuth is inferred from the end-on front view.
The native hip estimate and fitted skeleton hip do not represent perfectly identical anatomical points;
the table retains the discrepancy rather than asserting an exact match.
The raw side bitmap faces right and its forward end rises about 17.8°. The explicit approved sketch instead
asks for the forward end lower and the string underneath. R4 follows that more specific instruction
(−18° signed forward pitch); bow geometry/size stays unchanged. This signed difference is shown in the table.

Measured standing bow-to-leg surface clearance: {n['round4']['bow_to_leg_clearance_m']*1000:.2f} mm.

### Texture sets and memory

| Runtime asset | Image count | Atlas dimensions per map | GLB bytes before / after padding |
|---|---|---|---|
{texturetable}

There were already shared LOD maps: image count stays **10 total**, with one set per asset across all its LODs.
All colour, tangent normal, material and region-mask maps now use **17 px nearest-edge dilation** around
packed connected all-LOD texture charts (18 px minimum UV-to-patch border). UV island shapes and texel
density stay unchanged: integer-pixel translation, no rotation, scale or resampling.
[Packing record](review/round4/texture_sets.json) and per-asset translation maps in work/round4/ record the layout.
Float32 UV rounding is below .001 texel; delivery checks compare triangle shape and actual sampled map pixels.

Total package size: R3 **{oldbytes:,} bytes → R4 {newbytes:,} bytes** ({100*(1-newbytes/oldbytes):.2f}% smaller).
**Decoded RGBA8 base-level memory rises {before/1048576:.2f} → {after/1048576:.2f} MiB** to provide the margins
without reducing density. A full mip chain is approximately 4/3 of these figures; actual cooked/GPU formats
may differ. Smaller compressed files do not imply lower GPU texture memory.

### Validation and retained faults

Viewer: 24 tier/clip switches and seven appearance captures, zero browser errors. check_bindings.py:
**no BAD line**, including final runtime skin weights/materials. All 71 read-only native input hashes match.
Exact Attack/Cast channel equality, all rest boundaries, triangle caps, shadow OPAQUE materials and export
preservation pass. Shared gate verdict: **{g['status']}**, {g['counts']}.
Near grip: gap ≤ {measure['near_grip_gap_max_mm']:.3f} mm, penetration ≤ {measure['near_grip_penetration_max_mm']:.3f} mm.
Bow/body penetration maximum across the audit: {measure['bow_body_penetration_max_mm']:.3f} mm.
[Rest sole/heel/toe measurements](review/round4/selected_measurements.json).

Shared failures include distant-LOD grip contact and retained action anatomy/cloth/palm/foot findings.
See the exact rows and newly failing/resolved comparison in the audit; none is relabelled PASS.
The broad all-gates requirement remains unmet. The closed-body scan finds no boundary edges entirely below
the 0.95 m belt band. Colour LOD0–3 have 71/68/31/45 boundary edges intersecting the 1.25–1.45 m shoulder band;
this includes garment/neck/quiver openings. Their intended-opening classification remains **UNVERIFIED**,
not a closed-body PASS. Topology is unchanged; counts and method are in the delivery report.

No triangle reduction was added in this pose round, per the instruction to keep the selected LODs.
The existing [near reduction curve](review/round2/reduction/curve.png) remains the selection evidence:
body near IoU .99461 / SSIM .96445; the next 8,555-triangle candidate failed SSIM at .9447.
Geometry is byte-identical to R3. Current equipped silhouettes were remeasured at 550/220/88 px:

| LOD | Standing pooled IoU | Attack release pooled IoU |
|---|---:|---:|
{distance_table}

[Current distance metrics](review/round4/reduction/assembled_distance_metrics.json).
Failures below .97 remain distance-review faults; no counts were increased to hide them.
The selected near reduction curve is historical evidence, not a fresh textured re-render against the high mesh.
Final viewer checks and direct texel-translation checks cover the atlas revision.

### Reproduction and scope

Use the workspace lease on every write and tools/run_creature_blender.sh with --threads 4, one process.
1. scripts/round4_motion.py restores archived R3 animation inputs, authors the new carry and exports the selected LODs.
2. Copy the three exported runtime GLBs to work/round4/runtime_unpadded/.
3. scripts/round4_textures.py pads/repackages those snapshots; scripts/round4_arrow_export.py restores hidden-arrow quaternion continuity; scripts/round4_viewer.py builds the viewer from final GLBs.
4. scripts/round4_render.py runs shared gates, native measurement, all clip/hand/pose sheets, release checks and
   current switch-size silhouettes. scripts/round4_final_audit.py refreshes the shared verdict, final runtime master and release check after the hidden-arrow post-process. CPU Cycles was used because Workbench crashes on this host.
5. scripts/check_viewer.py, scripts/round4_validate.py, scripts/round4_sheets.py and scripts/round4_records.py
   finish checks and records.

Do not run historical round2_assemble.py over the fitted LOD scenes. Do not install the viewer GLBs as runtime assets.
Budget: **40/100 credits total, 0 this round**. No Meshy calls, game launches, builds, installation or commits.
Game integration/regression and hardware capture remain the orchestrator's work. Lease released at handoff.
"""
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text(f"""# MM6 BArcher arc1 — Codex project

Review round 4 exports the user-approved native bow carry. **Shared gates remain {g['status']}; technical acceptance is pending.**
[HANDOFF.md](HANDOFF.md) has files, hashes, counts, measurements, texture-memory tradeoff and open faults.

![Native versus round 4](review/round4/native_rest_comparison.jpg)

The left hand hangs at the relaxed right hand's height, with the native slight forward side bend.
The bow is nearly horizontal along facing direction: 72° from vertical, front tip lower, string underneath.
The old vertical-bow instruction is superseded. Both bracers, right arm, feet, bow-shot Cast and selected LOD geometry remain.
Hit retains its library body/free-arm recoil with a smooth outward bow carry to clear the leg.

One shared texture set per asset/LOD chain, 17 px dilated margins and unchanged texel density. Image count remains 10.
Compressed GLBs shrink, but decoded texture memory grows {before/1048576:.2f} → {after/1048576:.2f} MiB.
integration/actors.yml is unchanged; no assets_dev installation. Budget 40/100 credits, zero this round.

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) ·
[Shared audit](review/round4/SHARED_AUDIT.md) · [Delivery checks](review/delivery_validation.json) ·
[Previous handoff](review/round4/baseline/HANDOFF.md).
""")
progress=read('creature_3d_progress.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
progress.update(stage='review_round_4_handoff',status='needs_review',technical_completion=v['technical_completion'],user_acceptance='review_round_4_pending',updated_at=now,next_action='Orchestrator reviews the corrected native carry and explicit shared-gate/LOD faults before installation.')
progress['selected_artifacts']={k:{'path':k,**val}for k,val in files.items()}
progress['validation']={'report':'review/delivery_validation.json','status':v['status'],'shared_runner':v['shared_runner'],'viewer':'review/round4/check_viewer.log','viewer_switches':24,'skin_weights':'review/round4/check_bindings.log'}
progress['runtime']['installation']='round4_staged_with_open_shared_gate_findings';progress['stages']['animations_and_gates']='pending_shared_gate_findings'
progress['review_round_4']={'recorded_at':now,'credits_spent':0,'total_credits':40,'integration_actors_yml_changed':False,'shared_runner':v['shared_runner'],'changed_runtime_files':runtime,'native_comparison':'review/round4/native_pose.json','texture_sets':'review/round4/texture_sets.json','handoff':'HANDOFF.md'}
progress['findings']=[{'id':'shared_runtime_gate_findings','status':'open','evidence':['review/round4/SHARED_AUDIT.md','review/round4/shared_final/gates.md']},{'id':'distance_silhouette','status':'open_artistic_review','evidence':['review/round4/reduction/assembled_distance_metrics.json']}]
progress['correction_ledger']=[r for r in progress['correction_ledger']if not r['finding'].startswith('Review round 4:')]
progress['correction_ledger'].append({'finding':'Review round 4: hanging arm and native horizontal carry; shared texture margins','change':'Front-matched relaxed arm, native side bend, forward 18-degree bow with underside string, padded shared atlases','result':'Pose revision exported; shared audit FAIL and memory tradeoff recorded.'})
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
manifest={}
paths=[P/k for k in files]+[P/'integration/actors.yml',P/'gates.json',P/'README.md',P/'HANDOFF.md']+list((P/'scripts').glob('round4*.py'))+list((P/'review/viewer').glob('*.glb'))+list((P/'work/round2').glob('lod[0-3].blend'))
paths += [P/'source/ANIMATION_STUDY.md',P/'integration/playbook_notes.md',P/'scripts/viewer_manifest.py',P/'review/viewer/manifest.json']
paths += [x for x in R.rglob('*')if x.is_file()and 'baseline'not in x.relative_to(R).parts and x.name!='artifact_manifest.json']
paths += [x for x in (P/'review/clips').rglob('*')if x.is_file()]
paths += list((P/'review').glob('browser_*.png'))+list((P/'review').glob('*sheet.jpg'))+list((P/'review').glob('hands_*.jpg'))
for path in paths:
 if path.is_file():manifest[str(path.relative_to(P))]={'sha256':sha(path),'bytes':path.stat().st_size}
(R/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('R4 handoff written. Shared verdict:',g['status'])

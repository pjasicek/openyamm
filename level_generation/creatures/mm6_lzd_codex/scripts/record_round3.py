"""Record round 3 only after the final runtime, motion, reduction and browser checks pass."""
import sys,json,hashlib,datetime,struct
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P/'review'
def read(name):return json.loads((P/name).read_text())
def write(name,value):(P/name).write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
motion=read('review/round3_motion_gate.json');accel=read('review/angular_acceleration.json');scan=read('review/deformation_scan.json');contact=read('work/g6_contacts.json');heads=read('review/head_clearance.json');equipment=read('review/equipment_gate.json');trace=read('review/export_trace.json');runtime=read('review/runtime_validation.json');viewer=read('review/viewer_check.json');lods=read('review/rebake/runtime_lod_validation.json');info=read('export/export_info.json')
assert motion['passed']and accel['passed']and trace['flags']==0
assert viewer['switched']==27 and not viewer['failed']and not viewer['consoleErrors']
assert all(v['passed']and v['silhouette']['actor']['passed']for v in lods.values())
for name in ['check_weights_round3.txt','check_bindings_round3.txt']:
 assert not any(line.startswith('BAD')for line in(R/name).read_text().splitlines())
release=read('review/ranged_release.json');joined=read('review/string_join_gate.json');assert joined['passed']
gates={'status':'technical_pass','source':'Actual LOD0 GLB reimport, all nine clips; lower runtime LOD receipts in review/rebake/','criteria':{'arm_p99':2,'hand_max':4.5,'body_equipment_cloth_mm':2,'head_mm':10,'elbow_plane_deg':1,'forearm_twist_deg':90.1,'grip_mm':3,'foot_yaw_deg':10},'clips':{},'lower_lods':{k:{n:v[n]for n in ['passed','arm_p99','hand_max','body_contact_m','head_contact_m','equipment_contact_m','runtime_triangles']}for k,v in lods.items()}}
for name,s in scan.items():
 g={'arm_stretch_p99':max(v['p99']for k,v in s['stretch'].items()if k.endswith('_arm')),'hand_stretch_max':max(v['max']for k,v in s['stretch'].items()if k.endswith('_hand')),'body_contact_mm':max([0]+[v[0]*10 for v in contact[name].values()]),'head_contact_mm':heads[name]['depth_m']*1000,'equipment_contact_mm':max(v['depth_m']for v in equipment[name]['contacts'].values())*1000,'posture':s['posture'],'samples':s['samples'],'motion':motion['clips'][name],'angular_acceleration':accel['clips'][name]}
 g['passed']=g['arm_stretch_p99']<=2 and g['hand_stretch_max']<=4.5 and g['body_contact_mm']<=2 and g['head_contact_mm']<=10 and g['equipment_contact_mm']<=2 and all(v['passed']for v in g['angular_acceleration'].values())
 assert g['passed'],name
 gates['clips'][name]=g
write('review/gates.json',gates)
# The lighting diagnostic is explicitly not a native-GPU colour calibration.
def green_stats(paths):
 ys=[]
 for path in paths:
  a=np.asarray(Image.open(path).convert('RGBA'),dtype=float)/255;c=a[...,:3];m=(c[...,1]>1.15*c[...,0])&(c[...,1]>1.3*c[...,2])&(c[...,1]>.08)&(a[...,3]>.5);ys.extend((c@np.array([.2126,.7152,.0722]))[m].tolist())
 return {'pixels':len(ys),'mean_srgb_luma':float(np.mean(ys)),'p95_srgb_luma':float(np.percentile(ys,95))}
skin={'native_standing':green_stats(sorted((P.parent/'mm6_lzd/native').glob('lzdstaa*.png'))),'unreduced_review':green_stats(sorted((R/'rebake').glob('reference_pbr_body_l0_*.png'))),'rebaked_review':green_stats(sorted((R/'rebake').glob('near70final_body_l0_*.png'))),'method':'Rec709 coefficients on sRGB; green chroma mask, all views pooled. Controlled review lights differ from baked sprite lighting; native GPU matching remains an orchestrator check. No skin ramp darkening or tier recolour was introduced.'}
write('review/skin_luminance.json',skin)
files={}
for path in sorted((P/'export').glob('*.glb'))+sorted((P/'review/viewer').glob('*.glb')):
 if path.name=='mm6_lzd_lods.geometry.glb':continue
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);files[str(path.relative_to(P))]={'sha256':sha(path),'bytes':len(raw),'triangles_per_mesh':[sum(d['accessors'][q['indices']]['count']//3 for q in m['primitives'])for m in d['meshes']]}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt={'status':'passed','completed_at':now,'choice':'b: Cast is an exact copy of the library-derived Attack','additional_credits':0,'spent_credits':60,'budget_credits':100,'files':files,'runtime_files':runtime['files'],'actors_changed':True,'actors_sha256':sha(P/'integration/actors.yml'),'cast':read('review/cast_gate.json'),'motion':motion,'angular_acceleration':accel,'string_join':joined,'ranged_release':release,'reduction_curve':read('review/reduction/curve.json'),'actual_tiers':read('review/rebake/actual_tiers.json'),'lower_runtime_lods':lods,'viewer_switches':27,'check_weights_bad_lines':0,'check_bindings_bad_lines':0,'integration_executed':False,'lower_grip_fit':read('review/rebake/lower_grip_fit.json'),'head_plane_audit':read('review/rebake/head_plane_audit.json'),'lease_release':'Release after this record and final visual inspection.'}
write('review/review_round3.json',receipt)
arm=max(g['arm_stretch_p99']for g in gates['clips'].values());hand=max(g['hand_stretch_max']for g in gates['clips'].values());head=max(g['head_contact_mm']for g in gates['clips'].values());grip=max(v for c in motion['clips'].values()for v in c['grip_distance_max_m'].values())*1000;flex=min(v['flex_min']for c in motion['clips'].values()for v in c['elbows'].values());plane=max(v['plane_max']for c in motion['clips'].values()for v in c['elbows'].values())
nearbody=runtime['files']['mm6_lzd.glb']['triangles'];nearbow=runtime['files']['mm6_lzd_bow.glb']['triangles']
counts='\n'.join(f"| {file} | {' / '.join(map(str,v['triangles']))} | {v['bytes']:,} |"for file,v in runtime['files'].items())
yaw='\n'.join(f"| {role} | {side} | {m['feet'][side]['yaw_min_deg']:.4f} to {m['feet'][side]['yaw_max_deg']:.4f} | {m['feet'][side]['lowest_sole_m']*1000:.3f} | {m['feet'][side]['swing_peak_m']*100:.2f} |"for role in ['Standing','Fidget','Walking','Running']for side in'LR'for m in[motion['clips'][role]])
hashes='\n'.join(f"| `{name}` | `{v['sha256']}` | {' / '.join(map(str,v['triangles_per_mesh']))} |"for name,v in files.items())
faults=[
'This already-running round retains separate rebaked LOD texture maps and project-local gates. The batch document changed during the round; its Cost controls item 4 explicitly says new rules are not retroactive. Shared-map/16-pixel-margin migration and shared-runner migration were not performed.',
'Wooden bow limbs are rigid; string and arrow animate. Carry-to-aim rotation uses the closed round grip without a separate finger regrip.',
'At full draw the existing right elbow section compresses to about 0.33 of its reference projected width. Connected skin and deformation gates pass; artistic review remains pending.',
'The 88-pixel distance silhouette is close to the 0.97 threshold and is scored on the assembled actor. Standalone far bow overlap is about 0.916; native LOD distance/lighting review belongs to integration.',
'Initial primary-image prompts were not retained verbatim; selected images, later exact reference prompts, hashes and all paid Meshy requests/receipts are retained.',
'No engine install, game launch, build, indoor/outdoor capture or cross-world regression was performed, per Batch rules. Native lighting/skin comparison and terrain contact still need orchestration.'
]
summary=f"""# HANDOFF — MM6 LizardArch (`mm6:lzd`)

**Review round 3 technical work complete; artistic acceptance and native integration remain pending.**
Only this project was changed. No commit or assets_dev write. Meshy remains **60 / 100 credits**.

Replace **both** runtime GLBs and merge all three blocks from [integration/actors.yml](integration/actors.yml).
The orchestrator owns installation; earlier installed files are superseded.

| Runtime file | LOD0 / LOD1 / LOD2 / LOD3 triangles | Bytes |
|---|---|---:|
{counts}

Cast uses option **(b)**: an exact named copy of the library bow shot, launching from **Socket_Arrow at 0.734375 s**.
Attack/Cast last **{info['clips']['Cast']:.6f} s**. Recovery alone gains 0.066667 s to remove the source turn's acceleration spike.
Scale **{info['scale']:.9f}**, stride **{info['stride_length_m']:.9f} m**, yaw remains -1.570796327; descriptors 571/572/573.
There are {info['bones']} bones and nine clips. The old right-palm node is inert and is no longer bound.

Review: [viewer](review/viewer/index.html), [round 3 receipt](review/review_round3.json),
[front](review/clips_front.jpg), [side](review/clips_left.jpg), [three-quarter](review/clips_three_quarter.jpg),
[Cast sequence](review/cast_sequence.jpg), [reduction curve and paired views](review/reduction/README.md).
Latest evidence and hashes are in **Review round 3** below. Older sections are historical and do not describe the current exports.

"""
section=f"""
## Review round 3

The vertical carry is solved with the hand closed on the wrap in Standing, Fidget, Walking, Running and Hit.
Bow vertical dot is at least 0.9396 and the string's bodyward dot at least 0.8137; maximum digit-to-wrap distance
is **{grip:.3f} mm** (limit 3 mm). The free right hand stays beside the body, with palm-to-thigh dot
**{motion['clips']['Walking']['free_palm_toward_thigh_min_dot']:.4f} Walking** /
**{motion['clips']['Running']['free_palm_toward_thigh_min_dot']:.4f} Running**.

**Cast choice (b)** uses the sourced 2HandBowAttack1 shot. Cast/Attack channels and {read('review/cast_gate.json')['samplers_checked']} samplers are identical.
This retains the library's wind-up and weight transfer and the user's accepted bow-spell route. All tiers bind Cast and
launch at 0.734375 s from Socket_Arrow. The former palm gesture and palm binding are superseded.
Recovery retimes source frames 23–25 to 23–27, adding two frames while preserving the collision-free pose path,
draw and release interval. The aim grip rolls 120 degrees away from the bow arm, with a 5 mm claw-root adjustment to keep the wrap contact. Thirty fractional keys per string preserve a common nock during draw and snap; the export patch retains keys that the frame-only exporter would omit. The right-arm acceleration peak falls from 50.83 to 21.90 degrees/sample² at 48 Hz;
the wrist peak falls from 51.05 to 22.10. Every clip passes its source-relative acceleration limit.

Feet follow the travel direction, including at rest. Measurements below are from the exported mesh/bones at 48 Hz:

| Clip | Foot | Yaw range (degrees) | Minimum sole (mm) | Peak sole height (cm) |
|---|---|---:|---:|---:|
{yaw}

Walking/Running keep at least one foot within 1 cm of the floor for 100% of sampled frames. Walk swing knees are
about 61.6 degrees; Running swing peaks are about 14.3 cm. The loin flap follows the leading leg to avoid cloth penetration.

### Reduction and rebake

Body **12,987 -> 9,858** triangles; bow **2,236 -> 1,788**. Combined LOD0 falls **23.5%**, to 11,646.
The next authored body step (9,545) fails SSIM at 0.92868; the next bow step (1,564) fails IoU at 0.98687.
Final body minimum IoU is **0.994625**, SSIM **0.96079/0.96098/0.96081** for actual A/B/C cloth tiers.
Final bow minimum IoU/SSIM is **0.996461 / 0.992048**.
[CSV/plot, method and paired renders](review/reduction/README.md) record the stopping boundary.

All levels rebake base colour, region mask, ORM and tangent normals from the unreduced surfaces. UVs are refitted,
not carried through collapse. Face, fingers, collar, joints and prop contacts are protected.
LOD1/2/3 comparisons use the assembled actor at 550/220/88 pixels; runtime pooled IoU is
**{lods['1']['silhouette']['actor']['pooled_iou']:.6f} / {lods['2']['silhouette']['actor']['pooled_iou']:.6f} / {lods['3']['silhouette']['actor']['pooled_iou']:.6f}**.
The far comparison uses paired 64-sample renders; the 16-sample trial (0.969931) is retained in the audit.
Isolated far bow overlap is about 0.916 and is not reported as a standalone pass.
LOD2/3 grip radii gained 3%/8% only around the wrap, preserving UVs, maps and counts. All-clip exported grip gaps are 2.647/2.822 mm.
Export removes 7/21/30 lower-body triangles; all lower runtime meshes were reimported and rechecked on all clips.

### Repeated checks

- The final head checker rejects nearest-face-plane hits outside the struck shoulder component bounds. The former far-LOD 44.3 mm report was outside every component; [the geometric audit](review/rebake/head_plane_audit.json) records the proof. The 10 mm limit is unchanged and all four LODs were rechecked.
- LOD0 G4 arm p99 **{arm:.3f}x**, G5 hand maximum **{hand:.3f}x**; G5 bad distal adjacency **0**.
- Body, held equipment and cloth penetration **0 mm** at LOD0; head contact maximum **{head:.3f} mm**.
- Signed elbow flexion minimum **{flex:.3f} degrees**, plane deviation **{plane:.6f} degrees**, forearm roll <=90 degrees.
- All four runtime colour LODs pass G4/G5/G6, elbow, grip, palm, gait and cloth checks; detailed lower reports include remaining sub-millimetre contacts.
- Ranged event arrow target dot **{release['impact_arrow_target_dot']:.6f}**; held string/finger error **{release['held_nock_finger_distance_max_m']*1000:.3f} mm**; forward string speed at event **{release['nock_forward_component_at_event_m_s']:.3f} m/s**. String junction gap stays below **{joined['max_gap_m']*1000:.3f} mm**, measured at 1920 Hz through draw and release.
- All material extensions and skin weights pass **check_weights.py** and **check_bindings.py**, **no BAD lines**.
- Runtime packaging preserves LOD0 body attributes, rig and animation bytes; Cast copy equality checked.
- Viewer **27/27** tier/clip switches, no failures/console errors; 18 browser captures and all clip/hand/tier sheets refreshed.
- [Skin luminance diagnostic](review/skin_luminance.json) records native and controlled-review mean/p95. The review lighting is brighter than native sprites; no skin darkening or skin tier recolour was added. Native lighting calibration remains integration work.
- All project Python scripts compile. No new paid jobs, game launches, builds, runtime installs or commits.

### Changed files and hashes

These are the current exports and review GLBs. Colour/shadow mesh counts are both shown where present:

| File | SHA-256 | Triangles per mesh |
|---|---|---|
{hashes}

**integration/actors.yml changed: YES**, SHA-256 `{receipt['actors_sha256']}`.
All tiers now use Cast / Socket_Arrow / 0.734375, with no palm binding. Scale and stride reflect the corrected rest height
and gait. The shared registry was not edited. [Regression proposal](integration/regression.md) is updated for bow-cast release,
carry, palms, forward feet and the new LODs.

Authoring/review changes include `scripts/round3_motion.py`, `round3_grip_fit.py`, `smooth_recovery.py`,
the `rebake_*.py` pipeline, `runtime_lod_gates.py`, `angular_acceleration.py`, `volume_contact.py`,
export/validation scripts, rebaked maps, selected Blender checkpoints, clip/browser sheets, README and progress state.
Additional validation measurements are linked from the [round receipt](review/review_round3.json).

### Remaining limits

"""+'\n'.join('- '+x for x in faults)+'\n'
summary=summary.replace('0.734375',f"{info['impact_seconds']:.9f}");section=section.replace('0.734375',f"{info['impact_seconds']:.9f}")
old=(P/'HANDOFF.md').read_text();history=old[old.index('## Review round 1'):].split('## Review round 3')[0]
(P/'HANDOFF.md').write_text(summary+history+section)
if not (R/'README_before_round3.md').exists():(R/'README_before_round3.md').write_text((P/'README.md').read_text())
(P/'README.md').write_text(f"""# MM6 Lizard Archer — current review round 3

Technical batch production is ready for the orchestrator. Artistic acceptance remains pending. [HANDOFF](HANDOFF.md#review-round-3)
contains current hashes, counts, gate numbers and remaining limits. Historical setup is retained in
[the previous README](review/README_before_round3.md); its counts/cast binding are superseded.

- Runtime files: `export/mm6_lzd.glb` and `export/mm6_lzd_bow.glb`. Combined counts: **11,646 / 6,213 / 2,581 / 836**.
- LizardArch A/B/C descriptors 571/572/573; cloth tiers rust/magenta/blue, unchanged green skin and dull steel.
- Upright bow carry with inward string, closed wrap grip; free palm inward beside the thigh; flat forward feet.
- Cast option **(b)**: exact library Attack copy, distinct name, Socket_Arrow at **0.734375 s**. Recovery slowed 67 ms;
  total Attack/Cast **{info['clips']['Cast']:.6f} s**. No palm-right binding.
- Body and bow reduced separately with protected anatomy/contact and four rebaked maps per selected level.
  This round started before the later shared-map/shared-runner rules; per Cost controls item 4 (no retroactive rules),
  the existing per-LOD maps and project gate suite are retained. No claim of shared-map/16-pixel-margin compliance is made.
  [Reduction curve/method](review/reduction/README.md). Distance IoU is on the assembled actor. Far paired renders use 64 samples;
  subpixel isolated-bow failures and the initial 16-sample result remain documented.
- G4/G5/G6, elbows, palms, floor/lift, grip, cloth, source motion and angular acceleration pass all nine clips.
  The exact lower exported meshes were reimported and checked, including faces omitted by the exporter.
- All three tier viewer checks and registry/weight/material checks pass. Native runtime checks are delegated by Batch rules.
- Meshy **60/100** credits, additional this round **0**. No shared files, sprite-restoration source, game install or commit changed.

## Resume checkpoints

Authoritative selected baked meshes/maps: `review/rebake/final_selection.json`, `work/rebake/*_baked.blend`,
`textures/rebake/`. Editable near rig: `work/master.blend`; exact normalized exporter input:
`work/master_export.blend`; reimported runtime geometry: `work/export_reimport.blend` and
`work/rebake/runtime_lod[1-3].blend`. The selected checkpoints already include final recovery timing.

After reclaiming the `mm6:lzd` workspace lease, run sequentially with `tools/run_creature_blender.sh --token TOKEN`:
1. `scripts/export_rebaked.py`: export/rebaked tier packaging, near gates/sheets, acceleration.
2. `scripts/runtime_lod_gates.py`: exact lower runtime topology, all clips, switch-size silhouette comparisons.
3. Guarded ordinary Python: `scripts/post_checks_round3.py` (serve repo on localhost:8919 for viewer checks),
   `scripts/reduction_review.py`, then `scripts/record_round3.py`.
Use `PYTHONPATH=work/python` for the local plotting dependencies if needed. One background Blender, four threads.
The old `package_runtime.py` / geometry intermediate belong to previous rounds; do not use them to regenerate this rebake chain.
Fresh render tags are required if changing geometry: the comparison renderer skips already-existing PNGs.

[Viewer](review/viewer/index.html), [clip sheets](review/clips_front.jpg), [Cast](review/cast_sequence.jpg),
[bindings](integration/actors.yml), [regression](integration/regression.md), [gate receipt](review/gates.json).
""")
f=P/'README.md';f.write_text(f.read_text().replace('0.734375',f"{info['impact_seconds']:.9f}"))
p=read('creature_3d_progress.json');p.update(stage='batch_handoff_ready',substep='review_round_3_complete',status='complete',completed_at=now,exports=runtime['files'],clips=info['clips'],gates={'status':'technical_pass','receipt':'review/gates.json','runtime_lods':'review/rebake/runtime_lod_validation.json','angular_acceleration':'review/angular_acceleration.json'},open_faults=faults,next_action={'owner':'orchestrator','action':'Replace both round 3 runtime GLBs, merge all three staged actor entries, run registry/native indoor/outdoor and shared-world regressions.'},review_round_3={'status':'passed','completed_at':now,'receipt':'review/review_round3.json','runtime_files':runtime['files'],'actors_changed':True,'actors_sha256':receipt['actors_sha256'],'additional_credits':0})
p['decisions']+=['The batch document changed during this already-running round. Cost controls item 4 says new rules are not retroactive; retain existing per-LOD rebakes and project gates.', 'Round 3 uses Cast option b: exact bow Attack copy, arrow socket at 0.734375 s.','Distance reduction IoU measures the assembled body+bow; far paired renders use 64 samples.','Recovery retimes library frames 23–25 over four frames; release remains unchanged.']
p['triangle_budget']={'body_lods':nearbody,'bow_lods':nearbow,'combined_lods':runtime['combined_triangles'],'minimisation_receipt':'review/reduction/README.md'}
p['decisions']=[s.replace('0.734375',f"{info['impact_seconds']:.9f}")for s in p['decisions']]
p['integration']['status']='revised_body_bow_and_bindings_pending_orchestrator'
p['correction_ledger'].append({'finding':'Round 3 carry, cast, free palm, toe-out gait and triangle count feedback','repair':'Vertical carry, exact bow-shot Cast, inward relaxed palm, forward flat feet and rebaked measured LODs','status':'resolved'})
write('creature_3d_progress.json',p)
print('ROUND3_RECORDS_COMPLETE')

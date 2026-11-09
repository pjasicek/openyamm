"""Publish the reviewed assets and the shared runner's unmodified verdict."""
import json,hashlib,shutil,datetime,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1]
# Reuse the existing sheet and skin-statistics writer without reissuing historical reduction claims.
script=P/'scripts/review_assets.py'
exec(compile(script.read_text().split('curves={}')[0],str(script),'exec'),{'__file__':str(script)})
for tier in 'abc':
 shutil.copyfile(P/f'review/viewer/mm6_mer1_{tier}.glb',P/f'export/mm6_mer1_portable_{tier}.glb')
g=json.loads((P/'review/gates/gates.json').read_text());rows=g['gates']
identity=json.loads((P/'review/runtime_geometry_identity.json').read_text());assert identity['pass']
viewer=json.loads((P/'review/viewer_check.json').read_text());assert viewer['ready']=='true'and viewer['switched']==24 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD'not in (P/'review/bindings_check.txt').read_text()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
roles=[('runtime_body','mm6_mer1.glb'),('runtime_club','mm6_mer1_club.glb'),('editable_source','mm6_mer1.blend')]+[(f'portable_{t}',f'mm6_mer1_portable_{t}.glb')for t in 'abc']
artifacts=[]
for role,name in roles:
 f=P/'export'/name;artifacts.append({'role':role,'path':str(f.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
for item in g['assets']:
 if item['asset'] in ['body','club']:
  expected=artifacts[0 if item['asset']=='body'else 1]['sha256'];assert item['sha256']==expected
(P/'export/artifacts.json').write_text(json.dumps({'created_at':now,'revision':'review_round_1','status':'QA HOLD'if g['status']!='PASS'else'REVIEW READY','artifacts':artifacts},indent=2))
open_rows={}
for row in rows:
 if row['status'] not in ['FAIL','UNVERIFIED']:continue
 key=(row['gate'],row.get('clip'),row.get('region'))
 if key not in open_rows or (row['worst']or 0)>(open_rows[key]['worst']or 0):open_rows[key]=row
(P/'review/shared_gate_open_findings.json').write_text(json.dumps({'status':g['status'],'counts':g['counts'],'worst_by_clip_and_region':list(open_rows.values())},indent=2))
def maximum(gate,clip=None,region=None,lod=None):
 values=[r['worst']for r in rows if r['gate']==gate and r['worst']is not None and (clip is None or r['clip']==clip) and (region is None or region in r['region']) and (lod is None or r['lod'].endswith(lod))]
 return max(values)if values else 0
def number(x):return f'{x:.4f}'
counts=g['counts'];levels=identity['levels'];skin=json.loads((P/'review/final_skin_luminance.json').read_text())
atlas=json.loads((P/'review/shared_texture_atlases.json').read_text())
artifact_table='\n'.join(f"| [{a['path']}]({a['path']}) | {a['role']} | {a['sha256']} |"for a in artifacts)
triangle_table='\n'.join(f"| {x['level']} | {x['body_triangles']} | {x['club_triangles']} | {x['body_triangles']+x['club_triangles']} |"for x in levels)
clip_table='\n'.join(f"| {role} | {maximum('arm_stretch_p99',role):.4f} | {maximum('arm_stretch_max',role):.4f} | {maximum('hand_stretch_max',role):.4f} | {maximum('cloth_penetration_mm',role):.3f} | {maximum('rotation_step_deg',role,'Cloak_'):.3f} |"for role in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'])
failure_counts=collections.Counter(r['gate']for r in rows if r['status']=='FAIL')
failure_table='\n'.join(f"| {name} | {n} | {maximum(name):.4f} |"for name,n in failure_counts.most_common())
binding_hash=hashlib.sha256((P/'integration/actors.yml').read_bytes()).hexdigest()
(P/'HANDOFF.md').write_text(f"""# MM6 Merchant — Review round 1 handoff

The requested repair revision is exported and reviewable. **Overall technical QA remains on hold.**
The shared runner returns **{g['status']}: {counts.get('PASS',0)} PASS, {counts.get('FAIL',0)} FAIL,
{counts.get('UNVERIFIED',0)} UNVERIFIED**. Repeated colour/shadow and skeleton rows are included in those counts.
This is not a claim that the full production done criteria pass or that the user accepted the artwork.

**30/100 Meshy credits total; this round cost 0 credits.** No paid jobs pending.
No installation, shared integration edits, builds, game launches or commits were performed.

## Review round 1

1. **Shoulders:** closed both sleeve roots and the small right-sleeve tear. The upper sleeve has a fuller cloth
   volume and corrected smooth normals. Its inner ring is projected 15 mm inside the actual torso surface and
   receives that surface's interpolated skin weights, so it overlaps the body through motion. A gradual
   clavicle-to-original-arm blend preserves forearm weighting. Lower-LOD sleeves receive the repaired near
   surface's weights. The green connecting cloth under the gold trim is modeled geometry, not an empty opening.
2. **Club:** retained the Club attachment node. The handle is belt/hip-carried, with a modeled leather loop, in
   Standing, Walking, Running, Fidget, Hit, Death and Dead. Attack draws over 0.2 seconds and returns over
   0.25 seconds. The parked grip moved to approximately (-0.248, 0.105, 0.910) m before the pelvis transform.
   The standalone club binary is unchanged; the changed socket animation is in the body GLB.
3. **Hands:** replaced the blotchy diffuse islands with consistent skin and softened the noisy normal response.
   Target linear mean is 0.448836 versus native hand mean 0.444972. Final LOD0 measured hand mean:
   {skin['LOD0_hands']['baked']['mean']:.6f}. The low-contrast hand finish no longer reproduces the native
   white highlight percentiles; the previous blanket mean/p90/p95 pass claim is withdrawn.
   [Measured skin values](review/final_skin_luminance.json), [right hand close-up](review/hand_export_R_outer.png).
4. **Running:** replaced RelaxRunForward with local **anim_library/mixamo/Jogging.fbx**. Its upright torso/arm
   cycle is retargeted, with anatomically fitted elbows. The planted 0.8-second leg cycle and 1.302 m stride
   remain matched to walking stride 0.84 m times the engine's 1.55 run multiplier. No paid animation.
5. **Death hem:** resampled and smoothed all 64 cloth joints' rotation and translation channels at 120 Hz;
   old channels were removed before writing the new samples. Dead holds the resulting terminal pose.
   The shared G6 rotation-step check now includes all cloth joints through explicit config aliases.
   Maximum Death cloth-joint step: **{maximum('rotation_step_deg','Death','Cloak_'):.4f} degrees at 48 Hz**.
   The runner has no dedicated cloth vertex/translation acceleration gate; no such numeric pass is claimed.

The sleeve containment config now describes the actual long sleeves: wrists are allowed inside their cuffs
until the opening. It no longer treats them as short-sleeve collision volumes.

[Left shoulder](review/review1_preview_Standing_left.png),
[right shoulder and belt club](review/review1_preview_Standing_right.png),
[Death side](review/review1_preview_Death_right.png),
[running side](review/review1_preview_Running_left.png).

## Exported files and hashes

| File | Role | SHA-256 |
|---|---|---|
{artifact_table}

All runtime body LODs retain the same eight clips, three colour tiers and compatible joint names.
The body and club each have one shared texture set with 16-pixel chart margins.
[Artifact sizes](export/artifacts.json), [atlas receipt](review/shared_texture_atlases.json).

| LOD | Body triangles | Club triangles | Combined |
|---|---:|---:|---:|
{triangle_table}

The closure/loop cost was offset by removing low-curvature interior torso vertices and locally rebaking the
changed triangles using the existing projection helper. Counts do not exceed the previous installed levels.
LOD3 authoring has 952 body triangles; glTF omits one degenerate triangle, leaving 951.
No new reduction search was run. The old IoU/SSIM curves describe the pre-review reduction, not these repairs.
[Local rebake receipt](review/review1_local_rebake.json).

## Checks against this revision

- [Viewer receipt](review/viewer_check.json): 24/24 tier/clip switches, no console errors.
- [Binding receipt](review/bindings_check.txt): exit 0, no BAD line.
- [Runtime identity](review/runtime_geometry_identity.json): geometry/weights preserved by packaging;
  maximum weight-sum error {identity['max_weight_sum_error']:.9g}; unsupported extensions absent;
  all shadow materials OPAQUE.
- [Shared gate report](review/gates/gates.md), [full JSON](review/gates/gates.json):
  **{g['status']}**, with exact input hashes. No new per-creature gate implementation was added.
- Near-model arm p99/max stretch: {maximum('arm_stretch_p99',lod='colour0'):.4f} /
  {maximum('arm_stretch_max',lod='colour0'):.4f}. All-LOD hand maximum: {maximum('hand_stretch_max'):.4f}.
  Elbow out-of-plane maximum: {maximum('elbow_plane_deg'):.4f} degrees.
- [Source motion trace](review/final_source_motion_trace.json) records the current local animation sources.

The table below is the shared runner's worst result over all colour/shadow LODs for each clip.
Arm p99 limit is 2.0, arm/hand maximum limit 4.5, and cloth penetration limit 2 mm.
The hem column reports cloth-joint rotation steps, not a new vertex jitter test.

| Clip | Arm p99 | Arm max | Hand max | Cloth mm | Hem step degrees |
|---|---:|---:|---:|---:|---:|
{clip_table}

## Remaining shared findings

| Gate | Failing rows | Worst reported value |
|---|---:|---:|
{failure_table}

[Deduplicated failures](review/shared_gate_open_findings.json) preserve the offending clip, LOD, region and time.
Four UNVERIFIED rows concern missing weighted right-pinky grip samples on LOD1/2 and their shadows.
Garment and parked-prop reports include folded-hem containment and contact around the belt loop; these are
not silently discarded as false positives. Wrist/upper-arm, palm, grip and foot-yaw findings also remain.
Full technical completion is therefore **false** pending review/further correction.

## Integration and records

**integration/actors.yml changed: comments only.** Its executable binding values are unchanged:
Club attachment node, Running role, stride_length 0.84, impact 0.8125 seconds, Cast alias Attack,
scale 103.841591817, yaw -1.570796327 and z_offset -0.103841592.
Binding file SHA-256: {binding_hash}.
[Staged bindings](integration/actors.yml), [proposed runtime regression](integration/regression.md).

The orchestrator owns installation and game checks. The already-installed previous revision was not touched.
These large PNG atlases still need the orchestrator's runtime memory/mip review; no hardware result is claimed.

[Standing](review/clip_Standing.jpg), [Walking](review/clip_Walking.jpg),
[Running](review/clip_Running.jpg), [Attack](review/clip_Attack.jpg),
[Hit](review/clip_Hit.jpg), [Fidget](review/clip_Fidget.jpg),
[Death](review/clip_Death.jpg), [Dead](review/clip_Dead.jpg).

Resume from work/reduction_master.blend and review/reduction/selection.json.
The packed editable selected source is export/mm6_mer1.blend. Earlier work files and scripts are historical.
The pre-review handoff is preserved at work/review1/HANDOFF.md.
""")
(P/'README.md').write_text(f"""# MM6 Merchant (mer1)

**Review round 1 is staged; overall technical QA remains on hold.**
[HANDOFF.md](HANDOFF.md) contains the current files, hashes, repairs and the full remaining validation findings.
Shared verdict: **{g['status']}**, {counts.get('FAIL',0)} failing and {counts.get('UNVERIFIED',0)} unverified rows.
No artistic acceptance is claimed.

Budget: **30/100 Meshy credits**, with zero additional credits spent in this review.
Only this project was written. The sprite-restoration [mm6_mer1](../mm6_mer1/) remains read-only.
No installation, game launches, builds or commits.

## Current revision and decisions

The two sleeves are closed and joined into the actual torso with an overlapping, torso-weighted cloth root.
Upper sleeves fill the shoulder trim; their arm weights blend through the clavicles while preserving forearm motion.
A visible loop supports the club at the right belt. The Club socket follows the pelvis except during the drawn
Attack, and it stays belt-mounted in Death/Dead as explicitly requested.

Hands use clean, consistent low-contrast skin. This intentionally removes the old blotchy highlight islands;
their mean matches native hands, but native highlight percentiles are no longer claimed as passes.
Running now uses local Mixamo Jogging.fbx; RelaxRunForward is rejected. The planted 0.8-second,
1.302 m stride remains matched to the binding. Death cloth translation/rotation is smoothed and Dead is its held
terminal frame. Shared angular-step coverage includes all 64 cloth joints; the runner has no vertex-acceleration test.

Merchant A/B/C are ids 577/578/579. Preserve the stocky native build, grey cap, blue collar,
green/blue/red coat, brown trim, belt pouch and wooden club.
Eight clips use the local Mixamo/humanoid library; Cast aliases Attack because this NPC has no spells.
The separate carefully modeled [club design](references_hd/club_design.png) and texture are retained.

Runtime body LODs: 9546 / 2420 / 2384 / 951 triangles; club: 1122 / 290 / 252 / 200.
Counts stay within the installed revision. New closure/loop triangles replace interior torso triangles;
changed torso faces were locally rebaked. Historical reduction curves are not new validation of this repair.
There is one shared texture set per object, with 16-pixel dilated margins:
body 2048x6912 (four maps), club 2048x2816 (three maps). Runtime memory/mips remain an integration check.

## Review and resume

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html):
24/24 switches pass. [Bindings](integration/actors.yml) pass with no BAD line; only their comments changed.
The [shared report](review/gates/gates.md) remains authoritative and has unresolved findings.

Authoritative sources: work/reduction_master.blend and review/reduction/selection.json.
Editable delivery: export/mm6_mer1.blend.
Assembly: export_selected.py, package_runtime.py, share_lod_atlas.py, prepare_viewer.py.
The review1_* scripts record the repair sequence; do not restart from historical motion or geometry scripts.
Meshy receipts and selected artifact hashes are in creature_3d_progress.json.
""")
notes=P/'integration/playbook_notes.md'
notes.write_text(notes.read_text()+"""
## Review round 1

- A shrunken sleeve-root cap can remain visibly recessed. Project the inner ring into the actual torso,
  transfer its surface weights, and fill the shoulder volume; inspect both sides and Death.
- Keep the original forearm weighting. A hard spatial cutoff in a shoulder-only weight replacement produces
  short, highly stretched transition edges. A clavicle blend and near-surface transfer are more stable.
- Hanging equipment needs a modeled belt loop and a pelvis socket. It should not receive arbitrary outward/backward offsets.
- Use Mixamo Jogging, never RelaxRunForward. Preserve fitted stride and recheck source-frame elbows.
- Smooth every cloth rotation/translation channel, remove old keys, and refresh the held Dead pose.
- The shared runner can include cloth joints in its helper rotation-step coverage through explicit bone aliases.
  This is not a cloth vertex or translation acceleration gate. Keep its remaining failures visible.
- Report actual exported triangles: Blender can omit a degenerate authored triangle.
""")
reduction=P/'review/reduction/README.md'
text=reduction.read_text()
if not text.startswith('# Historical reduction evidence'):
 reduction.write_text('# Historical reduction evidence — before review round 1\n\nCurrent repair counts and evidence are in [HANDOFF.md](../../HANDOFF.md). The following IoU/SSIM curves predate the sleeve/loop repairs and local torso rebakes; they are not rerun results.\n\n'+text)
state=P/'creature_3d_progress.json';d=json.loads(state.read_text())
d.update(stage='handoff',current_stage='handoff',substep='review_round_1_with_open_qa',status='handoff_with_open_qa',technical_completion=False,user_acceptance='not_recorded',selected_artifacts=artifacts)
d['review_round_1']={'completed_at':now,'repairs_staged':True,'additional_credits':0,'gate_status':g['status'],'gate_counts':counts,'viewer_switches':24,'bindings_pass':True,'integration_yaml_changed':'comments only','source_running':'anim_library/mixamo/Jogging.fbx','runtime_installation':False}
d['handoff']={'path':'HANDOFF.md','integration_applied':False,'runtime_checks_run':False,'committed':False,'budget_credits':100,'spent_credits':30}
state.write_text(json.dumps(d,indent=2))
source=Path('/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/5707d78c-82f0-4aec-b463-6fc01c03b6f9/images')
dest=P/'review/user_round1';dest.mkdir(exist_ok=True)
for i in range(64,69):
 if (source/f'{i}.png').exists():shutil.copyfile(source/f'{i}.png',dest/f'{i}.png')
print(json.dumps({'gate_status':g['status'],'counts':counts,'artifacts':artifacts,'handoff':'HANDOFF.md'},indent=2))

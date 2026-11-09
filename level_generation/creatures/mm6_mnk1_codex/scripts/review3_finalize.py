import json,hashlib,shutil,datetime
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round3'
def read(f):return json.loads((p/f).read_text())
def sha(f):return hashlib.sha256((p/f).read_bytes()).hexdigest()
def write(f,d):(p/f).write_text(json.dumps(d,indent=2)+'\n')
runtime=read('review/runtime_validation.json');dense=read('work/gates_dense.json');contacts=read('work/g6_contacts.json');coverage=read('work/review1_occlusion.json');pen=read('review/round3/penetration.json');elbows=read('review/round3/elbows.json');cloth=read('review/round3/cloth_metrics.json');parity=read('review/export_parity.json');trace=read('review/export_trace.json');lod=read('review/round3/reduction/lod_metrics.json');viewer=read('review/round3/viewer_check.json');playback=read('review/playback/playback.json')
assert runtime['pass'] and runtime['sha256']==sha('export/mm6_mnk1.glb')
assert all(v['G4_pass'] and v['G5_pass'] for v in dense.values())
assert all(v[0]<=.2 for c in contacts.values() for v in c.values())
assert all(v['pass'] for v in coverage.values()) and all(v['pass'] for v in pen['clips'].values())
assert pen['input_sha256']==sha('export/mm6_mnk1.blend')
assert elbows['pass'] and cloth['pass'] and parity['pass'] and trace['flags']==0 and lod['pass']
assert viewer['runtime_sha256']==runtime['sha256'] and viewer['ready']=='true'
assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert len(playback)==18 and all(len(v['frames'])==5 for v in playback)
assert 'BAD' not in (out/'check_bindings.txt').read_text()
assert (p/'integration/actors.yml').read_bytes()==(out/'before/integration/actors.yml').read_bytes()
assert all(sha(f)==v['sha256'] for f,v in read('review/round2/receipt.json')['files'].items() if f.startswith('textures/'))
for src,dst in [('work/gates_dense.json','rig_gates.json'),('work/g6_contacts.json','contacts.json'),('work/review1_occlusion.json','master_coverage.json'),('review/review1_runtime_occlusion.json','runtime_coverage.json'),('review/runtime_validation.json','skin_weights.json')]:shutil.copy2(p/src,out/dst)
g4=max(v['stretch'][s+'_arm']['p99'] for v in dense.values() for s in 'LR');g5=max(v['stretch'][s+'_hand']['max'] for v in dense.values() for s in 'LR');ground=min(v['min_floor_m'] for v in dense.values())*1000;paritymm=max(v['max_surface_error_m'] for v in parity['clips'].values())*1000
tri=runtime['colour_lod_triangles'];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
files=['export/mm6_mnk1.glb','export/mm6_mnk1.blend','export/mm6_mnk1_lod0.glb','review/viewer/mm6_mnk1_a.glb','review/viewer/mm6_mnk1_b.glb','review/viewer/mm6_mnk1_c.glb','textures/mnk1_basecolor_2k.png','integration/actors.yml']
filetable='\n'.join(f"| [{f}]({f}) | {sha(f)} |" for f in files)
rows=[]
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 d=dense[name];q=pen['clips'][name]
 rows.append(f"| {name} | {q['samples_48hz']} | {q['sleeves']['worst_penetration_mm']:.3f} | {q['robe']['worst_penetration_mm']:.3f} | {max(d['stretch'][s+'_arm']['p99'] for s in 'LR'):.3f} | {max(d['stretch'][s+'_hand']['max'] for s in 'LR'):.3f} | {max([v[0]*10 for v in contacts[name].values()]+[0]):.3f} |")
gatetable='\n'.join(rows);lodrows=[]
for level,pixels in [(1,500),(2,200),(3,80)]:
 values=[v for k,v in lod['views'].items() if k.startswith(f'lod{level}_')]
 lodrows.append(f"| {level} | {tri[level]} | {pixels} | {min(v['silhouette_iou'] for v in values):.6f} | {min(v['foreground_ssim'] for v in values):.6f} |")
lodtable='\n'.join(lodrows)
handoff=f"""# MM6 BMonk (mnk1) — technical handoff

**Review round 3 complete for batch handoff.** User artistic acceptance and native game review remain pending. Meshy **20/100 credits total; zero new credits this round**. No commit, installation, shared-file edit, build or game launch.

## Review round 3

The user reported wrists passing through sleeve fabric during Attack and a foot piercing the Walking robe. The previous revision is frozen in [review/round3/before/](review/round3/before/).

- Added forearm-parented cuff controls. Distal cuffs retract 10 cm before palm release, so wrists leave through the openings. The two sleeves and symmetric, fully covered rest pose are retained.
- Weighted lower robe strips to thighs, calves and feet. Removed always-covered upper boot shafts and fitted the remaining shoes, hem and waist. Walking/Running use planted IK with 8.55–8.58 cm swing clearance.
- Kept the library Death torso and duration; planted the feet apart and stepped them back during the fall. Cloth-only leg controls keep the skirt above the floor.
- Corrected anatomical elbow hinge frames, retaining cloth and hand world transforms through cloth support bones. Smoothed a short Cast transition while preserving its 0.45 s release and 1.0 s duration; [timing map](work/review3_cast_timing.json).
- Re-exported and calibrated the LOD chain. Further LOD0 reduction was rejected by contact and texture comparisons below. **Canonical textures and palette ramps remain byte-identical to round 2.**

**integration/actors.yml changed: no.** SHA256: {sha('integration/actors.yml')}. IDs, scale, yaw, sockets and event times are unchanged. Nothing was copied to assets_dev.

Runtime: **{runtime['bytes']:,} bytes**, **{runtime['skin_joints']} joints**, up to eight influences, nine clips at 60 fps. Colour/shadow LOD triangles: **{' / '.join(map(str,tri))}**, versus round 2's 12427 / 6212 / 2235 / 744. The master and each viewer tier have {tri[0]} triangles.

| File | SHA256 |
|---|---|
{filetable}

Animation SHA256: {runtime['animation_sha256']}. Full file hashes and changed implementation: [round-3 receipt](review/round3/receipt.json). The primary repair scripts are review3_sleeves.py, review3_leg_weights.py, review3_walk_lift.py, review3_death_feet.py, review3_floor.py, review3_arm_frames.py and review3_cast_timing.py under scripts/. Gates, exports, build_lods.py, manifests and review composition were refreshed.

## Gates

| Clip | Samples at 48 Hz | Sleeve mm | Robe mm | G4 arm p99 | G5 hand max | G6 contact mm |
|---|---:|---:|---:|---:|---:|---:|
{gatetable}

[Signed-distance evidence](review/round3/penetration.json) tests every hand/wrist and remaining boot vertex against closed animated cloth volumes, with 0.01 mm arithmetic tolerance. Exits are allowed beyond the actual sleeve opening plane or through/below the animated robe hem. All nine clips have zero invalid vertices; hidden upper boot geometry was removed as permitted.

This gate runs on the **selected exported Blender master**. The actual runtime preserves LOD0 geometry and animation buffers, with maximum sampled surface error **{paritymm:.4f} mm** at 60 Hz (limit 0.1 mm). Exported Standing coverage is checked independently. Signed-distance sampling was not repeated directly on each simplified LOD.

Standing has **zero visible hand vertices** in 121 samples at 60 Hz, from 26 directions: 1828 master skin vertices and 2586 exported vertices including UV duplicates. Full rest clips and covered Attack/Cast endpoints also pass. Forearm level error: **{coverage['Standing']['max_forearm_level_error_mm']:.4f} mm**.

All elbow samples pass at 48 Hz: flexion −5° to 150°, axial forearm roll ±90°, out-of-plane limit 5°. Maximum out-of-plane error: **{max(v['out_of_plane_max_deg'] for row in elbows['clips'].values() for v in row.values()):.4f}°**. Walking/Running knee peaks are 61.4° / 58.2°; lowest sampled soles are 0.49 / 0.48 mm above ground. Standing/Fidget soles remain within 1 cm. Running retains the existing Walking alias.

Dense maxima: **G4 {g4:.6f} ≤ 2, G5 {g5:.6f} ≤ 4.5, G6 0 mm ≤ 2 mm**. Minimum mesh height at 60 Hz is **+{ground:.4f} mm**. Export rotation trace: zero flags. All {tri[0]} UV triangles are finite, bounded and non-degenerate. Every runtime colour/shadow primitive passes weights; max sum error **{runtime['max_weight_error']:.3g}**. check_bindings.py exits 0 with **no BAD line**.

Sleeve/torso density: **611.315 / 609.718 px/m**, ratio **1.002620**. Luminance ratios: **1.002915 sRGB / 0.995645 linear**. Sleeve UV anisotropy p95: **1.319**. [Cloth metrics](review/round3/cloth_metrics.json).

Evidence: [rig](review/round3/rig_gates.json), [contacts](review/round3/contacts.json), [elbows](review/round3/elbows.json), [locomotion](review/round3/locomotion.json), [master coverage](review/round3/master_coverage.json), [runtime coverage](review/round3/runtime_coverage.json), [weights](review/round3/skin_weights.json), [bindings](review/round3/check_bindings.txt), [parity](review/export_parity.json), [trace](review/export_trace.json).

## Reduction and LOD calibration

Protected planar dissolve/collapse retained hands, deformation regions, boundaries and silhouette edges from eight directions. The **11678**-triangle trial passed G4/G5/G6 and silhouette IoU (minimum **0.997756**). Fresh UVs and component-isolated rebakes of base colour, region mask, ORM and tangent normals introduced visible colour blemishes and lost weave detail: minimum foreground SSIM **0.846786**, below 0.95. The **10564**-triangle trial failed Death contact, up to **49.9 mm**. More aggressive collapse stopped at the same triangle count under the protection mask. The selected **12364**-triangle mesh is the last accepted LOD0 result; rejected geometry and rebakes are not selected.

[Reduction curve](review/round3/reduction/curve.json) · [eight-view comparison](review/round3/reduction/comparison.png) · [visual metrics](review/round3/reduction/visual_metrics.json) · [bake settings](review/round3/reduction/rebaked/bake.json).

The original 50%/18%/6% chain failed the visual thresholds. The fitted chain passes IoU ≥ 0.99 and foreground SSIM ≥ 0.95 in eight views with the native tier material. It retains more distant geometry than the old chain; native performance checks belong to the orchestrator.

| LOD | Triangles | Actor height px | Minimum IoU | Minimum SSIM |
|---|---:|---:|---:|---:|
{lodtable}

[LOD calibration](review/round3/reduction/lod_metrics.json) · [LOD comparison](review/lod_comparison.png). Tests use the 500/200/80 pixel actor thresholds in engine/render/ModelLod.h. The engine also applies hysteresis; corpse stand-in thresholds are separate.

## Review evidence

[Viewer](review/viewer/index.html) · [before/after](review/round3/before_after.png) · [close-ups](review/round3/closeups.png).

Sleeves: [Standing front](review/round3/standing_front.png), [side](review/round3/standing_left.png), [three-quarter](review/round3/standing_quarter.png), [Attack front](review/round3/attack_palms.png), [Attack side](review/round3/attack_side.png), [Cast](review/round3/cast_front.png).
Robe: [Walking front](review/round3/walking_front.png), [side](review/round3/walking_side.png), [three-quarter](review/round3/walking_quarter.png), [Death](review/round3/death_final.png).

All clips: [front](review/clips_front.png), [side](review/clips_left.png), [three-quarter](review/clips_three_quarter.png). [Tiers](review/tier_comparison.png) · [normal playback](review/playback_normal.png) · [half-speed playback](review/playback_slow.png).

Viewer: **27/27 switches**, zero failures and console errors. Browser playback covers nine clips at 1× and ½×: 18 runs, 90 captures. [Playback record](review/playback/playback.json). Agent inspection confirms covered rest hands, wrists through openings and feet below the walking hem. This is technical/agent review, not user artistic acceptance.

## Integration and remaining work

No failing selected-asset gate remains. The orchestrator replaces worlds/mm6/models/mm6_mnk1.glb with [export/mm6_mnk1.glb](export/mm6_mnk1.glb), retaining [integration/actors.yml](integration/actors.yml), then runs [integration/regression.md](integration/regression.md) and indoor/outdoor captures. Installation, builds, game launches and regression execution remain deferred under batch rules.

BMonk A/B/C IDs **583/584/585**, scale **105.142549**, yaw **−1.570796327**, stride **1.57**, run→Walking. Sockets: Socket_Palm_Left/Right. Releases: **Attack 0.716667 s**, **Cast 0.450000 s**. Regression proposal: mm6_bmonk_actor_model_tiers_share_one_size, 6d07.blv, height 162–198, tier difference ≤1 game unit; outdoor oute3.odm.

## Review round 2

The tapered sleeves, overlap and matched weave are retained. [Archived round-2 handoff](review/round3/before/HANDOFF.md). Its penetration defects are superseded by round 3.

## Review round 1

Covered level hands and corrected hand colour are retained. The original muff shape was superseded by round 2. [Archived round-1 handoff](review/round2/before/HANDOFF.md).
"""
(p/'HANDOFF.md').write_text(handoff)
(p/'README.md').write_text(f"""# MM6 BMonk — mnk1

**Review round 3: technical batch handoff ready; artistic review pending.** [HANDOFF.md](HANDOFF.md) contains hashes, gates and integration instructions.

Wrists now exit through the sleeve openings. The robe follows the moving legs, with hidden upper boot geometry removed. Covered symmetric rest hands, two sleeves, colours and palm releases are retained. All nine clips pass the 48 Hz penetration gate; bindings and viewer checks pass.

- [Runtime](export/mm6_mnk1.glb): SHA256 {runtime['sha256']}; {runtime['bytes']:,} bytes.
- [Master](export/mm6_mnk1.blend): {runtime['skin_joints']} joints; nine clips; 60 fps export.
- Colour/shadow LOD triangles: **{' / '.join(map(str,tri))}**.
- [Before/after](review/round3/before_after.png), [close-ups](review/round3/closeups.png), [viewer](review/viewer/index.html).
- [Actors](integration/actors.yml) unchanged. **20/100 credits**, zero new this round. No install, build, game launch or commit.

Unattended decisions: retain the existing colours and tiled weave; reject rebakes that visibly change them; use retracting forearm cuffs, leg-driven robe strips, planted feet during the library fall, and a local Cast timing correction preserving release/duration. The LODs are calibrated at actual actor switch sizes. Running remains the existing Walking alias.

Rebuild with scripts/review3_build.py, review3_export.py, package_runtime.py prepare, build_lods.py, package_runtime.py final, refresh_manifest.py, validate_glb.py and review3_render.py. Use the workspace lease and shared Blender wrapper, one process at --threads 4. Reduction trials are separate evidence; do not replace the selected master or textures with them. The frozen source is [review/round3/before/](review/round3/before/); the sprite-restore project is read-only.

The orchestrator owns installation, regression and native captures. User artistic acceptance remains pending.
""")
progress=read('creature_3d_progress.json');progress.update(status='complete',stage='review_round_3_handoff',current_stage='review_round_3_handoff',updated_at=now,technical_completion=True,technical_complete=True,artistic_acceptance=False,runtime_validation=runtime,open_technical_faults=[],next_action_owner='orchestrator',next_action='Install selected runtime, execute regression and native captures, obtain user artistic review.')
progress['selected_artifacts']=[{'role':'runtime_body','path':'export/mm6_mnk1.glb','sha256':runtime['sha256'],'master':'export/mm6_mnk1.blend','master_sha256':sha('export/mm6_mnk1.blend'),'revision':'mm6_mnk1_codex_review3'}]
progress['user_acceptance']={'round':3,'status':'revised_pending_user_review'}
progress['rig_gate_evidence']={'dense':'review/round3/rig_gates.json','contacts':'review/round3/contacts.json','G4':g4,'G5':g5,'G6_mm':0,'minimum_surface_height_mm':ground,'export_parity_max_mm':paritymm,'export_trace_flags':0,'covered_hands':'review/round3/master_coverage.json','runtime_covered_hands':'review/round3/runtime_coverage.json','cloth':'review/round3/cloth_metrics.json','penetration_48hz':'review/round3/penetration.json','elbows_48hz':'review/round3/elbows.json','locomotion':'review/round3/locomotion.json','skin_weights':'review/round3/skin_weights.json','lod_calibration':'review/round3/reduction/lod_metrics.json'}
progress['review_round_2'].update(status='superseded_by_round_3',handoff='review/round3/before/HANDOFF.md');progress['review_round_1']['handoff']='review/round2/before/HANDOFF.md'
progress['review_round_3']={'status':'technical_complete_pending_user_review','new_credits':0,'integration_actors_changed':False,'runtime_sha256':runtime['sha256'],'standing_visible_hand_vertices':0,'all_clip_penetration_mm':0,'receipt':'review/round3/receipt.json','handoff':'HANDOFF.md'}
progress['viewer_validation']={'switches':27,'failures':0,'console_errors':0,'normal_and_slow_playback_clips':9,'playback_runs':18,'captures':90}
progress['artistic_review_points']=['Revised wrist exits and hem await user review.','Native lighting, pacing and LOD performance await orchestrator integration.']
progress['correction_ledger']=[x for x in progress['correction_ledger'] if x.get('stage')!='review_round_3']+[{'stage':'review_round_3','issue':'Wrists crossed sleeve walls; feet pierced the moving robe.','fix':'Forearm cuff controls, leg-weighted robe, boot trim, fitted gait/fall, elbow frames, Cast transition timing and calibrated LODs.','evidence':'review/round3/receipt.json'}]
progress['substeps']['review_round_3']={'status':'complete','evidence':'review/round3/receipt.json'};write('creature_3d_progress.json',progress)
feedback=read('review/viewer/feedback/user_feedback.json')
for row in feedback['findings']:row.update(resolution_revision='mm6_mnk1_codex_review3',resolution_model_sha256=runtime['sha256'],status='revised_pending_user_review')
feedback['findings']=[x for x in feedback['findings'] if x['id']!='R3']+[{'id':'R3','region':'Sleeves and robe hem','user_quote':'monk feedback - [Image #27] - hands comint out through the sleeves fabric, walking [Image #28] - feet peeking through fabric','observed':'Cuff controls and leg-driven robe eliminate invalid cloth exits at 48 Hz; covered rest and colours retained.','evidence':['../round3/closeups.png','../round3/penetration.json'],'resolution_revision':'mm6_mnk1_codex_review3','resolution_model_sha256':runtime['sha256'],'status':'revised_pending_user_review'}];write('review/viewer/feedback/user_feedback.json',feedback)
write('review/final_audit.json',{'revision':'mm6_mnk1_codex_review3','created_at':now,'runtime_sha256':runtime['sha256'],'master_sha256':sha('export/mm6_mnk1.blend'),'technical_complete':True,'artistic_accepted':False,'G4_max':g4,'G5_max':g5,'G6_mm':0,'sleeve_and_robe_invalid_vertices':0,'penetration_sample_hz':48,'runtime_weights_max_error':runtime['max_weight_error'],'viewer_switches':27,'playback_runs':18,'integration_actors_changed':False,'credits_total':20,'credits_new':0,'batch_deferrals':progress['batch_deferrals']})
selected=set(files+['README.md','HANDOFF.md','creature_3d_progress.json','review/final_audit.json','review/runtime_validation.json','review/export_parity.json','review/export_trace.json','review/uv_validation.json','export/clip_manifest.json','export/export_info.json','export/lods.json','review/viewer/manifest.json','review/viewer/feedback/user_feedback.json','review/playback/playback.json','scripts/build_lods.py','scripts/gates_dense.py','scripts/refresh_manifest.py','scripts/compose_final.py'])
for pattern in ['scripts/review3_*.py','work/review3_*.json','review/round3/**/*.json','review/round3/**/*.png','review/final_frames/*.png','review/playback/*.png','review/round3/*.txt','review/clips_*.png','review/playback_*.png','review/tier_comparison.png','review/lod_comparison.png','textures/*']:
 selected.update(str(f.relative_to(p)) for f in p.glob(pattern) if f.is_file() and '/before/' not in str(f) and f.name!='receipt.json')
write('review/round3/receipt.json',{'revision':'mm6_mnk1_codex_review3','created_at':now,'runtime_sha256':runtime['sha256'],'animation_sha256':runtime['animation_sha256'],'colour_and_shadow_lod_triangles':tri,'integration_actors_changed':False,'meshy_new_credits':0,'files':{f:{'sha256':sha(f),'bytes':(p/f).stat().st_size} for f in sorted(selected)}})
print('HANDOFF',runtime['sha256'],tri,'receipt files',len(selected))

"""Record the requested review scope and disclose unchanged shared-gate failures."""
import sys,json,hashlib,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round6';E=P/'export'
sys.dont_write_bytecode=True;runpy.run_path(str(P/'scripts/verify_r6.py'),run_name='__main__')
proof=json.loads((R/'artifact_parity.json').read_text());g=json.loads((R/'final/gates.json').read_text());old=json.loads((R/'baseline/gates.json').read_text());j=json.loads((R/'running_jitter.json').read_text());steel=json.loads((R/'steel_luminance.json').read_text());viewer=json.loads((R/'viewer_check.json').read_text());assert viewer['switched']==24 and not viewer['failed'];assert 'BAD' not in (R/'bindings_check.txt').read_text()
assert all(x['status']=='PASS'for x in j['after']['shared_angular_jitter'])
def metric(gate,lod=0):
 v=[x['worst']for x in g['gates']if x['lod']==f'FighterChain/colour{lod}'and x['gate']==gate and x['worst']is not None];return max(v)if v else None
source=P.parents[2]/'anim_library/mixamo/Standard Run.fbx';sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
counts={n:proof[n]['triangles'][:4]for n in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb']}
files={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in [E/n for n in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb','mm6_figc_lod0.glb','mm6_figc_portable.glb','mm6_figc_authoring.blend']]}
artifact=json.loads((E/'artifacts.json').read_text());artifact.update(date='2026-10-13',revision='review_round_6',files=files,technical_completion=False);artifact['clips_seconds']['Running']=22/30;artifact['triangles']=counts;(E/'artifacts.json').write_text(json.dumps(artifact,indent=2))
limits=['Inherited grip gaps, shield grip penetration and palm axes remain above shared thresholds; accepted grip geometry preserved.','Generic pelvis >= 0.9 m threshold fails on the fitted run (minimum 0.793 m).','Distant sole sampling retains yaw failures and lacks a usable left heel/toe separation on LOD3; shadow LOD1/2 contact is below 80%.','Existing LOD ratio and historical distant silhouette limits remain; no geometry changed.','The shared runner has angular jitter gates but no positional acceleration threshold; 48 Hz positional series are diagnostics.','Native game integration/captures are owned by the orchestrator.']
summary={'revision':'review_round_6','scope':'Running plus body/axe steel ramp and matte ORM mask','source':str(source.relative_to(P.parents[2])),'source_sha256':sourcehash,'duration_s':22/30,'stride_length_m':1.2,'run_stride_m':1.86,'loop_endpoint_exact':True,'geometry_and_seven_other_clips_identical':True,'actors_yml_changed':False,'shield_byte_identical':True,'triangles':counts,'shared_gates':g['counts'],'shared_verdict':g['status'],'technical_completion':False,'open_limits':limits,'credits_used':30,'round_credits':0,'viewer_switches':24,'bindings_BAD_lines':0,'contact_percent':[metric('running_contact_pct',i)for i in range(4)]}
(R/'final_validation.json').write_text(json.dumps(summary,indent=2));progress=json.loads((P/'creature_3d_progress.json').read_text());progress.update(stage='review_round_6_handoff',review_round_6=summary,technical_completion=False,open_limits=limits);progress['motion_sources']['Running']='Mixamo Standard Run.fbx, source frames 0–22; smooth 12 mm bob, foot IK';progress['completed_at']='2026-10-13';progress['status']='handoff_with_open_faults';progress['user_acceptance']='Accepted geometry and other clips retained; round-6 run/steel pending user review';progress['next_action']={'owner':'orchestrator','action':'Review round-6 run and mid-grey steel; integrate staged body/axe exports. Shield and actors.yml unchanged.'};progress['exports']={'manifest':'export/artifacts.json','files':files,'lod_triangles':counts,'combined_lod_triangles':[8921,4676,2224,858]};progress['gates']={'shared_scope':'Running','shared_verdict':g['status'],'counts':g['counts'],'report':'review/round6/final/gates.md','jitter':'review/round6/running_jitter.json','artifact_parity':'review/round6/artifact_parity.json','bindings':'review/round6/bindings_check.txt','viewer':'review/round6/viewer_check.json','viewer_switches_passed':24};progress['review']={'sheets':[f'review/final_{v}.png' for v in ['front','left','three_quarter']],'round':'review/round6/README.md','final_viewer':'review/viewer/index.html','artistic_acceptance':'round_6_pending'};(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2))
rows='\n'.join(f'| {i} | {metric("running_contact_pct",i):.2f}% | {metric("running_airborne_mm",i):.3f} | {metric("floor_penetration_mm",i):.3f} | {metric("arm_stretch_max",i):.3f} / {metric("hand_stretch_max",i):.3f} |'for i in range(4))
hashes='\n'.join(f'| export/{n} | {v["bytes"]} | `{v["sha256"]}` |'for n,v in files.items())
jrows='\n'.join(f'| {n} | {j["before"]["vertical"][n]["max_abs_velocity_m_s"]:.3f} → {j["after"]["vertical"][n]["max_abs_velocity_m_s"]:.3f} | {j["before"]["vertical"][n]["max_abs_acceleration_m_s2"]:.3f} → {j["after"]["vertical"][n]["max_abs_acceleration_m_s2"]:.3f} |'for n in ['B_Pelvis','B_Head'])
colrows='\n'.join(f'| {name} | '+ ' | '.join(f'{steel["materials"][name][s]["srgb_mean"]:.3f} / {steel["materials"][name][s]["srgb_p50_p90_p95"][2]:.3f}'for s in ['round1','current','new'])+' |'for name in ['mm6_figc.glb','mm6_figc_axe.glb'])
text=f'''# FighterChain handoff — review round 6

## Review round 6

Changed **Running** and the **body/axe steel appearance** only. Runtime body and axe exports need orchestrator replacement. Geometry, UVs, weights, normal/base/mask image pixels, tier cloth ramps, nodes and seven other animation payloads are identical to the accepted round-5 package. The shield GLB is byte-identical. **integration/actors.yml did not change**, SHA-256 `888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b`. [Exact parity and storage proof](review/round6/artifact_parity.json).

No new paid generation: **0 this round; 30/100 credits total**. No game, build, install or commit. This is the requested scoped review delivery with disclosed inherited failures, not a full shared-gate PASS claim.

### Running clip: Standard Run

Source: `anim_library/mixamo/Standard Run.fbx`, SHA-256 `{sourcehash}`. Existing rest-delta retarget path, source frames 0–22 at 30 fps, **0.733333 s** seamless loop, baked at 120 Hz. Stride binding stays **1.2 m**, corresponding to **1.86 m** at the runtime 1.55× running multiplier (nominal cycle speed 2.536 m/s). Neither Jogging nor RelaxRunForward is used.

The old per-leg pelvis lowering and subsequent per-frame root floor snap caused the height jerk. The new pelvis follows one analytic 12 mm-amplitude sinusoid, two symmetric bobs per cycle, at a constant feasible baseline. Legs solve to that curve. Sole orientation/height is fitted against shipped mesh samples, with no subsequent root snapping. Source torso/arm motion is periodically smoothed, loop endpoint equals start exactly, feet travel linearly backwards in stance (48% per foot) and use a smooth swing/recovery. The axe-carry rotation is distributed over forearm, twist helper and wrist; both props move with their arms and clear the body.

[Front](review/round6/running_front.png), [side](review/round6/running_left.png), [three-quarter](review/round6/running_three_quarter.png), [viewer frames 4](review/round6/viewer/running4.png) / [8](review/round6/viewer/running8.png), [motion fit](review/round6/motion_fit.json), [48 Hz curves](review/round6/vertical_motion.png).

| Bone | Max vertical velocity, before → after, m/s | Max vertical acceleration, before → after, m/s² |
|---|---:|---:|
{jrows}

All reused shared torso angular-jitter rows pass. The existing runner has **no positional velocity/acceleration gate**; those measurements are diagnostics, not a newly invented pass gate. [Complete jitter series](review/round6/running_jitter.json). All Running channels close exactly; the other seven clips remain byte-identical.

| Colour LOD | Contact | Peak lowest sole, mm | Worst floor penetration, mm | Max arm / hand stretch |
|---|---:|---:|---:|---:|
{rows}

All colour LODs pass contact, floor and stretch checks. Arm/wrist angular jitter, elbow plane/flexion, forearm/wrist roll and prop/body clearance pass. LOD0 trunk lean stays within {metric('trunk_lean_deg'):.2f}°. The lowest foot remains within {metric('running_airborne_mm'):.2f} mm of the floor. Contact complement at LOD0 is {100-metric('running_contact_pct'):.2f}% of the cycle (the gate defines contact as ≤10 mm, so this is not literal zero-contact flight time).

Shared Running verdict: **{old['status']} → {g['status']}**, FAIL rows **{old['counts']['FAIL']} → {g['counts']['FAIL']}**, final counts **{g['counts']}**. [Final shared report](review/round6/final/gates.md). Remaining failures: accepted finger gaps (axe middle 5.243 mm; shield ring 4.693 mm), shield penetration 7.691 mm, palm axes, generic pelvis minimum 0.9 m versus fitted minimum 0.793 m, distant yaw/sole sampling, shadow LOD1/2 contact (71.59% / 65.91%), and existing LOD ratios. No thresholds were relaxed. Attack and its blade/blow timing are unchanged; the round-6 runner is scoped to Running.

### Mid-grey matte steel

Body and axe steel use the **sRGB midpoint** between archived round-1 and current steel ramps, evaluated at matching source luminance. The same steel ramp applies to all three tiers of each model; existing painted texture detail is retained. Steel ORM red (specular mask) is capped at 32/255 and green (roughness) raised to at least 220/255, blended by the existing steel mask. Metallic factor remains zero. High roughness implements the requested matte/no-shine appearance; lowering roughness would make it glossier.

[Round 1 / current / new front](review/round6/steel_comparison_front.png), [three-quarter](review/round6/steel_comparison_three_quarter.png), [axe close-up](review/round6/axe_steel_comparison.png). These isolate the three palettes on identical accepted geometry and lighting; the shield is unchanged in every column. [Numeric native comparison](review/round6/steel_luminance.json) uses the recorded 2233 native armor pixels and core atlas-mask texels, not viewer lighting or surface-area averages.

| Material | Round 1 mean / P95 sRGB | Current mean / P95 | New mean / P95 |
|---|---:|---:|---:|
{colrows}

Native steel mean / P95: **{steel['native']['srgb_mean']:.3f} / {steel['native']['srgb_p50_p90_p95'][2]:.3f}**. Linear mean and P50/P90/P95 are also recorded. Shield appearance remains accepted and untouched.

### Files and checks

Triangle counts are unchanged:

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 6797 | 3610 | 1725 | 694 |
| Axe | 796 | 432 | 196 | 78 |
| Shield | 1328 | 634 | 303 | 86 |
| Total | 8921 | 4676 | 2224 | 858 |

Body images **4 → 4**, axe images **4 → 4**, one shared set per component across LODs. Geometry/UV density and atlas margins remain unchanged. Body size **{proof['mm6_figc.glb']['before']['bytes']} → {proof['mm6_figc.glb']['after']['bytes']} bytes**; axe **{proof['mm6_figc_axe.glb']['before']['bytes']} → {proof['mm6_figc_axe.glb']['after']['bytes']} bytes**.

| File | Bytes | SHA-256 |
|---|---:|---|
{hashes}

Changed source/review files: `scripts/*_r6.py`, `textures/round6/body/metal_rough.png`, `textures/round6/axe/metal_rough.png` and their `steel_ramp.json`, `export/artifacts.json`, assembled three-tier viewer GLBs/manifest, editable LOD0 tier-A blend, refreshed full front/side/three-quarter sheets, `review/round6/`, README and progress record. Runtime exports remain authoritative for all LODs and tier ramps.

**check_bindings.py: no BAD line** ([log](review/round6/bindings_check.txt)); **viewer: 24/24 tier/clip switches, no console errors** ([result](review/round6/viewer_check.json)). Running and Attack playback captured at 1× and 0.5×. Native integration/capture remains the orchestrator's job. The final shared gate report is bound to the exported body hash; no changes to game assets were made.

Reproduction under a reclaimed lease: `run_retarget_r6.py` → `run_fit_r6.py` → `run_patch_r6.py` → `materials_r6.py` → `final_checks_r6.py` → `sheets_r6.py`; shared bindings/viewer checks and `record_r6.py`. Blender uses one background process, `--threads 4`. Earlier round builders below are historical and would restore rejected clips. **Never use RelaxRunForward or Jogging.**

## Earlier handoffs (superseded)

'''
oldtext=(R/'before/HANDOFF.md').read_text();(P/'HANDOFF.md').write_text(text+oldtext)
readme='''# Current delivery: review round 6 — Standard Run and mid-grey steel

Running now uses Mixamo **Standard Run** with a smooth symmetric 12 mm pelvis bob and fitted feet, replacing rejected Jogging. Body/axe steel is the measured perceptual midpoint between round-1 bright and current dark, matte on all tiers. All geometry and seven other clips are unchanged; shield and integration/actors.yml remain byte-identical. No new credits (30/100 total).

[HANDOFF.md](HANDOFF.md) contains hashes, native luminance measurements, 48 Hz jitter diagnostics and shared gate results. [Colour comparison](review/round6/steel_comparison_front.png), [running side sheet](review/round6/running_left.png), [viewer](review/viewer/index.html). Bindings and viewer pass. The shared rig verdict remains FAIL on disclosed inherited grip/posture/LOD limits; all visible LODs pass Running contact/floor checks. No game, build, installation or commit.

Reproduction uses the scripts ending `_r6.py` listed in HANDOFF.md. Decisions: retain the 1.2 m stride binding, solve feet to a fixed smooth root curve, use the archived bright ramp as the colour midpoint reference, keep the accepted shield untouched, preserve texture packing, report the missing shared positional-jitter threshold without adding a custom gate.

## Earlier project record (superseded)

'''
(P/'README.md').write_text(readme+(R/'before/README.md').read_text());print('ROUND6_RECORDED',summary)

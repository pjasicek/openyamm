"""Final review-two handoff from validated runtime artifacts; does not install runtime files."""
import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round2';D=json.loads((P/'review/delivery_validation.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=D['review_round_2'];n=a['native_comparison'];m=n['model'];contact=D['grip_palms_cloth_locomotion']['clips'];walk=contact['Walking'];cal=a['transitions_and_head']['calibration'];distance=D['distance_silhouettes'];distance_rows='\n'.join(f"| LOD{x['lod']} | {x['pooled_iou']:.5f} |"for x in distance['rows']if x['clip']=='Standing')
g=D['gates'];selected=json.loads((R/'reduction/selected.json').read_text())
counts={name:list(info['triangles'].values())[:4]for name,info in D['files'].items()if name.startswith('export/')}
gap=max(max(x['grip_gap_mm'].values())for x in contact.values());pen=max(x['grip_penetration_mm']for x in contact.values())
tilt=max(x['soles'][s]['max_tilt_degrees']for x in a['clips'].values()for s in x['soles'])
heeltoe=max(max(abs(v)for v in so[key])for row in a['clips'].values()for so in row['soles'].values()for key in ['heel_height_m','toe_height_m'])*1000
elbow=min(e['signed_flexion_degrees'][0]for row in a['clips'].values()for e in row['elbow'].values());roll=max(e['max_forearm_roll_degrees']for row in a['clips'].values()for e in row['elbow'].values())
release=json.loads((P/'review/release_gate.json').read_text())
table='\n'.join(f"| [{Path(k).name}]({k}) | {' / '.join(map(str,counts[k]))} | {v['bytes']} | {v['sha256']} |"for k,v in D['files'].items()if k in counts)
gtable='\n'.join(f"| {name} | {v['arm_p99']:.2f} | {v['finger_max']:.3f} | {v['body_contact_cm']:.3f} / {v['equipment_contact_cm']:.3f} | {v['floor_min_m']*1000:.3f} | {v['pelvis_range_m'][0]:.3f}–{v['pelvis_range_m'][1]:.3f} | {v['trunk_lean_degrees'][0]:.1f}–{v['trunk_lean_degrees'][1]:.1f} |"for name,v in g.items())
# Editable files and all map hashes live in one machine-readable manifest.
files={k:dict(v)for k,v in D['files'].items()}
for path in [P/'integration/actors.yml',*sorted((P/'textures').rglob('*.png')),*sorted((P/'scripts').glob('*.py')),*sorted((P/'scripts').glob('*.mjs'))]:
 files[str(path.relative_to(P))]={'sha256':sha(path),'bytes':path.stat().st_size}
(R/'artifact_manifest.json').write_text(json.dumps(files,indent=2))
masters='\n'.join(f"- [{k}]({k}): {v['sha256']}"for k,v in D['files'].items()if k.startswith('work/'))
summary=f"""The left hand now closes around the leather grip in every clip; the bow attachment is solved from that fist.
The carry stays vertical beside the leg with the string inward. The matching right leather bracer is painted into
the shared texture and excluded from the cloth colour mask, so it remains leather on all three tiers. The HD front
master had omitted that bracer; the explicit user correction takes precedence over that omission.

Cast is an exact copy of Attack under the distinct name Cast: {D['cast_exact_attack_copy']['channels']} exported
animation channels have identical time and value arrays. Both release at 1.200 s from Socket_Arrow_Release.
The old palm gesture and palm_right descriptor binding are removed. The unused Socket_Palm_Right bone remains
to preserve the 63-joint skeleton; nothing binds to it.

The accepted relaxed Standing and Fidget remain. Foot yaw is aligned with travel and the walk has a visible
9 cm swing while retaining a planted support foot. Entry/return keys match the rest pose exactly; Death starts
there and ends in the held Dead pose. Walking stride is recalibrated to {cal['new_binding_stride_m']:.8f} m.
"""
handoff=f"""# MM6 BArcher arc1 — batch handoff

Review round 2 technical checks complete; user artistic acceptance and orchestrator integration remain pending.
Total spend: 40/100 credits, zero this round. No shared assets, game launches, builds or commits.

[Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/) ·
[Native and sole comparison](review/round2/native_rest_comparison.jpg) · [Turnaround](review/turnaround_sheet.jpg).

## Review round 2

{summary}
### Changed files and integration

Replace all three runtime files together, then merge [integration/actors.yml](integration/actors.yml):

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{table}

Body shadow counts equal their respective colour LOD counts. The body includes the 24-triangle moving string,
63 joints, eight clips, three region variants and one primitive per LOD with four shared 2080×1024 atlases.
Combined intermediate GLBs and the baked browser tier files are review/build inputs, not installation files.

integration/actors.yml **changed**: all three tiers bind Cast and its 1.200 s event to Socket_Arrow_Release;
palm_right was removed; stride_length is {cal['new_binding_stride_m']:.8f}. Its SHA-256 is
{sha(P/'integration/actors.yml')}. IDs 475/476/477, scale 106.382287, yaw −π/2 and run: Walking remain.
Standing height is {cal['upright_height_world']:.3f} world units against native {cal['native_height_world']:.3f}.
Clip durations: {', '.join(f'{k} {v:.5g} s'for k,v in D['clips'].items())}.

Editable masters:

{masters}

Changed texture maps include body/head base colour, normal, metal/roughness and region masks, plus bow base colour,
normal and metal/roughness. The right-bracer material class and source generation scripts also changed.
[Artifact manifest](review/round2/artifact_manifest.json) records exact map/script/master hashes.
The round-one export and masters remain in review/round2/baseline/.

### Reduction and rebaking

The revised batch criterion was applied: planar dissolve and protected collapse, followed by Cycles
selected-to-active base-colour, region-mask, material-channel and tangent-normal rebaking from the unreduced model.
Face, fingers, soles, joints, silhouette and the hair/quiver contact geometry are protected. The lower LODs retain
the UV layout and reuse the selected rebake, with their actual resulting appearance measured independently.
Eight views use a near body height of approximately 750 px (conservative against the requested about 700 px);
LOD switch diameters use 550/220/88 px, including a 10% switch margin. All three actual tier ramps are tested. Distance selection uses the eight-view pooled silhouette of the equipped Standing pose; the near gate retains its per-view IoU and SSIM limits.

[Curve](review/round2/reduction/curve.png), [CSV](review/round2/reduction/curve.csv),
[all tier metrics](review/round2/reduction/final_material_metrics.json) and
[rebake receipt](review/round2/reduction/rebake.json) retain the measurements.
[Body comparison](review/round2/reduction/body_side_by_side.jpg),
[bow comparison](review/round2/reduction/bow_side_by_side.jpg) and
[arrow comparison](review/round2/reduction/arrow_side_by_side.jpg) accompany the full-resolution eight-view PNGs.

Near body reduction: 10,564 to 9,507 triangles (10.0%), plus the unchanged 24-triangle string. The initial source had 15,096 body triangles before the first production reduction and retexture; this round rebakes from the reviewed 10,564-triangle textured authoring surface. Total body reduction from that initial geometry is 37.0%.
The next 8,555-triangle rebaked body passes silhouette IoU (0.9915) but fails textured SSIM (0.9447 < 0.95).
The selected near body reaches IoU {selected['body']['0']['min_iou']:.5f} and worst-tier SSIM
{selected['body']['0']['min_ssim']:.5f}. Near meshes meet IoU ≥ 0.99 and SSIM ≥ 0.95. Distance meshes meet equipped-standing pooled IoU ≥ 0.97 and strictly decreasing installed-count caps.
The 5–8k humanoid expectation could not be reached within these measured limits.
The original UV-preserving trials are retained for audit but are superseded by the rebaked selection.

The final equipped chain is strictly decreasing and below the installed triangle counts at every level.
The body and every prop also stay at or below their own installed counts. Protected reduction, silhouette fitting,
physical grip/sole corrections and selected rebaked maps are retained in work/round2/.
The coarsest exported body is 596 triangles plus its 24-triangle moving string. Cleanup removed seven duplicate body faces and seven duplicate bow faces before the final gates. Its grip faces are explicitly triangulated
before contact fitting, preventing Blender from choosing a different diagonal after the fit.

| Distance level | Equipped Standing pooled IoU, eight views |
|---|---:|
{distance_rows}

[Distance comparisons](review/round2/reduction/distance_sheet.jpg) and
[assembled silhouette measurements](review/round2/reduction/assembled_distance_metrics.json) show the result.
Component IoU/SSIM remains in the curve data; the pooled equipped-actor criterion controls distance selection.
An additional Attack-release diagnostic gives about 0.984 / 0.963 / 0.926 IoU at LOD1/2/3. These are supplementary
pose comparisons, not the calibrated Standing selection test. The two farthest attack silhouettes need visual
acceptance at their actual switch size; the loss is recorded rather than presented as a 0.97 pass.

### Gates and review

All selected LODs run the body, equipment, signed elbow, hand contact, palm, sleeve and foot gates on all clips.
Signed anatomy, grip/palm/cloth/sole and gait samples run at 48 Hz; equipment and floor use quarter frames.
G4/G5 cover every authored frame. These are sampled checks, not continuous collision proofs. The table below summarizes LOD0; every distance-level report is retained in the per-LOD folders.

| Clip | G4 p99 × | G5 max × | Body / equipment cm | Floor min mm | Pelvis m | Trunk lean ° |
|---|---:|---:|---:|---:|---:|---:|
{gtable}

LOD0 grip gap ≤ {gap:.3f} mm and conservative grip penetration ≤ {pen:.3f} mm. Across all four LODs, the maxima are {max(v["grip_gap_mm"]for v in D["lod_gate_maxima"].values()):.3f} mm gap and {max(v["grip_penetration_mm"]for v in D["lod_gate_maxima"].values()):.3f} mm penetration, both below 3 mm.
Sleeve penetration is zero; fitted shorts/boots have no separate skirt or robe shell.
Minimum signed elbow flexion {elbow:.3f}°, maximum forearm roll {roll:.3f}°.
Standing/Fidget sole tilt ≤ {tilt:.3f}°; heel and toe ≤ {heeltoe:.3f} mm above the floor.
Walking sole peaks L/R: {walk['sole_height_m']['L'][1]*100:.2f}/{walk['sole_height_m']['R'][1]*100:.2f} cm;
mid-swing knees {walk['knee_at_peak_deg']['L']:.2f}/{walk['knee_at_peak_deg']['R']:.2f}°;
support foot within 1 cm for {100*walk['support_fraction']:.1f}% of sampled frames.
Foot yaw and palm direction for every clip are recorded in [contact gates](review/round2/contact_gates.json).
Running intentionally uses this same grounded Walking clip.

Native rest comparison: foot spacing / height 8.98% native versus {m['foot_spacing_per_height']*100:.2f}% model;
body width 25.0% versus {m['body_width_per_height']*100:.2f}%; upper arms about 0° versus 4.3°;
forearms 5.4–8.9° versus 9.6°. Native landmarks have ±2 px uncertainty.
The shared skin passes native mean/p90/p95 luminance comparisons; the face received a small grade before rebaking.
Head/quiver clearance is checked separately at 48 Hz, with ray-parity confirmation for the open quiver lip. Equipment intersections likewise require three-of-four ray-parity confirmation for open shoulder flaps. Grip surfaces use barycentric eighths (45 points per triangle); the 3 mm limits are unchanged.

Attack/Cast arrow direction is {release['arrow_axis_degrees_from_forward']:.3f}° from forward;
socket error {release['launch_socket_offset_error_m']:.3g} m; string contraction peaks at
{release['peak_string_contraction_m_per_s']:.3f} m/s after release. The nocked arrow is hidden by 1.23333 s.
There is no blade; arrow direction, draw-hand contact and string release are the corresponding weapon gates.
Bow limbs remain rigid.

All eight exported motion traces have zero flags. The source-calibrated angular-acceleration gate passes on every upper arm, forearm and wrist; see [acceleration](review/round2/angular_acceleration.json) for source values and the stated sampling allowance. Final skin-weight sums pass 1e-4 on all colour/shadow primitives.
[Mandatory binding/weight checker](review/round2/check_bindings.log) has no BAD line.
Viewer check passes 24/24 tier/clip switches with no console errors; capture browser processes were closed.
All 71 recorded native inputs remain unchanged. See [delivery validation](review/delivery_validation.json),
[anatomy/feet](review/round2/anatomy_and_feet.json), [transitions/head](review/round2/transitions_and_head.json),
[skin luminance](review/round2/skin_luminance.json) and [per-LOD gates](review/round2/lod_gates/).

Fresh sheets: [Standing](review/clips/Standing_sheet.jpg), [Fidget](review/clips/Fidget_sheet.jpg),
[Walking](review/clips/Walking_sheet.jpg), [Attack](review/clips/Attack_sheet.jpg),
[Cast](review/clips/Cast_sheet.jpg), [Hit](review/clips/Hit_sheet.jpg),
[Death](review/clips/Death_sheet.jpg), [Dead](review/clips/Dead_sheet.jpg).
[Standing grip](review/hands_Standing.jpg), [Attack grip](review/hands_Attack.jpg),
[Cast grip](review/hands_Cast.jpg), [Death grip](review/hands_Death.jpg).
The agent's inspection list is in [visual review](review/round2/visual_review.json).

## Review round 1

The relaxed native rest, two-second Fidget, flat soles and rest transitions were established in round 1 and retained.
Its historical files, hashes and gate results are preserved in
[the round-one handoff snapshot](review/round2/baseline/HANDOFF.md). Round-two integration instructions supersede it.

## Remaining external work

The orchestrator installs the three GLBs and descriptor changes, builds, runs the proposed regression checks,
and captures indoor/outdoor gameplay. Inspect fireball handoff, pacing, look overlays, lighting, distance attack silhouettes, LOD switches and shadows.
See [integration/regression.md](integration/regression.md). Artistic acceptance is pending.
The project lease is released as the last handoff operation; a future edit must reclaim mm6:arc1.
"""
(P/'HANDOFF.md').write_text(handoff)
(P/'README.md').write_text(f"""# MM6 BArcher arc1 — Codex project

Review round 2 complete; artistic acceptance and orchestrator integration pending. Total spend **40/100 credits**,
zero this round. [HANDOFF.md](HANDOFF.md) contains current filenames, hashes, counts and gate results.

[Open viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).
Viewer check: 24/24 tier/clip switches, zero errors.

![Native rest and sole comparison](review/round2/native_rest_comparison.jpg)

## Current decisions

{summary}
No new Meshy job or animation purchase was needed. The local Mixamo draw/release remains the source for Attack
and its distinct Cast copy. The original palette variants, adult auburn-haired design, quiver and detailed bow remain.
The native ../mm6_arc1 project is read-only; all 71 recorded hashes match.

## Deliverables and limits

Install all three files in export/: mm6_arc1.glb, mm6_arc1_bow.glb and mm6_arc1_arrow.glb, plus the changed
[integration/actors.yml](integration/actors.yml). The orchestrator owns installation.
The body colour/shadow LOD counts are {' / '.join(map(str,counts['export/mm6_arc1.glb']))};
bow {' / '.join(map(str,counts['export/mm6_arc1_bow.glb']))};
arrow {' / '.join(map(str,counts['export/mm6_arc1_arrow.glb']))}.
Body: 63 joints, eight clips, three native colour ramps and four shared 2080×1024 atlases.
Editable masters are work/rig_equipped.blend, rig_textured.blend and runtime_authoring.blend.

Reduction follows the revised batch rebake method. Actual-tier eight-view IoU/SSIM and every selected LOD's motion
gates pass. The final LOD chain strictly decreases and stays below installed counts. Additional far Attack-release silhouette diagnostics and real-GPU LOD transitions still need integration review. The bow has a moving string and rigid limbs. These limits are recorded, not hidden by thresholds.

## Reproduction and evidence

All writes require the project lease. Use tools/run_creature_blender.sh (background, four threads, one process)
for Blender scripts, and tools/creature_workspace.py run for ordinary Python writes.
Round-one inputs are preserved in review/round2/baseline/. Current source textures for reprojection are in
work/round2/high_textures/; selected geometry is enumerated in review/round2/reduction/selected.json.

The local pipeline is round2_texture.py and round2_motion.py; measured protected reduction trials;
round2_rebake.py; round2_assemble.py and round2_lod_gates.py; round2_pack_lods.py and pack_runtime.py;
round2_endchecks.py; round2_material_metrics.py using round2_tier_maps.py; compose_sheets.py and
round2_sheets.py; round2_finish_records.py; check_viewer.py; validate_delivery.py.
Distance refinement adds the round2_distance_* scripts, constrained grip/sole fitting, explicit triangulation and duplicate-face cleanup. Selected .blend files are the authoritative resumable inputs.
Use the active textured Body object when transferring geometry; an orphan datablock named Body is not authoritative.

See [reduction curve](review/round2/reduction/curve.png), [body comparison](review/round2/reduction/body_side_by_side.jpg),
[delivery validation](review/delivery_validation.json), [grip/palms/gait](review/round2/contact_gates.json),
[visual inspection](review/round2/visual_review.json), [animation study](source/ANIMATION_STUDY.md),
[integration checks](integration/regression.md) and [playbook notes](integration/playbook_notes.md).
No assets_dev write, game launch, build or commit was performed.
""")
progress=json.loads((P/'creature_3d_progress.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
progress.update(stage='review_round_2_handoff',status='complete',technical_completion='complete',user_acceptance='review_round_2_pending',updated_at=now,next_action='Orchestrator installs all three GLBs and merges changed actors.yml; runs runtime checks and user review')
progress['selected_artifacts']={k:{'path':k,**v}for k,v in D['files'].items()}
progress['runtime']['installation']='review_round_2_three_exports_and_changed_binding_await_orchestrator'
progress['validation']={'report':'review/delivery_validation.json','gates':g,'viewer':'review/check_viewer.log','viewer_switches':24,'anatomy_and_feet':'review/round2/anatomy_and_feet.json','contacts':'review/round2/contact_gates.json','reduction':'review/round2/reduction/final_material_metrics.json','skin_weights':'review/round2/check_bindings.log','visual_review':'review/round2/visual_review.json'}
progress['review_round_2']={'completed_at':now,'credits_spent':0,'total_credits':40,'budget':100,'integration_actors_yml_changed':True,'cast_exact_attack_copy':True,'grip_gap_mm':gap,'grip_penetration_mm':pen,'triangles':counts,'source_hashes_unchanged':71,'handoff':'HANDOFF.md','lease':'released as final operation'}
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('README, HANDOFF, manifest and progress updated')

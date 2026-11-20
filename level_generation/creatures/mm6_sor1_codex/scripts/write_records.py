"""Write completion records from actual export, viewer and gate receipts."""
from pathlib import Path
import json,hashlib,datetime
p=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((p/name).read_text())
gates=read('work/gates_exported.json');audit=read('work/runtime_audit.json');trace=read('work/export_trace.json');parity=read('work/export_parity.json');release=read('work/motion_details.json')
viewer=read('review/viewer_check.json');play=read('review/browser/viewer_playback.json')
assert len(gates)==8 and all(all(v[k] for k in ['G4_pass','G5_pass','G6_pass']) for v in gates.values())
assert all(not v['flags'] for v in trace.values())
assert viewer['switched']==24 and not viewer['failed'] and not viewer['consoleErrors']
assert play['passed'] and len(play['checks'])==16
for n in ['review/final_clips/front_sheet.jpg','review/final_clips/left_sheet.jpg','review/final_clips/three_quarter_sheet.jpg','review/staff_crown_three_quarter.png','review/staff_full_front.png']:assert (p/n).is_file(),n
body=audit['export/mm6_sor1.glb'];staff=audit['export/mm6_sor1_staff.glb'];progress=read('creature_3d_progress.json')
spent=sum(x['consumed_credits'] for x in progress['meshy']['jobs'].values());assert spent==40 and spent<=100
rows=[]
for name,v in gates.items():
 g4=max(a[0] for a in v['G4_p99'].values());g5=max(a[0] for a in v['G5_max'].values());g6=max([a[0] for a in v['G6_mm'].values()]+[0])
 pelvis='–'.join(f'{a:.3f}' for a in v['pelvis_height_m']);lean='–'.join(f'{a:.2f}' for a in v['trunk_lean_deg'])
 rows.append(f'| {name} | {g4:.3f} | {g5:.3f} | {g6:.3f} | {pelvis} | {lean} |')
table='| Clip | G4 edge p99 | G5 hand max | G6 depth mm | Pelvis m | Trunk lean ° |\n|---|---:|---:|---:|---|---|\n'+'\n'.join(rows)
runtime_files=['export/mm6_sor1.glb','export/mm6_sor1_staff.glb']
checksums={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in runtime_files}
(p/'export/SHA256SUMS').write_text(''.join(h+'  '+Path(n).name+'\n' for n,h in checksums.items()))
maxparity=max(parity['surface_parity_max_mm'].values())
floor=min(v['floor_min_mm'] for v in gates.values());grip=min(v['grip_min_mm'] for v in gates.values())
hand=f'''# MM6 Sorcerer — batch handoff

**Technically complete; artistic acceptance pending.** Meshy **{spent}/100 credits**, no active paid jobs.
Owner codex-batch-sor1, identity mm6:sor1. No commit, runtime installation, shared source edit, build or game launch.

## Installable files

| Project file | Runtime destination | Colour LOD triangles |
|---|---|---|
| [export/mm6_sor1.glb](export/mm6_sor1.glb) | assets_dev/worlds/mm6/models/mm6_sor1.glb | {body['colour_lod_triangles']} |
| [export/mm6_sor1_staff.glb](export/mm6_sor1_staff.glb) | assets_dev/worlds/mm6/models/mm6_sor1_staff.glb | {staff['colour_lod_triangles']} |

Four colour LODs each, plus dedicated body shadow LODs. One body primitive per LOD; 124-joint skeleton, at most eight influences.
Three native robe tiers: sor1_a / sor1_b / sor1_c. Static staff attaches to B_Staff.
[SHA256SUMS](export/SHA256SUMS) and [structural receipt](work/runtime_audit.json) identify the final bytes.
[Packed editable master](work/production_master.blend) retains the separate body and staff.

## Integration

- [Exact descriptor blocks](integration/actors.yml): Sorcerer A/B/C, scale 106.121, yaw -1.570796327.
- [Proposed regression and capture checks](integration/regression.md): mm6_sorcerer_codex_family, mm6 / 6d07.blv, ids 631/632/633.
- [Playbook notes](integration/playbook_notes.md), staged only.
- Attack and Cast release from Socket_Palm_Left at **0.7375 s**; actual forward socket speeds
  {release['Attack']['forward_speed_mps']:.3f} / {release['Cast']['forward_speed_mps']:.3f} m/s.
  Socket_Staff_Head is the secondary focus. There is no cutting blade; blade-edge gate is not applicable.

## Gate results

All eight clips pass G4/G5/G6 on the actual reimported GLB, sampled at **240 Hz**, including half-key frames.
G4 p99 limit <2; G5 maximum <=4.5; G6 contact depth <=2 mm; head/shoulder <=10 mm.

{table}

Minimum measured body/floor clearance {floor:.3f} mm. Hand tunnel radius {grip:.3f} mm versus a 10.500 mm shaft.
Head/shoulder and final staff/body penetration checks pass. Export/master surface parity maximum {maxparity:.3f} mm.
[Full gates](work/gates_exported.json), [weight profiles](work/g4_production.json), [source-speed trace](work/export_trace.json),
[release measurement](work/motion_details.json). All eight source-relative speed traces have zero flags.
Posture is recorded for every clip; the lean in Death/Dead is intentional.

## Review package

- [Viewer](review/viewer/index.html), served from the repository root; manifest offers all three tiers and eight clips.
- Existing check_viewer.mjs: **24 tier/clip switches, zero failures or console errors** ([receipt](review/viewer_check.json)).
- Real-time browser playback: all eight clips at 1× and 0.25× ([receipt](review/browser/viewer_playback.json),
  [recording](review/browser/viewer_playback.webm)).
- Clip sheets: [front](review/final_clips/front_sheet.jpg), [side](review/final_clips/left_sheet.jpg),
  [three-quarter](review/final_clips/three_quarter_sheet.jpg).
- Staff: [native-derived design](references_hd/staff_design.png), [full model](review/staff_full_front.png),
  [crown](review/staff_crown_three_quarter.png), [grip](review/staff_grip_three_quarter.png).
- Feedback file is empty; no user acceptance is implied by these technical checks.

## Open review items and limits

The adapted corpse is more extended and supine than the native curled side pose; the staff remains held at an angle,
rather than settling as low beside the native corpse. Hidden trousers, fine embroidery, staff engraving and unseen
anatomy are inferred. The fall hem flares more broadly than the native sprite and exposes the inferred trousers; review that drape and the head's gray temple detail artistically.
Whole-model fidelity, gait speed, combat blending, runtime event timing, bgfx material appearance and real-GPU performance
remain with the orchestrator. No game validation is claimed.

The source restoration project ../mm6_sor1/ remained read-only; retained source hashes match.
The remaining 60 Meshy credits were not needed. Final action is release of the creature lease after this handoff.
'''
(p/'HANDOFF.md').write_text(hand)
(p/'README.md').write_text(f'''# MM6 Sorcerer (sor1) — Codex batch

**Asset production complete; see [HANDOFF.md](HANDOFF.md). Artistic acceptance and game integration remain pending.**
FULL production followed [Batch rules](../MM6_CODEX_BATCH_GOAL.md#batch-rules). Only this project was changed;
../mm6_sor1/ supplied read-only native sprites. No commit, build or game launch.

## Result and review

Rigged body plus separately attached detailed staff, eight clips, four LODs, three native palette tiers.
Body LOD triangles {body['colour_lod_triangles']}; staff {staff['colour_lod_triangles']}; 124 joints, maximum eight influences.
Body/head retain separate 1K source sets and merge into one 2080×1024 runtime atlas with a gutter.
The staff uses its own detailed 1K atlas. Body and head are matte; the staff has a per-pixel material mask.

Start with the [viewer](review/viewer/index.html), [front clip sheet](review/final_clips/front_sheet.jpg) and
[staff design](references_hd/staff_design.png). Serve the repository root over HTTP; the viewer reuses the existing
read-only three.js vendor bundle and native sor1 frames. The empty feedback record means user approval is still pending.

## Recorded unattended decisions

- Native identity: mature slender man, high purple/red-lined collar, short receding dark hair, moustache and pointed
  beard, gold shoulder accents, red/gold trim and belt, loose long robe, bracers and brown shoes; no cape.
- Model from tier C purple. Native palettes 819/820/821 supply A black/olive, B red, C purple robe ramps.
  Gold, red trim, skin, leather and the staff stay unchanged between tiers.
- Generate body references without equipment to preserve fingers. Build the required staff separately from its own
  native-derived imagegen design. Its 2,888 triangles form a slender wooden shaft, bevelled ferrules, grooved leather
  grip, engraved gold socket, four curved crown fingers and a faceted dark-red jewel.
- Local Relax/Armed/Unarmed clips were inspected before modelling. Use upright idle/walk, planted caster attacks,
  small discrete steps, a left-hand chin fidget, face-covering hit and adapted backward fall. No paid animation.
- Staff stays in the right hand; the left palm casts. Measure the actual release socket, not a clip name:
  Attack and Cast both peak at 0.7375 seconds after the Cast ready hold.
- Repaired generated needle triangles, false robe/shoe bridges, forehead anchors and fragmented lip geometry.
  The lower robe and closed shoes were rebuilt, and fitted trousers connect shoes to the body during the fall.
  Small eye/mouth boundaries remain; the head is not advertised as watertight.
- Fit the source-frame humanoid rig, fingers and staff grip; add four twist helpers, 64 cloth helpers and three sockets.
  The walk retains restrained robe movement. Death uses a smooth fitted drape with actual leg/shoe/floor corrections;
  both arms clear the cloth while preserving grip. No free-flapping cloak is used for this closed robe.
- Export at 120 Hz and test at 240 Hz. Limit to eight influences before export and validate the reimported surface.
  Every clip passes deformation/contact/posture checks; source-relative motion-speed checks have no flags.
- Body calibration excludes the staff: 257 native pixels × 0.699997 = 179.899 game units.
  Standing body height 1.695234 m gives scale 106.121. Speeds 200/220/240 use Walking, below the run threshold 254.690.
- Technical completion is distinct from art acceptance. The final corpse is more extended than the curled native
  side pose, with the retained staff angled higher. See handoff open items and the proposed native runtime captures.

## Provenance and budget

Meshy Smart Topology 5 + rig 5 + body retexture 10 + superseded head v1 10 + repaired head v2 10 =
**40/100 credits**, all jobs complete and downloaded. The detailed ledger, task ids, requests and hashes are in
[creature_3d_progress.json](creature_3d_progress.json). Head v1 is superseded by v2; no paid job is pending.
Body, head and staff design artwork came from built-in imagegen; staff surface samples were packed from its retained design.
Source restoration hashes are unchanged. No OpenEnroth/mm_mapview2 code was copied.

## Reproducibility and handoff boundaries

The editable endpoint is work/production_master.blend. Project scripts and work receipts retain the geometry,
UV transfer, rig, animation, cloth and export steps. export/ also contains intermediate combined GLBs;
only the two files named in HANDOFF.md are installable endpoints.
integration/ contains exact YAML blocks, a proposed regression and lessons without editing shared files.
The orchestrator owns installation, build, regression and indoor/outdoor captures.
''')
f=p/'ANIMATION_STUDY.md';s=f.read_text().replace('All motion remains 30 fps; impacts measured after blend-in, target near 0.75 s.','Source motion was studied at 30 fps; final clips are baked at 120 fps and checked at 240 Hz. Attack/Cast left-palm releases peak at 0.7375 seconds. Hit lasts 0.75 seconds.')
s+='\nFinal adaptation: closed-robed fall uses a fitted drape and contact corrections; left arm opens to clear cloth and the right arm keeps the staff beside it. The final supine, extended corpse and retained angled staff differ from the native curled side corpse; artistic review remains pending.\n'
f.write_text(s)
progress['stage']='batch_handoff_complete';progress['status']='technically_complete_artistic_acceptance_pending';progress['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
progress['next_action']={'owner':'orchestrator','action':'Integrate staged assets and snippets, run regression and indoor/outdoor visual checks, request artistic review'}
progress['mesh_credits_spent']=spent;progress['runtime_exports']={k:audit[k] for k in runtime_files}
progress['gates'].update({k:{'status':'pass','every_clip':True,'sample_hz':240,'evidence':'work/gates_exported.json'} for k in ['G4','G5','G6','posture']})
progress['gates']['viewer']={'status':'pass','switches':24,'evidence':'review/viewer_check.json'}
progress['gates']['playback']={'status':'pass','clips':8,'speeds':[1,.25],'evidence':'review/browser/viewer_playback.json'}
progress['gates']['source_speed']={'status':'pass','flags':0,'evidence':'work/export_trace.json'}
progress['gates']['staff']={'status':'pass','blade_edge':'not applicable; caster staff','release_seconds':.7375,'evidence':['work/motion_details.json','work/staff_geometry.json','review/staff_crown_three_quarter.png']}
progress['gates']['runtime_structure']={'status':'pass','evidence':'work/runtime_audit.json'}
progress['artistic_acceptance']='pending';progress['game_validation']='deferred to orchestrator by batch rules'
progress['open_review_items']=['Extended supine corpse versus native curled side pose; retained staff sits higher','Review inferred embroidery/engraving, hidden trousers and gray temple texture','Runtime gait, combat blending, event timing, materials and performance not tested']
(p/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('HANDOFF READY',spent,'credits; all gates and viewer receipts verified')

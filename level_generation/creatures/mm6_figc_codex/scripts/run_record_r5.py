"""Validate and record the Running-only handoff from shared-gate and viewer evidence."""
import json,hashlib,sys,subprocess,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review/round5';E=P/'export';V=P/'review/viewer';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((R/'artifact_parity.json').read_text());g=json.loads((R/'final/gates.json').read_text());old=json.loads((R/'baseline/gates.json').read_text())
assert not g['error']
for asset in g['assets']:assert sha(Path(asset['path']))==asset['sha256']
for path,entry in proof.items():
 assert sha(P/path)==entry.get('after',entry.get('sha256'))
 if entry.get('unchanged'):assert (P/path).read_bytes()==(R/'before'/path).read_bytes()
 else:
  d,b=read_glb(P/path);od,ob=read_glb(R/'before'/path);assert bytes(b[:len(ob)])==bytes(ob)
  for k in ['meshes','nodes','skins','images','textures','materials']:assert d.get(k)==od.get(k)
  for a,oa in zip(d['animations'],od['animations']):
   if a['name']!='Running':assert a==oa
   else:
    for sam in a['samplers']:
     val=accessor_array(d,b,sam['output']);assert np.array_equal(val[0],val[-1])
viewer=json.loads((R/'viewer_check.json').read_text());assert viewer['ready']=='true' and viewer['switched']==24 and not viewer['failed'] and not viewer['consoleErrors']
viewer['manifest_sha256']=sha(V/'manifest.json');(R/'viewer_check.json').write_text(json.dumps(viewer,indent=2));(P/'review/viewer_check.json').write_text(json.dumps(viewer,indent=2))
manifest=json.loads((V/'manifest.json').read_text())
for m in manifest['models']:assert sha(V/m['url'].split('?')[0])==m['sha256']
res=subprocess.run(['python3',str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],capture_output=True,text=True,check=True);assert 'BAD'not in res.stdout;(R/'bindings_check.txt').write_text(res.stdout)
play=json.loads((R/'viewer/playback_review.json').read_text());assert len(play)==16 and all(x['time']>0 for x in play)
for view in ['front','left','three_quarter']:
 subprocess.run(['python3',str(P/'scripts/compose_sheet.py'),str(P/f'review/final_{view}'),str(P/f'review/clips_{view}.png')],check=True)
 rows=json.loads((P/f'review/final_{view}/frames.json').read_text());row=rows[2];im=Image.open(row[0][0]);sheet=Image.new('RGB',(im.width*len(row),im.height+24),(38,38,38));draw=ImageDraw.Draw(sheet)
 for i,(file,label)in enumerate(row):sheet.paste(Image.open(file).convert('RGB'),(i*im.width,24));draw.text((i*im.width+6,6),label,fill='white')
 sheet.save(R/f'running_{view}.png')
counts={}
for name in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb']:
 d,b=read_glb(E/name);chain=[0]+d['meshes'][0]['extras']['openyamm_lods'];counts[name]=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in chain]
assert counts=={'mm6_figc.glb':[6797,3610,1725,694],'mm6_figc_axe.glb':[796,432,196,78],'mm6_figc_shield.glb':[1328,634,303,86]}
combined=[sum(row[i]for row in counts.values())for i in range(4)]
files={p:{'bytes':(E/p).stat().st_size,'sha256':sha(E/p)}for p in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb','mm6_figc_portable.glb','mm6_figc_lod0.glb','mm6_figc_authoring.blend']}
art=json.loads((E/'artifacts.json').read_text());art.update(revision='review_round_5',files=files,lod_triangles=counts,combined_lod_triangles=combined,technical_completion=False);(E/'artifacts.json').write_text(json.dumps(art,indent=2))
info=json.loads((E/'export_info.json').read_text());info.update(revision='review_round_5',changed_clip='Running');(E/'export_info.json').write_text(json.dumps(info,indent=2))
lods=json.loads((E/'lods.json').read_text());lods.update(revision='review_round_5',original_rig_clips_retained=False,changed_clip='Running');(E/'lods.json').write_text(json.dumps(lods,indent=2))
def metric(report,name,lod=0,region=None):
 rows=[r for r in report['gates']if r['lod']==f'FighterChain/colour{lod}'and r['gate']==name and r['worst']is not None and(region is None or region==r['region'])]
 return max(r['worst']for r in rows)if rows else None
curve=[]
for lod in range(4):
 curve.append({'lod':lod,'contact_pct':metric(g,'running_contact_pct',lod),'airborne_mm':metric(g,'running_airborne_mm',lod),'floor_penetration_mm':metric(g,'floor_penetration_mm',lod),'foot_yaw_deg':metric(g,'foot_yaw_deg',lod),'arm_stretch_max':metric(g,'arm_stretch_max',lod),'hand_stretch_max':metric(g,'hand_stretch_max',lod)})
source=P.parents[2]/'anim_library/mixamo/Jogging.fbx';source_hash=sha(source)
result={'revision':'review_round_5','scope':'Running only','source':str(source.relative_to(P.parents[2])),'source_sha256':source_hash,'duration_s':.8,'stride_length_m':1.2,'run_stride_m':1.86,'loop_endpoint_exact':True,'non_running_payload_preserved':True,'props_and_bindings_byte_identical':True,'counts':counts,'combined':combined,'gates_status':g['status'],'gates_counts':g['counts'],'lod_metrics':curve,'viewer_switches':24,'playback_pairs':16,'credits_used':30,'round_credits':0,'technical_completion':False}
(R/'final_validation.json').write_text(json.dumps(result,indent=2));(P/'review/handoff_validation.json').write_text(json.dumps(result,indent=2))
progress=json.loads((P/'creature_3d_progress.json').read_text());progress['stage']='review_round_5_handoff';progress['review_round_5']=result;progress['technical_completion']=False;progress['open_limits']=['Ground contact is 79.17% on LOD0–2, below the shared 80% threshold; LOD3 is 100%.','Shared Running gate remains FAIL; see review/round5/final/gates.md for exact rows.','Accepted grip gaps/penetration persist with unchanged finger/prop local frames.','Existing LOD3 left heel/toe patch cannot establish yaw; right yaw exceeds the shared limit.','Running pelvis height falls below the inherited 0.9 m standing threshold; trunk remains upright.','Integration and game checks remain owned by the orchestrator.'];(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2))
metrics='\n'.join(f"| {x['lod']} | {x['contact_pct']:.2f}% | {x['airborne_mm']:.3f} | {x['floor_penetration_mm']:.3f} | {x['arm_stretch_max']:.3f} / {x['hand_stretch_max']:.3f} |"for x in curve)
hashes='\n'.join(f'| export/{name} | {v["bytes"]} | {v["sha256"]} |'for name,v in files.items())
head=f'''# FighterChain handoff — review round 5

## Review round 5 (running clip)

Replaced Running's rejected RelaxRunForward motion with local **Mixamo Jogging**. All seven other clips, nodes, meshes, weights, textures, tiers and LODs retain their original definitions and binary payload. Axe and shield GLBs are byte-identical to round 4. **integration/actors.yml did not change** (SHA-256 {sha(P/'integration/actors.yml')}). No game launch, build, installation or commit; zero new credits, **30/100** total.

Running uses the existing rest-delta Mixamo retarget path, source frames 0.5–26.5 at 30 fps, fitted to a **0.8 s** loop. The source supplies torso and arm swing; the shield arm keeps 45% of its swing for plate clearance. Hands retain the accepted closed grip and both attachments follow their hand. Two-bone leg IK fits a **1.86 m** run stride to the unchanged **1.2 m** binding and the runtime's **1.55×** run multiplier (game/fx/WorldFxSystem.cpp). Stance is 47% per foot, with a short low transition; toes align with travel. Root-floor fitting uses the shared runner's mesh evaluator against every shipped colour LOD. Keys are baked at 120 Hz, and every Running channel's final value equals its first value exactly. No new gate implementation was added.

Source SHA-256: `{source_hash}`. [Motion fit](review/round5/motion_fit.json), [sole fit](review/round5/sole_fit.json), [binary preservation proof](review/round5/artifact_parity.json), [final validation](review/round5/final_validation.json).

[Front](review/round5/running_front.png), [side](review/round5/running_left.png), [three-quarter](review/round5/running_three_quarter.png), [viewer shots/playback](review/round5/viewer/playback_review.json). The three existing full clip sheets have only their Running rows refreshed.

### Checks and remaining limits

Shared runner scoped to **Running**, baseline and final: **{old['status']} → {g['status']}**; FAIL rows **{old['counts']['FAIL']} → {g['counts']['FAIL']}**. [Final gate report](review/round5/final/gates.md), [accepted baseline](review/round5/baseline/gates.md). The script only filters the shared runner's clip inventory; all measurement and thresholds are its unchanged implementation. Exact loop closure is separately asserted on all exported animation accessors; the shared runner has no dedicated loop endpoint gate.

| LOD | Ground contact | Peak lowest sole, mm | Worst floor penetration, mm | Max arm / hand stretch |
|---|---:|---:|---:|---:|
{metrics}

Ground contact at LOD0–2 is **79.17%, below the shared 80% threshold**; LOD3 is 100%. Floor penetration and arm/hand stretch pass at every colour and shadow LOD.

The accepted baseline's LOD0 contact was {metric(old,'running_contact_pct'):.2f}%, floor penetration {metric(old,'floor_penetration_mm'):.3f} mm. Final LOD0 trunk lean is {metric(g,'trunk_lean_deg'):.2f}°, pelvis minimum {min(r['worst']for r in g['gates']if r['gate']=='pelvis_min_m'and r['worst']is not None):.3f} m. The inherited generic posture threshold requires pelvis ≥0.9 m and still fails on the fitted run. Existing LOD3 sole sampling has no usable left heel/toe separation, and right yaw remains above 10°. Full rig certification is **not** claimed.

Grip remains at the accepted local transforms: LOD0 axe middle-finger gap **{metric(g,'grip_gap_mm',0,'axe R middle'):.3f} mm**, shield gap **{metric(g,'grip_gap_mm',0,'shield L ring'):.3f} mm**, shield penetration **{metric(g,'grip_penetration_mm',0,'shield L'):.3f} mm**; the shared grip limits still fail. Correcting these would change the otherwise accepted fingers/prop fit. No such changes were made.

check_bindings.py has **no BAD line**. Viewer passes **24 tier/clip switches** and all eight clips advance at 1× and 0.5×. [Bindings](review/round5/bindings_check.txt), [viewer result](review/round5/viewer_check.json). Shared-suite failures and the historical distant LOD visual limit remain explicit; technical completion is false.

### Unchanged triangles and delivery hashes

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 6797 | 3610 | 1725 | 694 |
| Axe | 796 | 432 | 196 | 78 |
| Shield | 1328 | 634 | 303 | 86 |
| Total | 8921 | 4676 | 2224 | 858 |

Only the body runtime GLB needs replacement by the orchestrator. Its embedded image count remains **4**; prop image bytes and sizes are unchanged. Review GLBs and the editable blend carry the new Running loop too.

| File | Bytes | SHA-256 |
|---|---:|---|
{hashes}

Reproduction under a reclaimed lease: run_retarget_r5.py → run_refit_r5.py → run_patch_r5.py → run_gates_r5.py → run_finish_r5.py; then shared check_viewer.mjs, viewer_shots.mjs and run_record_r5.py. run_patch_r5.py always starts from review/round5/before, preserving the original payload. The editable blend uses corrected imported bone frames. Previous-round builders below are historical and would restore older Running clips. User rule: **never use RelaxRunForward again**.

Lease released at handoff. Integration and native game review belong to the orchestrator; use tools/install_model.py for accepted model installation, never copy to assets_dev.

## Historical handoffs (superseded)

'''
(P/'HANDOFF.md').write_text(head+(R/'before/HANDOFF.md').read_text())
(P/'README.md').write_text('''# Current delivery: review round 5 — Running

Running now uses local Mixamo Jogging, fitted to a 0.8-second seamless loop and the unchanged 1.86 m runtime run stride. RelaxRunForward is rejected. Every other clip and all geometry/material data are preserved; axe, shield and integration/actors.yml are byte-identical to round 4. No credits spent this round (30/100 total).

[HANDOFF.md](HANDOFF.md) records the new hashes, shared Running gate results and remaining limits. [Side sheet](review/round5/running_left.png), [viewer](review/viewer/index.html). The shared gate verdict remains FAIL; this is not a full rig-pass claim. No game, build, installation or commit.

The current Running-only builders are scripts/run_retarget_r5.py, run_refit_r5.py, run_patch_r5.py and run_finish_r5.py. Runtime patching preserves the accepted binary payload and changes only the Running animation references. The earlier builders below are historical.

## Earlier project record (superseded)

'''+(R/'before/README.md').read_text())
print(json.dumps(result,indent=2))

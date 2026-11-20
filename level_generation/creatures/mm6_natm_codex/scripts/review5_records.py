"""Record the narrow accepted-base revision and validate unchanged payloads."""
import json,hashlib,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];B=P/'work/review_round5_before';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads((P/f).read_text())
old,ob=read_glb(B/'export/mm6_natm.glb');new,nb=read_glb(P/'export/mm6_natm.glb')
assert bytes(nb[:len(ob)])==bytes(ob)
for key in ['meshes','skins','nodes','materials','images','textures']:assert old[key]==new[key],key
assert [a for a in old['animations']if a['name']!='Attack']==[a for a in new['animations']if a['name']!='Attack']
for name in ['mm6_natm_spear.glb','mm6_natm_buckler.glb']:assert (P/'export'/name).read_bytes()==(B/'export'/name).read_bytes()
assert (P/'integration/actors.yml').read_bytes()==(B/'integration/actors.yml').read_bytes()
main=read('review/round5_attack_gates/gates.json');reports=['review/round5_attack_gates/gates.json']+[f'review/round5_shaft_gates/lod{i}/gates.json'for i in range(4)]
for f in reports:
 d=read(f);assert d['status']=='PASS'
 for a in d['assets']:assert sha(Path(a['path']))==a['sha256'],a['path']
for row in read('review/round5_pairs/provenance.json')['pairs']:assert row['body_source_sha256']==sha(P/'export/mm6_natm.glb')
assert 'BAD'not in(P/'review/bindings_check.txt').read_text()
v=read('review/viewer_check.json');assert v['switched']==27 and not v['failed']and not v['consoleErrors']
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');og=S.Glb(B/'export/mm6_natm.glb');a=next(a for a in g.doc['animations']if a['name']=='Attack');oa=next(a for a in og.doc['animations']if a['name']=='Attack')
poses=g.pose(a,np.arange(58)/48);op=og.pose(oa,np.arange(109)/48)
pre=float(abs(poses[:46]-op[:46]).max());end=float(abs(poses[-1]-op[-1]).max());assert pre<2e-6 and end<2e-5,(pre,end)
invariants={'original_binary_prefix_identical':True,'other_eight_animation_records_identical':True,'both_prop_files_identical':True,'geometry_skin_material_texture_records_identical':True,'bindings_identical':True,'strike_max_matrix_delta':pre,'endpoint_max_matrix_delta':end,'first_recovery_hand_displacement_m':{side:float(np.linalg.norm(poses[46,g.names[f'B_{side}_Hand'],:3,3]-poses[45,g.names[f'B_{side}_Hand'],:3,3]))for side in 'LR'}}
(P/'review/round5_invariants.json').write_text(json.dumps(invariants,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
def tile(page,path,x,y,w,h,crop=False):
 im=Image.open(path).convert('RGBA')
 if crop:im=im.crop(im.getchannel('A').getbbox())
 bg=Image.new('RGBA',im.size,(87,87,87,255));bg.alpha_composite(im);im=bg.convert('RGB');im.thumbnail((w,h));page.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
page=Image.new('RGB',(2100,1228),(32,32,32));dr=ImageDraw.Draw(page);dr.text((12,10),'Review round 5 | Attack | 1.187500 s | hold removed, simultaneous recovery',font=font,fill='white')
for j,view in enumerate(['front','left','three_quarter']):
 for i,t in enumerate(np.linspace(0,57/48,7)):
  tile(page,P/f'review/final/Attack_{i:02}_{view}.png',i*300,42+j*390,300,370);dr.text((i*300+8,412+j*390),f'{view}: {t:.3f}s',fill='white')
page.save(P/'review/sheets/Attack.jpg',quality=94)
frames=[44,45,46,48,50,52,54,56,57];page=Image.new('RGB',(1500,len(frames)*470),(32,32,32));dr=ImageDraw.Draw(page)
for row,f in enumerate(frames):
 for c,view in enumerate(['front','left','three_quarter']):
  tile(page,P/f'review/final/round5_attack_{f:02}_{view}.png',c*500,row*470+35,490,425,True);dr.text((c*500+10,row*470+7),f'Frame {f} / 48 Hz — {view}',font=font,fill='white')
page.save(P/'review/round5_recovery.jpg',quality=94)
manifest=read('export/manifest.json');inventory={name:{'bytes':(P/'export'/name).stat().st_size,'sha256':sha(P/'export'/name)}for name in manifest['files']}
manifest.update(review_round=5,files=inventory,animations=read('export/export_info.json')['clips'],bindings_changed=False,bindings_sha256=sha(P/'integration/actors.yml'))
manifest['gate_reports']={f:sha(P/f)for f in reports};manifest['gate_scope']='Attack only; other eight animation payloads and all geometry/material/image payloads unchanged from accepted round 4.'
manifest['review_artifacts']={f:sha(P/f)for f in ['review/sheets/Attack.jpg','review/round5_recovery.jpg','review/round5_retime.json','review/round5_invariants.json','review/round5_clearance_diagnostic.json','review/round5_final_diagnostics.json','review/viewer/manifest.json','review/viewer_check.json','review/bindings_check.txt']}
(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def maximum(gate):return max(r['worst']for r in main['gates']if r['gate']==gate and r.get('worst')is not None)
table='\n'.join(f'| {name} | {row["bytes"]:,} | `{row["sha256"]}` |'for name,row in inventory.items())
counts=manifest['triangles'];tris='\n'.join(f'| {i} | {counts["body"][i]} | {counts["spear"][i]} | {counts["buckler"][i]} |'for i in range(4))
clearance=read('review/round5_clearance_diagnostic.json');gap=min(r['minimum_surface_distance_mm']for r in clearance['rows'])
text=f"""# MM6 PeasantM4 / natm — staged review handoff

Latest: **Review round 5**. Round 4 was accepted by the user. This revision changes only Attack's hold and recovery,
plus its editable source and review records. **50/100 Meshy credits spent; zero this round.**

## Review round 5 (attack hold)

- Removed the original frame 46–52 hold. The accepted wind-up and strike through frame 45 are preserved.
- Both arms now recover together immediately after the strike. World-space hand targets keep the spear on the right
  and route the shield clear of the torso; the fingers release the shaft during the return. The body and both arms
  finish in the accepted rest endpoint at **frame 57**. Local smoothing removes elbow acceleration peaks without
  increasing any gate threshold. Original planted support/step poses are retimed with the body.
- **Attack: 108/48 = 2.250000 s → 57/48 = 1.187500 s.** Recovery runs from the frame-45 boundary to frame 57:
  **12 intervals / 0.250000 s**, 25% shorter than the cited 16-frame 53–68 span. This replaces the old staggered
  recovery and its long tail through frame 108; the clip loses 51 intervals overall, not only the seven held frames.
- Impact remains **43.5/48 = 0.906250 s**, before the cut. Cast is a separate unchanged clip; release stays
  **23/48 = 0.479166667 s**. No later bound events exist to shift. `integration/actors.yml` is **byte-identical**.
  Bindings SHA256: `{manifest['bindings_sha256']}`.
- Geometry, skin weights, materials, every embedded image and all eight other animations retain their original
  metadata and binary payloads. Spear and buckler GLBs are **byte-identical** to accepted round 4. Texture sizes and
  triangle counts are unchanged. The original binary payload is retained and replacement Attack samples appended.
  [Invariant checks](review/round5_invariants.json), [retiming receipt](review/round5_retime.json).

[Attack sheet](review/sheets/Attack.jpg) · [recovery close-ups](review/round5_recovery.jpg) · [viewer](review/viewer/index.html).
Other clip sheets and skin comparisons remain the accepted round-4 images.

### Selected files

Integrate `export/mm6_natm.glb`; the two prop files are listed for verification but need no replacement.
`export/mm6_natm.blend` and `work/runtime_lod0.blend` through `runtime_lod3.blend` contain the new editable Attack.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
{table}

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
{tris}

### Validation

- [Shared Attack gates](review/round5_attack_gates/gates.md): **PASS**, {main['counts']}, all colour/shadow LODs,
  every one of **58 samples at 48 Hz**. The probe removes only the other animation inventory; it retains the exact
  runtime geometry, skeleton and Attack. [Source provenance](review/round5_probe_provenance.json).
- [Dense shaft probes](review/round5_shaft_gates/): **PASS** for LOD0–3, 58 samples each. Same coplanar shaft sampling
  method as round 4; runtime props unchanged. [Matching-LOD provenance](review/round5_pairs/provenance.json).
- Worst arm/body penetration **{maximum('arm_body_penetration_mm'):.6f} mm**; floor penetration
  **{maximum('floor_penetration_mm'):.6f} mm**; rotation step **{maximum('rotation_step_deg'):.6f}° / 25°**;
  arm angular acceleration **{maximum('angular_acceleration_deg_s2'):.6f}°/s² / 20000°/s²**.
  Blow timing error **{maximum('blow_time_error_s'):.6f} s**. No limits were loosened.
- [Strict shaft/body distance diagnostic](review/round5_clearance_diagnostic.json): zero penetration into torso/hips/legs
  on all four LODs; minimum separation **{gap:.6f} mm** excluding the intentionally gripping/releasing hands.
  This is additional authoring evidence using the shared evaluator, not a newly implemented shared gate.
- [Binding check](review/bindings_check.txt): exit 0, **no BAD line**, all three runtime GLBs.
- [Viewer check](review/viewer_check.json): **27 tier/clip switches**, zero failures or console errors; owned Chrome
  processes stopped. Front, side and three-quarter recovery renders inspected.
- Strike matrix maximum difference **{pre:.9g}**, endpoint difference **{end:.9g}** versus accepted round 4.
  [Head/unchanged corpse diagnostic](review/round5_final_diagnostics.json) retains forward gaze and identical Death/Dead.

### Reproduction and ownership

`review5_motion.py` loads the accepted `work/review_round5_before/` sources and edits only Attack. Its animation
intermediate is `work/round5_animation.glb`. `review5_retime.py` transplants that action onto the accepted runtime
payload and preserves the strike samples. `review5_probe.py` / `review5_pairs.py` prepare shared-runner probes;
`review5_preview.py`, `review5_render.py`, diagnostics and `review5_records.py` produce the review package.
`gates.json` changes only the offhand's actual grip interval endpoint from old frame 52 to new frame 45.

No game launch, build, installation, assets_dev edit or commit. Native integration and captures remain orchestrator-owned.
No new Meshy work or texture repack. The accepted round-4 texture-memory cost and historical qualifications are
preserved, not reworked in this animation-only review.

## Review round 4 — accepted

[Full accepted handoff, hashes, comparisons and qualifications](work/review_round5_before/HANDOFF.md).
That handoff links the preserved review rounds 1–3.
"""
(P/'HANDOFF.md').write_text(text)
(P/'README.md').write_text("""# MM6 PeasantM4 / natm — review round 5

Cannibal / Head Hunter / Witch Doctor, male. Round 4 accepted; this is the requested Attack hold/recovery revision.
**50/100 Meshy credits spent; zero this round.**

Attack is **1.1875 s** (was 2.25 s). Frames 46–52's hold is removed; both arms and the body recover together over
12 frame intervals (0.25 s), reaching rest at frame 57. Impact remains 0.90625 s; Cast and actors.yml are unchanged.
Geometry, textures, other clips and both prop files retain the accepted content. Shared Attack gates and viewer pass.

[HANDOFF.md](HANDOFF.md) has hashes, triangle counts, checks and reproduction commands.
[Attack sheet](review/sheets/Attack.jpg), [recovery close-ups](review/round5_recovery.jpg), [viewer](review/viewer/index.html).

Recorded decisions: preserve the accepted round-4 asset; replace the delayed recovery as a whole so both arms finish
together; retain the original strike/event time and rest endpoint; keep all gate thresholds; reuse existing preview
textures without rebaking. No installs, builds, game launches or commits. Orchestrator owns native integration.
Accepted round-4 memory tradeoff and historical qualifications remain in its archived handoff.
""")
progress=read('creature_3d_progress.json');entry={'status':'handoff_ready','accepted_base':'Review round 4 accepted by user','credits_spent':0,'old_attack_duration_s':2.25,'new_attack_duration_s':57/48,'recovery_frame_intervals':[45,57],'recovery_duration_s':12/48,'impact_s':.90625,'bindings_changed':False,'files':inventory,'shared_attack_gates':main['counts'],'dense_shaft_gates':'PASS all four LODs at 48 Hz','viewer_switches':27,'next_action':'Orchestrator: integrate revised body GLB, retain unchanged props/bindings, review faster recovery and perform native checks.'}
progress.update(stage='Review round 5: Attack hold removed and simultaneous recovery checked',status='handoff_ready',review_round_5=entry,next_action=entry['next_action'],handoff={'file':'HANDOFF.md','review_round':5,**entry});(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('ROUND5_RECORDS',inventory,invariants)

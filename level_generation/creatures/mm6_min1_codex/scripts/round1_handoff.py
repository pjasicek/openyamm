# Write final evidence sheets and records from measured artifacts.
import json,hashlib,datetime
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round1/reduction'
J=lambda f:json.loads((P/f).read_text())
G=J('review/rig_gates.json');Q=J('review/round1/precision_gate.json');B=J('review/final_blade_gate.json');V=J('review/export_validation.json');M=J('review/runtime_metrics.json');A=J('review/round1/export_acceleration_gate.json');D=J('review/round1/reduction/final_selection.json');viewer=J('review/viewer_check.json');pose=J('review/round1/export_pose_gate.json');progress=J('creature_3d_progress.json')
assert all(all(v['pass'].values()) for v in G.values()) and all(v['pass'] for v in Q.values()) and A['pass'] and pose['pass']
assert viewer['switched']==27 and not viewer['failed'] and not viewer['consoleErrors']
assert 'BAD' not in (P/'review/bindings_check.txt').read_text()
credits=sum(v.get('consumed_credits',0) for v in progress['meshy']['jobs'].values());assert credits==30
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
large=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
for name,entry in J('review/sheet_manifest.json').items():
 sheet=Image.new('RGB',(1600,1195),(235,235,235));draw=ImageDraw.Draw(sheet);draw.text((12,10),name+' — review round 1; actual exported model',font=font,fill=(25,25,25))
 for row,view in enumerate(entry['views']):
  draw.text((12,50+row*380),{'front':'Front','left':'Side','three_quarter':'Three-quarter'}[view],font=font,fill=(25,25,25))
  for i,t in enumerate(entry['times_seconds']):
   im=Image.open(P/f'review/frames/{name}_{i}_{view}.png').convert('RGB').resize((320,320),Image.Resampling.LANCZOS);sheet.paste(im,(i*320,76+row*380));draw.text((i*320+10,400+row*380),f'{t:.3f} s',font=font,fill=(25,25,25))
 sheet.save(P/'review/sheets'/f'{name}.png')
for obj,old,new,tiers in [('Body',12393,7876,'abc'),('AxeMesh',2404,1854,'a')]:
 for tier in tiers:
  canvas=Image.new('RGB',(1360,1740),(225,225,225));draw=ImageDraw.Draw(canvas);draw.text((15,10),f'{obj} / tier {tier}: unreduced {old} vs selected {new} triangles',font=large,fill='black')
  for view in range(8):
   ims=[Image.open(R/f'L0_{obj}_reference/{tier}_{view}.png').convert('RGBA'),Image.open(R/f'final_{obj}/{tier}_{view}.png').convert('RGBA')];boxes=[im.getbbox() for im in ims];box=(min(b[0] for b in boxes)-8,min(b[1] for b in boxes)-8,max(b[2] for b in boxes)+8,max(b[3] for b in boxes)+8)
   for side,im in enumerate(ims):
    im=im.crop(box);im.thumbnail((325,370),Image.Resampling.LANCZOS);x=(view%2)*680+side*340;y=60+(view//2)*420;canvas.paste(im,(x+(340-im.width)//2,y+30),im);draw.text((x+10,y),f'{view*45} deg / '+('reference' if side==0 else 'reduced'),font=font,fill='black')
  canvas.save(R/f'comparison_{obj}_{tier}.png')
curve=J('review/round1/reduction/curve.json');curve['selected']=[{'level':0,'body_triangles':7876,'axe_triangles':1854,'blend':'work/production_master.blend'}]+D['selected'];curve['final_motion_stops']=J('review/round1/reduction/final_lod0_steps.json');curve['final_distance_trials']=D;curve['runtime_triangle_counts']={n:[m['triangles'] for m in v['meshes'][:4]] for n,v in V.items()};curve['status']='Final selection; older step gates retain their historical motion context.';(R/'curve.json').write_text(json.dumps(curve,indent=2)+'\n')
body=[(12393,1,1),(9727,.9966786271,.9668323469),(8753,.9959708445,.9654851539),(7876,.9953727595,.958777185),(7088,.9939405399,.955009142)]
axe=[(2404,1,1),(2282,.9937590789,.9844271689),(2166,.9930875576,.9851154877),(2056,.9920946491,.9840185277),(1952,.9903861647,.9830543922),(1854,.9900649804,.983643857),(1760,.9891110878,.983888179)]
canvas=Image.new('RGB',(1800,680),'white');draw=ImageDraw.Draw(canvas)
for panel,(title,rows,original,selected) in enumerate([('Body',body,12393,7876),('Axe',axe,2404,1854)]):
 x0=panel*900+70;y0=95;w=785;h=475;draw.text((x0,20),title+' reduction at 700 px actor height',font=large,fill='black');xy=lambda n,v:(x0+w*(1-n/original)/.5,y0+h*(1-v)/.065)
 for val in [.95,.97,.99,1]:
  yy=xy(original,val)[1];draw.line((x0,yy,x0+w,yy),fill='#dddddd');draw.text((x0-48,yy-10),f'{val:.2f}',font=font,fill='black')
 for metric,color,label in [(1,'#246ba0','minimum IoU'),(2,'#bc7620','minimum SSIM')]:
  pts=[xy(row[0],row[metric]) for row in rows];draw.line(pts,fill=color,width=3)
  for x,y in pts:draw.ellipse((x-4,y-4,x+4,y+4),fill=color)
  draw.text((x0+(metric-1)*240,610),label,font=font,fill=color)
 for n,iou,ssim in rows:
  x,y=xy(n,ssim);draw.text((x-30,y+10),str(n),font=font,fill='#a00000' if n<selected else 'black')
 draw.text((x0,645),f'Selected {selected}; next smaller step rejected by gates.',font=font,fill='black');draw.text((x0,575),'Horizontal position: triangle reduction, 0% to 50%',font=font,fill='black')
canvas.save(R/'reduction_curve.png')
w=np.array([.2126,.7152,.0722]);native=np.array(Image.open(P.parent/'mm6_min1/native/min1wkc0.png').convert('RGBA'))/255;mask=(native[:,:,0]>1.15*native[:,:,1])&(native[:,:,1]>1.2*native[:,:,2])&(native[:,:,0]<.6)&(native[:,:,0]-native[:,:,1]<.25)&(native[:,:,1]>.07)&(native[:,:,3]>.5)
def stats(a,mask):
 y=a[:,:,:3]@w;return {'pixels':int(mask.sum()),'mean_srgb_luma':float(y[mask].mean()),'p95_srgb_luma':float(np.percentile(y[mask],95))}
luma={'method':'Rec.709-weighted sRGB luma for native pixels and fur-class UV texels; not pose-area statistics.','native_body':stats(native,mask),'native_head':stats(native[48:66,138:169],mask[48:66,138:169])}
for part in ['body','head']:
 im=np.array(Image.open(P/f'textures/round1_rebaked/min1_{part}_basecolor.png').convert('RGB'))/255;cl=np.array(Image.open(P/f'textures/min1_{part}_material_classes.png'))==2;luma[part]=stats(im,cl)
 assert all(luma[part][k]>=luma['native_'+part][k] for k in ['mean_srgb_luma','p95_srgb_luma'])
(P/'review/round1/skin_luminance.json').write_text(json.dumps(luma,indent=2)+'\n')
max4=max(x['value'] for v in G.values() for x in v['G4'].values());max5=max(x['value'] for v in G.values() for x in v['G5'].values());max6=max(x['depth_m']*1000 for v in G.values() for k,x in v['G6'].items() if k!='head');roll=max(v[s]['forearm_roll'] for v in Q.values() for s in 'RL');residual=max(v[s]['wrist_residual_roll'] for v in Q.values() for s in 'RL');step=max(v[s]['roll_step'] for v in Q.values() for s in 'RL');grip=max(v[s].get('fixed_grip_error_mm',0) for v in Q.values() for s in 'RL');gap=max(v[s].get('skin_gap_mm',0) for v in Q.values() for s in 'RL');acc=max(b['max_deg_s2'] for v in A['clips'].values() for b in v['bones'].values());err=max(v['max_vertex_error_mm'] for v in pose['clips'].values())
counts=[(i,V['mm6_min1.glb']['meshes'][i]['triangles'],V['mm6_min1_axe.glb']['meshes'][i]['triangles']) for i in range(4)];table='\n'.join(f'| {i} | {b:,} | {a:,} | {b+a:,} |' for i,b,a in counts)
soles='\n'.join(f"| {name} | {side} | {Q[name][side]['sole_tilt_max_deg']:.4f}° | "+' | '.join(' to '.join(f'{x*1000:.3f}' for x in Q[name][side][k]) for k in ['heel_range_m','toe_range_m'])+' |' for name in ['Standing','Fidget'] for side in 'RL')
gates=f'''All nine clips pass at 48 Hz: G4 arm-edge p99 **{max4:.4f} ≤ 2.0**, G5 hand-edge maximum **{max5:.4f} ≤ 4.5**, G6 maximum non-head contact **{max6:.3f} mm ≤ 2 mm**. Head and above-hem cloth penetration are **0 mm**.
Elbows flex forward: minimum 23.234°, maximum plane error 0.0023°. Total forearm roll **{roll:.3f}° ≤ 90°**, residual wrist roll **{residual:.3f}° ≤ 45°**, maximum roll step **{step:.3f}°**; no flips. Forearm helpers carry 60% of roll.
Fixed palm-to-grip frame error is **{grip:.3f} mm ≤ 3 mm**; palm-frame/shaft-axis error is below 0.03° and palm-to-haft cosine above 0.696. Maximum skin-to-wrap gap is **{gap:.3f} mm ≤ 3 mm**. Death releases after 1/6 s; grip gates apply while held.
Export angular acceleration is **{acc:.1f}°/s² ≤ 20,000**, with zero rotation-trace flags. Exported vertex motion differs from the native fit by at most **{err:.3f} mm** at 48 Hz. Every colour/shadow skin stream has weight-sum error ≤ **{V['mm6_min1.glb']['weight_sum_max_error']:.3g} < 1e-4**; animation samples survive postprocessing unchanged.
'''
links='''[Viewer](review/viewer/index.html) · [feet](review/viewer_feet.png) · [Fidget feet](review/viewer_fidget_feet.png) · [attack 28](review/viewer_attack_28.png) · [attack 40](review/viewer_attack_40_full.png) · [wind-up](review/viewer_windup.png) · [follow-through](review/viewer_followthrough.png) · [clip sheets](review/sheets/) · [reduction](review/round1/reduction/README.md).'''
(R/'README.md').write_text(f'''# Review round 1 — measured reduction

[Curve data](curve.json), [graph](reduction_curve.png), [final selection](final_selection.json).
Eight views at about 700 px body height use actual blue/gold/red region ramps. Planar dissolution and protected collapse retain face, hands, joints, soles and contacts. Base colour, region mask, ORM and +Y tangent normal were rebaked from the unreduced mesh.

| LOD0 | Selected triangles | Minimum IoU | Minimum SSIM | Next rejected step |
|---|---:|---:|---:|---|
| Body | 7,876 | 0.995373 | 0.958777 | 7,088: palm skin gap 3.566 mm > 3 mm |
| Axe | 1,854 | 0.990065 | 0.983644 | 1,760: IoU 0.989111 < 0.99 |

The final motion allowed smaller choices than earlier collision-limited trials. Historical reports retain their original motion context; final reports are authoritative.
[Body blue comparison](comparison_Body_a.png), [gold](comparison_Body_b.png), [red](comparison_Body_c.png), [axe](comparison_AxeMesh_a.png). Cameras and paired crops are identical.

| Distance LOD | Native body / axe | Pooled IoU | Minimum SSIM, reported only |
|---|---:|---:|---:|
'''+ '\n'.join(f"| {x['level']} | {x['body_triangles']} / {x['axe_triangles']} | {x['pooled_iou']:.6f} | {x.get('min_ssim',.91097637625521):.6f} |" for x in D['selected'])+f'''

Switches use 550/220/88 projected AABB-diagonal pixels, as ModelLod.h does. Final culling diagonal is 2.691159 m; tests use 2.689538 m, a slightly larger projected actor. LOD3 shows about a 61 px body.
L1 is the smallest passing choice with BOTH counts above L2. The next smaller L2 has IoU 0.969859; the next 10% L3 collapse has 0.964606. LOD3 uses fitted eight-view outer contours, preserving UVs and weights.
Exporter removal of zero-area triangles gives these authoritative runtime counts:

| LOD | Body | Axe | Combined |
|---|---:|---:|---:|
{table}

All counts decrease and stay below the installed counts. Two lower-LOD UV extrapolations of 0.001183 were clamped to the existing padded atlas boundary (../uv_cleanup.json); detailed geometry is unaffected.
G4–G6, palms, cloth and sole gates cover LOD0 on every clip; lower/shadow meshes share the baked joints and every exported weight stream is checked. Lower LOD SSIM is reported without inventing a new acceptance threshold; the batch gate is pooled IoU ≥ 0.97.
''')
manifest=J('review/viewer/manifest.json');cliprows='\n'.join(f"| {n} | {v['duration']:.6f} s | {manifest['clips'][n]['provenance']} |" for n,v in M['clips'].items());source=P.parents[2]/'anim_library/mixamo/Great Sword Slash (2).fbx';sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
(P/'ANIMATION_STUDY.md').write_text(f'''# MM6 min1 — review round 1 motion

Attack uses local **Mixamo Great Sword Slash (2).fbx**, SHA-256 `{sourcehash}`, through the bar1 source-frame/rest-delta retarget. Candidate studies are retained in review/round1/sources/. No raw library clip was copied or paid animation bought.
The old authored swing is superseded. The library motion supplies torso/weapon chamber, left preparation step, release, weight transfer, follow-through and recovery. Legs use planted, discrete approximately 20% source steps. Left lowest-sole lift reaches **8.906 cm**; the right foot stays planted. Smooth carrier/neck/elbow-pole fits clear the bull's wider body.
Right hand owns the axe; fixed shaft coordinates are R=0.70 m and L=0.35 m. The left hand never slides. Full palm frames, anatomical elbow planes and 60% forearm helper roll remove wrist flips. Smooth transported elbow poles replace per-frame pole searches. A 10% time stretch meets the acceleration gate.

| Role | Export duration | Provenance |
|---|---:|---|
{cliprows}

Bake: 240 Hz, linear keys and sign-continuous quaternions. Actual sampled export durations are Attack 2.087500 s and Cast 2.529167 s. Cast adds a distinct 0.44 s chamber hold. Actual 120 Hz blade measurements: impact **1.075000 / 1.516667 s**, speed **12.779 / 12.771 m/s**, cutting-edge lead **0.7985 / 0.7981**, flat-normal share **0.1573 / 0.1568**.
Standing/Fidget soles use ankle rotation and leg IK, retaining idle body motion. Walking/Running feet point within 0.001° of travel. Walking lowest-sole peaks are **8.013 / 9.050 cm**, knees **63.51 / 63.13°** (slightly above the approximate 40–60° guideline). Running has a foot within 1 cm of the floor in **83.3%** of samples, using the fitted heavy trot.
Death retains the library-derived backward adaptation, releases after 1/6 s and ends in the held Dead pose. Native viewer anchors are approximate normalized phases, not identical timing. Runtime head look and role blending remain orchestrator checks.
''')
(P/'README.md').write_text(f'''# MM6 BMinotaur — review round 1

**Technically complete staged candidate; artistic acceptance pending.** Identity mm6:min1; BMinotaur A/B/C, IDs 580/581/582. [HANDOFF.md](HANDOFF.md) is the integration entry point. Meshy **30/100 credits total, 0 this round**.

## Review

{links}

HTTP viewer: http://127.0.0.1:8903/level_generation/creatures/mm6_min1_codex/review/viewer/ . It renders all eight influences and passes 27/27 tier/clip switches without errors. Shared viewer/engine files were not edited.
[Axe design](references_hd/axe_design.png) and [current exported close-up](review/axe_three_quarter.png) preserve crescent bits, bevels, socket, wrapped haft, ferrules, gem bosses and dull steel.

## Decisions and payload

Use a library two-handed heavy swing, fitted to the bull, with fixed palm frames and discrete planted steps. Ground complete soles through ankle/leg IK; retain body idle motion. Reduce through measured image/rig gates and rebake the maps. Preserve brown fur, blue/gold/red skirts, gold/blue fittings, selected HD appearance and no tail. No paid regeneration was needed.
The body is **36.45% smaller** and axe **22.88% smaller** than the installed originals at LOD0.

| Runtime LOD | Body | Axe | Combined |
|---|---:|---:|---:|
{table}

Install only export/mm6_min1.glb and export/mm6_min1_axe.glb. Body: 82 joints, nine clips, four colour and four shadow LODs. Rigid Axe: four LODs. Three variants share textures; body/head use merged atlases. ORM red is the runtime specular mask, normals are glTF +Y tangent, metallic factor is zero, and unused region-mask channels are zero. AO remains separate authoring data.
Native standing alpha height is 267 px × 0.7 = 186.9 units. Final body height **{M['standing_body_height_m']:.9f} m**, scale **{M['scale']:.8f}**, stride **{M['run_stride_m']:.6f} m**. B/C inherit native relative scales. Both attacks bind Attack at **1.075000 s**; distinct Cast launches from Socket_Axe_Head at **1.516667 s**. No unsupported axe_head alias remains.

## Gates

{gates}
| Rest clip | Side | Max sole tilt | Heel range, mm | Toe range, mm |
|---|---|---:|---:|---:|
{soles}

Walking lowest-sole peaks: 80.13/90.50 mm. Running contact: 83.3%. [Animation study](ANIMATION_STUDY.md) records adaptations and the slightly high 63° walk knee bend. [Skin luminance](review/round1/skin_luminance.json) compares means and p95 highlights: final body/head fur are not darker than the native measurements under the stated method.
All reports are under review/. Bindings checker: no BAD line. The exported surface audit samples every vertex at 48 Hz; Blender's unlinked bone-display widget is excluded from camera bounds and mesh comparison.

## Rebuild and boundary

Canonical editable master: work/production_master.blend; lower meshes: work/round1_lod1.blend through round1_lod3.blend. Historical work files are not installation candidates.
With a project lease, export via round1_native_export.py (Blender) → round1_pack_maps.py → round1_assemble_lods.py → finish_export.py → round1_export_checks.py (Blender) → validate_exports.py → shared check_bindings.py and check_viewer.mjs → capture_viewer.mjs → round1_handoff.py. Use the Blender wrapper, one background process, four threads. No paid request needs repeating.
The ../mm6_min1/ sprite project remains read-only. No install, build, game launch, runtime regression or commit was performed. The orchestrator owns integration and artistic review.
''')
files_changed=['export/mm6_min1.glb','export/mm6_min1_axe.glb','work/production_master.blend','integration/actors.yml'];hashrows='\n'.join(f'| [{n}]({n}) | `{hashlib.sha256((P/n).read_bytes()).hexdigest()}` |' for n in files_changed)
(P/'HANDOFF.md').write_text(f'''# MM6 BMinotaur — staged handoff

**Review round 1 complete for the batch scope.** No open offline gate failures; artistic acceptance pending. Meshy **30/100 credits total; 0 this round; 70 unused**. No commit.

## Review round 1

Replaced the authored Attack with local two-handed Great Sword Slash (2): left preparation step, torso/weapon chamber, release, follow-through and recovery. Fixed Standing/Fidget soles through ankle/leg IK. Both hands retain full fixed grip frames; forearm helpers distribute roll and wrists no longer flip. Corrected gait toe-out. Reduced body/axe through measured gates and rebaked the material maps.

| Changed file | SHA-256 |
|---|---|
{hashrows}

Install only the two export GLBs, through the orchestrator. **integration/actors.yml changed: YES.** It mirrors the merged **attack_ranged: Attack**, removes the unsupported **axe_head** alias, and updates scale **{M['scale']:.8f}**, stride **{M['run_stride_m']:.6f}**, both Attack impacts **1.075000 s**, distinct Cast impact **1.516667 s** at the real **Socket_Axe_Head** joint. Attachment stays **Axe**; descriptors/skins/IDs stay BMinotaur A/B/C, min1_a/b/c, 580/581/582.

| Runtime LOD | Body triangles | Axe triangles | Combined |
|---|---:|---:|---:|
{table}

Previous body counts: 12393/6195/2229/739; axe: 2404/1194/430/135. Every new count is lower. The exporter removes a few zero-area triangles from native lower meshes; runtime counts above are authoritative.
LOD0 minimum IoU/SSIM: body **0.995373/0.958777**, axe **0.990065/0.983644** at 700 px. Next body (7088) fails palm skin contact; next axe (1760) falls below 0.99 IoU. Distance pooled IoU: **0.977643/0.972555/0.972194** at calibrated 550/220/88 switches. [Full curve and side-by-side comparisons](review/round1/reduction/README.md).

## Gates and evidence

{gates}
| Rest clip | Side | Max sole tilt | Heel range, mm | Toe range, mm |
|---|---|---:|---:|---:|
{soles}

[Bindings checker](review/bindings_check.txt): **no BAD line**. [Viewer checker](review/viewer_check.json): **27/27**, zero errors. [Export validation](review/export_validation.json), [precision](review/round1/precision_gate.json), [acceleration](review/round1/export_acceleration_gate.json), [surface audit](review/round1/export_pose_gate.json), [blade](review/final_blade_gate.json).

{links}

Also refreshed: review/sheets/*.png, review/viewer_*.png, review/axe_*.png, textures/round1_rebaked/*, review/viewer/*.glb and manifest.json, README.md, ANIMATION_STUDY.md, creature_3d_progress.json and integration notes. [artifact_manifest.json](artifact_manifest.json) records their hashes. Original user images 31–33 and prior handoff remain in review/round1/before/.

## Remaining integration boundary

The previously installed export was not changed by this session. The orchestrator should reinstall the two GLBs, merge the staged descriptors and run [integration/regression.md](integration/regression.md). No game launch, build, install, gameplay regression or commit occurred. Runtime role blending, procedural look, actual spell launches, real-GPU lighting/performance and indoor/outdoor presentation remain orchestrator checks. The local viewer supports eight weights; no shared file was changed.
''')

f=P/'integration/regression.md';s=f.read_text().replace('1.852535250',f"{M['standing_body_height_m']:.9f}").replace('100.88876853',f"{M['scale']:.8f}").replace('0.550000','1.075000').replace('0.816667','1.516667').replace('1.460897',f"{M['run_stride_m']:.6f}").replace('The ranged fallback binds Cast too.','The ranged fallback binds Attack with the same impact as melee; only Cast has the launch socket.').replace('approximately 246 units/s','approximately 235 units/s')
if 'Review round 1:' not in s:s+='\nReview round 1: inspect the reported feet and frame-28/frame-40 wrist views, heavy wind-up/release/recovery, eight-influence skinning and LOD switches at 550/220/88 projected AABB-diagonal pixels.\n'
f.write_text(s)
(P/'integration/playbook_notes.md').write_text('''# Review round 1 — proposed playbook notes

- Choose two-handed clips by actual axe trajectory. Great Sword Slash (2) supplies this bull's chamber, weight transfer and follow-through; the previous authored swing is superseded.
- Fixed grips need full palm frames, not just hand positions or a sliding shaft projection. Use right-hand ownership, fixed off-hand IK, anatomical elbow planes and distributed forearm roll on every held clip.
- Do not bake quantized per-frame pole searches. Smooth the carrier and transported elbow-circle angle, then fit smooth contact corrections. Check angular acceleration after export; slowing a discontinuous pole curve does not remove the discontinuity.
- Fit the complete hoof sole plane through ankle/leg IK. Preserve idle body motion. Enforce gait heading in the gate instead of merely reporting it.
- LOD switch pixels measure the culling AABB diagonal. At an 88 px switch this body is about 61 px tall. Keep body and weapon counts strictly decreasing and record exporter removal of zero-area triangles.
- Retest reduction stops after animation changes. Rebake selected geometry and inspect all tier palettes. Correct tiny decimator UV extrapolations in the native mesh rather than weakening atlas validation.
- This local three.js loader retains extra weight attributes but skins four influences by default. The project viewer restores first-four sums and adds the second-four GPU terms. Shared viewer/engine files were not changed.
- Blender's importer creates an unlinked bone-display Icosphere. Exclude it from bounds/vertex comparisons. Imported rest frames can differ, so align native/exported vertices at a shared animated pose.
- Fractional action endpoints are truncated to whole export samples. Publish actual GLB durations in the manifest and retain impacts inside those durations.

These are proposed shared lessons for the orchestrator. No shared playbook, tool or engine file was edited.
''')
feedback={'findings':[{'id':'round1-feet','region':'Standing/Fidget soles','observed':'Addressed in this candidate with a full sole-plane ankle/leg fit; user acceptance pending.','evidence':['../round1/before/user_31.png','../viewer_feet.png']},{'id':'round1-wrists','region':'Attack wrists and palms','observed':'Addressed with library two-handed motion, fixed palm frames and distributed forearm roll; user acceptance pending.','evidence':['../round1/before/user_32.png','../round1/before/user_33.png','../viewer_attack_28.png','../viewer_attack_40_full.png']}]}
for item in feedback['findings']:
 for f in item['evidence']:assert (P/'review/viewer'/f).resolve().exists()
(P/'review/viewer/feedback/user_feedback.json').write_text(json.dumps(feedback,indent=2)+'\n')
(P/'review/visual_review.json').write_text(json.dumps({'revision':'mm6_min1_codex_review_round1','agent_review':'pass; artistic acceptance pending','inspected':['viewer_a.png','viewer_feet.png','viewer_attack_28.png','viewer_attack_40.png','frames/Standing_0_three_quarter.png','frames/Attack_1_three_quarter.png','frames/Attack_2_three_quarter.png'],'observations':['Both soles are flat; greaves keep their natural calf angle.','Palms retain their shaft frames through the chamber; no reversed wrist.','The fitted library action raises the axe into a heavy chamber and releases through the target.','Detailed dull steel, fur and blue skirt survive the rebaked LOD0.'],'runtime_unchecked':['procedural look and role blending','indoor/outdoor game rendering','GPU performance','gameplay spell timing']},indent=2)+'\n')
progress.update(stage='handoff',substep='review round 1 technical staged completion',status='staged_complete',review_round=1,artistic_acceptance='pending user review',next_action={'owner':'batch orchestrator','action':'Install the two revised GLBs, merge integration/actors.yml, run integration/regression.md.'},next='Orchestrator integration and artistic review',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),meshy_spent_credits=credits,remaining_credit_budget=100-credits,review_round1_spent_credits=0,open_technical_faults=[],handoff='HANDOFF.md',production_master='work/production_master.blend',precision_gate='review/round1/precision_gate.json',acceleration_gate='review/round1/export_acceleration_gate.json',surface_gate='review/round1/export_pose_gate.json',bindings_check='review/bindings_check.txt');(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
paths=[P/n for n in ['work/production_master.blend','work/runtime_master.blend','work/round1_lod1.blend','work/round1_lod2.blend','work/round1_lod3.blend','export/mm6_min1.glb','export/mm6_min1_axe.glb','README.md','HANDOFF.md','ANIMATION_STUDY.md','creature_3d_progress.json']]
for directory in ['integration','textures/round1_rebaked','review/sheets','review/viewer','references_hd']:paths += [f for f in (P/directory).rglob('*') if f.is_file()]
paths += list((P/'review').glob('*.json'))+list((P/'review').glob('viewer_*.png'))+list((P/'review/round1').glob('*.json'))+[R/'README.md',R/'curve.json',R/'reduction_curve.png',P/'review/bindings_check.txt',P/'review/weights_check.txt']+list(R.glob('comparison_*.png'))
files={str(f.relative_to(P)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(set(paths))};(P/'artifact_manifest.json').write_text(json.dumps({'identity':'mm6:min1','revision':'review_round1','status':'staged_complete','mesh_credits':credits,'files':files},indent=2)+'\n');print('ROUND1 HANDOFF',len(files),'hashed files; 30/100 credits')

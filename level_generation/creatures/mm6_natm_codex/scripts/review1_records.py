"""Bind the round-one handoff and review evidence to the final staged files."""
import json,hashlib,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.path.insert(0,str(P.parents[2]/'tools'))
from reduction_metrics import compare
from merge_head_material import read_glb,image_of,TEXTURE_SLOTS,slot
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
main=json.loads((P/'review/runtime_gates/gates.json').read_text());floor=json.loads((P/'review/floor_gates/gates.json').read_text());assert main['status']==floor['status']=='PASS'
for asset in main['assets']:assert sha(Path(asset['path']))==asset['sha256']
source=json.loads((P/'review/round1_floor_provenance.json').read_text());assert sha(P/source['source'])==source['source_sha256']
old=json.loads((P/'review/round1_before.json').read_text());assert sha(P/'integration/actors.yml')==old['integration/actors.yml']['sha256']
info=json.loads((P/'export/export_info.json').read_text());counts=json.loads((P/'export/lods.json').read_text());inventory={};texture_audit={}
for name in ['mm6_natm.glb','mm6_natm_spear.glb','mm6_natm_buckler.glb','mm6_natm.blend']:
 f=P/'export'/name;inventory[name]={'bytes':f.stat().st_size,'sha256':sha(f)}
for kind,name,node in [('body','mm6_natm.glb','Natm'),('spear','mm6_natm_spear.glb','Spear'),('buckler','mm6_natm_buckler.glb','Buckler')]:
 d,b=read_glb(P/'export'/name);assert len(d['images'])==4;mi=next(n['mesh']for n in d['nodes']if n.get('name')==node);chain=[mi]+d['meshes'][mi]['extras']['openyamm_lods'];sets=[]
 for index in chain:
  pr=d['meshes'][index]['primitives'][0];mat=d['materials'][pr['material']];sets.append([slot(mat,path)['index']for path in TEXTURE_SLOTS])
 assert all(s==sets[0]for s in sets)
 shadows=d['meshes'][mi]['extras'].get('openyamm_shadow_lods',[])
 for index in shadows:
  for pr in d['meshes'][index]['primitives']:assert d['materials'][pr['material']].get('alphaMode','OPAQUE')=='OPAQUE'
 texture_audit[kind]={'images':4,'texture_indices_by_lod':sets,'image_sizes':[image_of(d,b,i)[0].size for i in sets[0]],'shadow_meshes':len(shadows),'shadow_alpha_mode':'OPAQUE'if shadows else None}
layout=json.loads((P/'export/textures_shared/layout.json').read_text());image_inventory={str(f.relative_to(P)):{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted((P/'export/textures_shared').rglob('*.png'))}
manifest={'files':inventory,'descriptors':['PeasantM4 A','PeasantM4 B','PeasantM4 C'],'triangles':counts,'animations':info['clips'],'scale':103.7995785021,'bones':78,'review_round':1,'textures':texture_audit,'image_files':image_inventory,'bindings_sha256':sha(P/'integration/actors.yml')};(P/'export/manifest.json').write_text(json.dumps(manifest,indent=2));(P/'review/round1_texture_audit.json').write_text(json.dumps(texture_audit,indent=2))
root=P/'review/reduction';metrics={};comparisons=root/'round1_comparisons';comparisons.mkdir(exist_ok=True)
for level,size in [(0,700),(1,550),(2,220),(3,88)]:
 rows={};I=U=0;before=[]
 for f in sorted((root/f'round1_lod{level}_{size}').glob('*.png')):
  ref=root/f'final_reference{size}'/f.name;row=compare(ref,f);a=np.array(Image.open(ref))[:,:,3]>127;b=np.array(Image.open(f))[:,:,3]>127;ii=int((a&b).sum());uu=int((a|b).sum());I+=ii;U+=uu;row.update(intersection_pixels=ii,union_pixels=uu);rows[f.name]=row
  if level==0:before.append(compare(root/'final_lod0_700'/f.name,f)['ssim'])
 result={'actor_pixels':size,'minimum_iou':min(r['iou']for r in rows.values()),'pooled_iou':I/U,'minimum_ssim_against_unreduced_or_near':min(r['ssim']for r in rows.values()),'views':rows}
 assert result['minimum_iou']>=.99 if level==0 else result['pooled_iou']>=.97
 if level==0:
  result['minimum_ssim_against_accepted_before_round1']=min(before);assert min(before)>=.95
  result['appearance_verdict']='Visually equivalent to the accepted pre-review export; same geometry and pixel density. Original reduction qualification is retained separately.'
 metrics[str(level)]=result
 for i in range(8):
  source=root/f'final_lod{level}_{size}'/f'natm_b_{i}.png';target=root/f'round1_lod{level}_{size}'/f'natm_b_{i}.png';page=Image.new('RGB',(1640,852),(48,48,48));draw=ImageDraw.Draw(page)
  for file,x in [(source,0),(target,820)]:
   im=Image.open(file).convert('RGBA');page.paste(im,(x,32),im)
  draw.text((12,10),f'Before review | LOD{level} | {size}px actor',fill='white');draw.text((832,10),'Review round 1 | shared padded textures',fill='white');page.save(comparisons/f'lod{level}_view{i}.jpg',quality=94)
(root/'round1_metrics.json').write_text(json.dumps(metrics,indent=2))
# Three views, seven samples per clip, from the actual packed-runtime preview.
for role,row in info['clips'].items():
 page=Image.new('RGB',(2100,1228),(32,32,32));d=ImageDraw.Draw(page);d.text((12,10),f'Review round 1 | {role} | {row["duration"]:.6f}s | final runtime GLBs',fill='white')
 for j,view in enumerate(['front','left','three_quarter']):
  for i,t in enumerate(np.linspace(0,row['duration'],7)):
   im=Image.open(P/f'review/final/{role}_{i:02}_{view}.png').convert('RGB');im.thumbnail((300,370));x=i*300+(300-im.width)//2;y=42+j*390;page.paste(im,(x,y));d.text((i*300+8,y+370),f'{view}: {t:.3f}s',fill='white')
 page.save(P/f'review/sheets/{role}.jpg',quality=93)
gates=main['gates'];maximum=lambda name:max(r['worst']for r in gates if r['gate']==name and isinstance(r.get('worst'),(int,float)))
floor_worst=max(r['worst']for r in floor['gates']if r['gate']=='floor_penetration_mm');floor_dead=max(r['worst']for r in floor['gates']if r['gate']=='floor_penetration_mm'and r['clip']=='Dead')
new_bytes=sum(v['bytes']for k,v in inventory.items()if k.endswith('.glb'));old_bytes=sum(v['bytes']for k,v in old.items()if k.endswith('.glb'));percent=100*(1-new_bytes/old_bytes)
rows='\n'.join('| '+name+' | '+str(data['bytes'])+' | `'+data['sha256']+'` |'for name,data in inventory.items())
trirows='\n'.join(f'| {i} | {counts["body"][i]:,} | {counts["spear"][i]:,} | {counts["buckler"][i]:,} |'for i in range(4))
texrows='\n'.join(f'| {kind} | {v["size"][0]} × {v["size"][1]} | {v["old_total_texels_per_map"]:,} | {v["shared_texels_per_map"]:,} |'for kind,v in layout.items())
gaterows='\n'.join(f'| {label} | {maximum(key):.6g} |'for label,key in [('Arm stretch p99','arm_stretch_p99'),('Arm stretch maximum','arm_stretch_max'),('Hand stretch maximum','hand_stretch_max'),('Elbow plane, degrees','elbow_plane_deg'),('Forearm roll, degrees','forearm_roll_deg'),('Upper-arm raw roll, degrees','upper_arm_roll_deg'),('Raw wrist roll, degrees','wrist_roll_deg'),('Angular acceleration, degrees/s²','angular_acceleration_deg_s2'),('Grip gap, mm','grip_gap_mm'),('Grip penetration, mm','grip_penetration_mm'),('Prop/body penetration, mm','prop_body_penetration_mm'),('Arm/body penetration, mm','arm_body_penetration_mm'),('Cloth penetration, mm','cloth_penetration_mm'),('Sole/floor penetration, mm','floor_penetration_mm'),('Rest sole height, mm','rest_sole_height_mm'),('Rest sole tilt, degrees','rest_sole_tilt_deg'),('Foot yaw, degrees','foot_yaw_deg'),('Walking lift maximum, mm','walking_lift_max_mm'),('Running airborne height, mm','running_airborne_mm'),('Blow timing error, seconds','blow_time_error_s'),('Weight-sum error','weight_sum_error')])
handoff=f"""# MM6 PeasantM4 / natm — batch handoff

Review round 1 is technically ready for orchestrator integration. Three tiers, nine clips, **78 bones**, four colour LODs and four **opaque** shadow LODs. User artistic acceptance remains unrecorded.

**50 / 100 Meshy credits spent; this round spent zero.** No commit, shared registry edit, asset installation, build or game launch. The original ../mm6_natm sprite-restoration project remains read-only.

## Review round 1

- Fixed the registry rejection: every shadow primitive now uses **Natm_Shadow_Opaque**. Colour LOD3 retains its feather MASK material. Shadow geometry is an opaque proxy; it no longer copies the colour alpha material.
- Replaced 16 images per GLB with **four shared images per GLB**. All four colour levels reference the exact same texture indices. LOD1 reuses the near charts; far envelope charts occupy the same shared atlases. Islands have **16 px dilated margins**, with **1.0× texel density**. Chart rotations also rotate tangent-normal XY channels with the runtime's +Y-up convention.
- Fixed the back-feather fall/corpse penetration with five paired deformation helpers. Each group flattens against the ground; the helpers remain beneath their original owner bones for upper-body layering. Skin, cloth and prop articulation are preserved. A smooth **8 mm fall-only root clearance** also brings the coarse skin/shadow proxies within the 2 mm floor limit. Standing, Fidget and locomotion have no added root offset.
- Dead is a constant two-frame hold of the Death endpoint. Five float32 endpoints are rounded down by less than one microsecond to prevent the shared runner inventing a near-zero final audit interval. The current run uses the **unmodified shared runner directly**.
- Rebuilt the viewer and all nine front/side/three-quarter clip sheets from the final packed GLBs. [Corpse floor view](review/final/corpse_floor_1.png), [other floor views](review/final/), [sheets](review/sheets/).
- **integration/actors.yml did not change.** SHA256: `{sha(P/'integration/actors.yml')}`. Descriptor blocks and impact/socket/scale settings remain the prior handoff's exact values.

## Final files and hashes

Install only the three named runtime GLBs. Other GLBs in the project are generation/review intermediates. The editable near source is the pre-atlas authoring checkpoint; the deterministic packing scripts produce the final shared UV atlases.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
{rows}

[Export manifest](export/manifest.json) also records the twelve shared PNG filenames/hashes, animation durations, counts and texture references. The final authoring LODs are work/runtime_lod0.blend through runtime_lod3.blend.

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
{trirows}

All triangle counts are unchanged from the installed pre-review export. The body reduction history remains in [the original curve](review/reduction/curve.png) and [original qualification metrics](review/reduction/final_metrics.json); no geometry-reduction search was repeated.

## Texture allocation

The three final GLBs total **{new_bytes:,} bytes**, down **{percent:.2f}%** from {old_bytes:,}. Image count falls from 48 to 12 across the three assets. Each asset has one shared base-colour / normal / specular-roughness-metal / region-mask set, with three material-ramp variants.

| Asset | Shared atlas | Previous total texels per map across LODs | Shared texels per map |
|---|---:|---:|---:|
{texrows}

**Tradeoff:** preserving accepted texel density while adding 16 px margins increases decoded atlas area. The image/file count and GLB bytes fall; this is **not a decoded GPU-memory reduction**. No per-LOD maps are referenced by the final GLBs. [Packing layout](export/textures_shared/layout.json) and [shared-texture/opaque-shadow audit](review/round1_texture_audit.json) make this explicit. Normal maps retain detail, MR red remains the engine's specular mask, and native equipment/skin ramps remain shared.

## Validation on these hashes

- [Full shared report](review/runtime_gates/gates.md): **{main['counts']['PASS']:,} PASS, zero FAIL, zero UNVERIFIED** ({main['counts']['INFO']} INFO, {main['counts']['N/A']} N/A).
- [Floor shared report](review/floor_gates/gates.md): **{floor['counts']['PASS']:,} PASS, zero FAIL, zero UNVERIFIED**. This probe uses the exact runtime geometry and Death/Dead animation, selecting the entire solid body including feathers as the floor region at every colour and shadow LOD. Maximum penetration **{floor_worst:.4f} mm / 2 mm**; Dead **{floor_dead:.4f} mm**. Cloth retains its separate collision test. [Probe derivation and source hash](review/round1_floor_provenance.json).
- `python3 output/codex_batch/check_bindings.py level_generation/creatures/mm6_natm_codex/integration/actors.yml`: exit 0, **no BAD line**, including shadow opacity and all three files' weights. [Receipt](review/bindings_check.txt).
- [Viewer checker](review/viewer_check.json): **27 tier/clip switches, zero console errors or failed switches**. [Viewer](review/viewer/index.html). Its server and checker Chrome were closed.

| Full runtime measurement | Worst value |
|---|---:|
{gaterows}

Audit intent is in [gates.json](gates.json) and [notes](review/gate_intent.md). Existing explicit limits remain: raw upper-arm/wrist roll 90 degrees for the source-frame twist-helper rig, actual skin deformation checks mandatory, exterior loincloth panels, and the previously accepted approximate LOD3 ratio cap 0.102. Historical distal-wrist evidence is retained; this round does not install a local gate implementation.

[New eight-view comparisons](review/reduction/round1_comparisons/) and [metrics](review/reduction/round1_metrics.json): near silhouette minimum **{metrics['0']['minimum_iou']:.6f}**; near minimum SSIM against the accepted pre-review export **{metrics['0']['minimum_ssim_against_accepted_before_round1']:.6f}**. Far pooled IoU at 550 / 220 / 88 px is **{metrics['1']['pooled_iou']:.6f} / {metrics['2']['pooled_iou']:.6f} / {metrics['3']['pooled_iou']:.6f}**. The fresh near-to-unreduced SSIM is {metrics['0']['minimum_ssim_against_unreduced_or_near']:.6f}; direct before/after visual equivalence is the texture-change acceptance basis, with no triangle change.

## Orchestrator integration

Use the unchanged [actors.yml blocks](integration/actors.yml) for PeasantM4 A/B/C (merged ids 616/617/618), the [regression proposal](integration/regression.md), and these three new GLBs. Body scale is 103.7995785021, yaw −π/2; B/C reference PeasantM4 A. Attack impact: 0.489583333 s. Distinct Cast impact: 0.447916667 s from Socket_LeftPalm. Props attach to Spear / Buckler. Native skin palettes remain 795 / 796 / 797.

The reported shadow-opacity and feather-floor faults are resolved. The shared-atlas decoded-memory tradeoff above remains material. Pale feather styling versus the darker original back sprite still awaits artistic review. Native installation, registry activation, indoor/outdoor captures, save/load regression and hardware performance remain **unrun by batch instruction** and belong to the orchestrator.

Reproduce: run scripts/quick_export.py with the Blender/workspace wrapper, then scripts/runtime_pack.py, scripts/review1_finalize.py, scripts/review1_preview_source.py and scripts/make_viewer.py under the workspace guard. Run the shared gates/run_gates.sh directly for export/mm6_natm.glb with gates.json and for review/round1_floor.glb with review/round1_floor.gates.json. Blender always uses four threads, one process at a time. scripts/review1_render.py refreshes clip sheets' input frames; scripts/review1_reduction.py matches the reference lighting; scripts/review1_records.py refreshes this handoff. Earlier scripts are historical checkpoints.
"""
(P/'HANDOFF.md').write_text(handoff)
readme=f"""# MM6 PeasantM4 / natm — review round 1

Cannibal / Head Hunter / Witch Doctor, male. The staged handoff has three tiers, nine local-library clips, 78 bones, detailed spear/buckler attachments, four colour LODs and four opaque body shadow LODs. **50 / 100 Meshy credits spent; zero this round.**

[HANDOFF.md](HANDOFF.md) is the integration record: exact filenames, hashes, triangle counts, gate results, unchanged bindings and remaining scope. [Export manifest](export/manifest.json), [viewer](review/viewer/index.html), [clip sheets](review/sheets/) and [corpse floor review](review/final/corpse_floor_1.png).

Review round 1 resolves the MASK-shadow registry failure and feather-ground penetration. All LODs now reference one four-image set per asset with 16 px dilated island margins and unchanged texel density. **The three GLBs are {percent:.2f}% smaller, but decoded atlas area increased to accommodate the padding.** This tradeoff is measured in the handoff; no decoded-memory saving is claimed.

The direct shared runner passes {main['counts']['PASS']:,} full checks plus {floor['counts']['PASS']:,} floor-probe checks; no failures/unverified rows. Bindings pass with no BAD line. The viewer passes all 27 switches. `integration/actors.yml` is unchanged. User artistic acceptance remains unrecorded. Native installation, builds, regression and game captures belong to the orchestrator. No commit or assets_dev write.

## Recorded decisions

- ../mm6_natm is read-only sprite-restoration source material.
- Preserve the source-frame rig, native warm-brown skin, local-library action choices, native palette ramps, impact timing, calibrated scale and held equipment.
- Fold feather groups through paired deformation helpers under their original bone owners. The fall-only 8 mm root clearance resolves the coarse proxies' remaining floor overlap; other clips keep their original root placement.
- Dead holds two constant frames so the unmodified shared runner can measure acceleration. Float32 endpoints round down by less than one microsecond; no attack/cast timing change.
- Keep the existing measured triangle chain, including the recorded 0.102 LOD3 ratio cap. No new reduction search or paid job.
- The editable work/runtime_lod*.blend files are pre-atlas authoring checkpoints with packed source images; export/textures_shared and the GLBs contain the final atlas layout. Intermediate per-LOD rebakes remain provenance, not runtime texture sets.
- Detailed packing and corpse-floor decisions are in review/round1_feathers.json, export/textures_shared/layout.json and review/gate_intent.md.
"""
(P/'README.md').write_text(readme)
notes=f"""# Runtime audit intent — review round 1

The current reports come from the unmodified claude_shared/gates/run_gates.sh and run_gates.py, called directly through the project workspace guard. The former scripts/runtime_gates.py is historical; its sampling patch is not used.

- Float32 endpoint rounding prevents an artificial sub-microsecond last interval. Dead is a constant two-frame hold. These are explicit export changes recorded in review/round1_timing.json.
- Source hinge frames, twist helpers and the cupped right-palm contact normal are unchanged. Raw upper-arm/wrist limits remain 90 degrees, with G4/G5, elbow-plane, angular acceleration and surface-contact gates mandatory.
- The complete spear grip and whole forearm buckler including straps remain audited.
- ClothFront/Back are exterior panels, so containment=false checks collision.
- The unchanged 1240/12192 LOD3 ratio is 0.1017056; keep the established 0.102 cap.
- The floor probe narrows only animation inventory to Death/Dead. It uses exact final runtime geometry/poses and both foot-region selectors cover the entire solid body, including feathers, with a 4 m sole band. Rest/gait classifications are disabled for this corpse probe. The ordinary report still checks actual soles, rest, walking and running.
- Main runner SHA256: {main['runner_sha256']}. Final body SHA256: {inventory['mm6_natm.glb']['sha256']}.
"""
(P/'review/gate_intent.md').write_text(notes)
f=P/'ANIMATION_STUDY.md';text=f.read_text();text=text.replace('0.020833 s','0.041667 s');text=text.replace('Decorative back feathers still extend below the ground plane during the fall/corpse pose; this is an explicit open visual fault in HANDOFF.md.','Review round 1 folds the feathers above the floor and adds 8 mm of smooth fall-only clearance for coarse body proxies. The shared runtime floor report now passes; see HANDOFF.md.');f.write_text(text)
f=P/'integration/playbook_notes.md';text=f.read_text().replace('The matching shadow LOD needs the same UV/alpha coverage.','Dedicated shadow LODs must remain OPAQUE; use an opaque proxy even when the colour feathers use MASK.').replace('This remains the explicit visual fault in this handoff.','Review round 1 fixes it with feather-owner deformation helpers and validates every solid-body vertex in a shared-runner Death/Dead floor probe.');text+='\nReview round 1: keep helper children under their original bone owner for upper-body layering. Copy deformation using both source and helper inverse rest frames; their edit-mode frames can differ. Repack shared UVs with dilated margins, retain pixel density, and report decoded texel area separately from compressed GLB bytes.\n';f.write_text(text)
progress=json.loads((P/'creature_3d_progress.json').read_text());progress.update(stage='Review round 1 complete: opaque shadows, shared padded atlases and feather-floor correction verified',status='handoff_ready',next_action='Orchestrator reinstalls the three new GLBs, restores the unchanged actors.yml entries, then runs native regression/captures; artistic acceptance and decoded-memory tradeoff remain for review.');progress['handoff']={'file':'HANDOFF.md','review_round':1,'files':inventory,'runtime_gates':main['counts'],'floor_gates':floor['counts'],'viewer_switches':27,'bindings_changed':False,'resolved_faults':['MASK dedicated shadow material','back feathers below the floor during Death/Dead'],'known_limitations':['Decoded atlas area increased to retain texel density with 16 px padding.','Native integration/captures/regression intentionally deferred to orchestrator.','User artistic acceptance not recorded.']};progress['review_round_1']={'credits_spent':0,'root_clearance_m':.008,'solid_body_floor_penetration_mm':floor_worst,'bindings_sha256':sha(P/'integration/actors.yml'),'files_bytes_reduction_pct':percent};(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2))
print('ROUND1_RECORDS',main['counts'],floor['counts'],'near_before_after_ssim',metrics['0']['minimum_ssim_against_accepted_before_round1'],'near_high_ssim',metrics['0']['minimum_ssim_against_unreduced_or_near'],flush=True)

"""Record this fixed-target handoff, including the shared runner's unresolved findings."""
import json,hashlib,sys,subprocess,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review/round4';E=P/'export';V=P/'review/viewer'
sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,accessor_array
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()

def sheet(rows,out,size=None):
 ims=[[Image.open(R/f).convert('RGB') for f,label in row] for row in rows]
 if size:
  for row in ims:
   for im in row:im.thumbnail(size)
 width=max(sum(im.width for im in row) for row in ims);height=sum(max(im.height for im in row)+26 for row in ims);canvas=Image.new('RGB',(width,height),(35,35,35));draw=ImageDraw.Draw(canvas);y=0
 for row,rr in zip(ims,rows):
  x=0
  for im,(_,label) in zip(row,rr):draw.text((x+8,y+7),label,fill='white');canvas.paste(im,(x,y+26));x+=im.width
  y+=max(im.height for im in row)+26
 canvas.save(R/out)
sheet([[(f'axe/{label}_{view}.png',f'{label}: '+('2122' if label=='accepted' else '796')+' triangles') for label in ['accepted','reduced']] for view in ['front','quarter']],'axe_closeup.png')
sheet([[(f'axe/{label}_ingame.png',label+' - same in-game scale') for label in ['accepted','reduced']]],'axe_ingame.png')
sheet([[(f'body/{label}_{i}.png',f'{i*45} degrees - {label}') for i in [k,k+1] for label in ['accepted','reduced']] for k in [0,2,4,6]],'body_eight_views.png',(384,384))
sheet([[(f'lower/{label}_lod1_{view}.png',f'LOD1 at 550px - {label}') for label in ['accepted','reduced']] for view in ['front','quarter']],'body_lod1.png',(550,550))
sheet([[(f'lower/reduced_lod{level}_front.png',f'LOD{level} - shared LOD0 maps') for level in [1,2,3]]],'lower_lods.png')
for view in ['front','left','three_quarter']:
 subprocess.run(['python3',str(P/'scripts/compose_sheet.py'),str(P/f'review/final_{view}'),str(P/f'review/clips_{view}.png')],check=True);shutil.copy2(P/f'review/clips_{view}.png',R/f'clips_{view}.png')
# Keep the current scene export distinct from the older, weighted-prop round-3 intermediates.
shutil.copy2(R/'combined_unbaked.glb',E/'mm6_figc_lod0.glb')
old=json.loads((R/'accepted_gates/gates.json').read_text());new=json.loads((R/'gates/gates.json').read_text());comparison=[]
for level in range(4):
 row={'lod':level}
 for label,data in [('before',old),('after',new)]:
  rows=[x for x in data['gates'] if x['gate'].startswith('grip_') and 'axe' in x['region'] and x['lod'].endswith('/colour'+str(level)) and x['worst'] is not None]
  row[label]={'gap_mm':max(x['worst'] for x in rows if x['gate']=='grip_gap_mm'),'penetration_mm':max(x['worst'] for x in rows if x['gate']=='grip_penetration_mm')}
 comparison.append(row)
(R/'grip_comparison.json').write_text(json.dumps(comparison,indent=2))
axe_gates=[r for r in new['gates'] if r['asset']=='axe' and r['clip']=='Attack'];assert len(axe_gates)==16 and all(r['status']=='PASS' for r in axe_gates)
for asset in new['assets']:assert sha(Path(asset['path']))==asset['sha256']
viewer=json.loads((R/'viewer_check.json').read_text());viewer['manifest_sha256']=sha(V/'manifest.json');(R/'viewer_check.json').write_text(json.dumps(viewer,indent=2));(P/'review/viewer_check.json').write_text(json.dumps(viewer,indent=2))
assert viewer['ready']=='true' and viewer['switched']==24 and not viewer['failed'] and not viewer['consoleErrors']
res=subprocess.run(['python3',str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],check=True,capture_output=True,text=True);assert 'BAD' not in res.stdout;(R/'bindings_check.txt').write_text(res.stdout)
counts={}
for name in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb']:
 d,b=read_glb(E/name);base=d['meshes'][0];chain=[0]+base['extras']['openyamm_lods'];counts[name]=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in chain]
assert counts['mm6_figc.glb']==[6797,3610,1725,694] and counts['mm6_figc_axe.glb']==[796,432,196,78] and counts['mm6_figc_shield.glb']==[1328,634,303,86]
combined=[sum(v[i] for v in counts.values()) for i in range(4)];storage=json.loads((R/'storage.json').read_text());density={}
for label,path,size in [('before',R/'before/mm6_figc_axe.glb',2048),('after',E/'mm6_figc_axe.glb',1024)]:
 d,b=read_glb(path);pr=d['meshes'][0]['primitives'][0];tri=accessor_array(d,b,pr['indices']).reshape(-1,3);v=accessor_array(d,b,pr['attributes']['POSITION'])[tri];uv=accessor_array(d,b,pr['attributes']['TEXCOORD_0'])[tri];area=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1).sum()/2;a=uv[:,1]-uv[:,0];c=uv[:,2]-uv[:,0];pixels=np.abs(a[:,0]*c[:,1]-a[:,1]*c[:,0]).sum()/2*size**2;density[label]={'surface_area_m2':float(area),'surface_texels':float(pixels),'linear_texels_per_m':float(np.sqrt(pixels/area))}
assert density['after']['linear_texels_per_m']>=density['before']['linear_texels_per_m'];(R/'axe_density.json').write_text(json.dumps(density,indent=2))
files={name:{'bytes':(E/name).stat().st_size,'sha256':sha(E/name)} for name in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb','mm6_figc_portable.glb','mm6_figc_authoring.blend','mm6_figc_lod0.glb']}
art=json.loads((E/'artifacts.json').read_text());art.update(revision='review_round_4',files=files,combined_lod_triangles=combined,lod_triangles=counts,technical_completion=False);(E/'artifacts.json').write_text(json.dumps(art,indent=2))
info=json.loads((E/'export_info.json').read_text());info.update(triangles=combined[0],revision='review_round_4');(E/'export_info.json').write_text(json.dumps(info,indent=2))
(E/'lods.json').write_text(json.dumps({'triangles':combined,'parts':counts,'method':'fixed axe targets; body and shield unchanged','original_rig_clips_retained':True,'textures_rebaked_per_lod':False,'shared_texture_set_per_asset':True,'visual_review':'review/round4/','shared_gates_status':new['status'],'historical_limit':'Round3 LOD3 silhouette criterion was below target; no new reduction curve requested.'},indent=2))
changed=[E/name for name in files]+[P/'gates.json',V/'manifest.json']+list((P/'textures/round4_body').glob('*.png'))+list((P/'textures/round4_axe').glob('*.png'))
(R/'changed_files.json').write_text(json.dumps({str(f.relative_to(P)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in changed},indent=2))
progress=json.loads((P/'creature_3d_progress.json').read_text());progress.update(stage='review_round_4_handoff',status='handoff_with_open_faults',technical_completion=False,user_acceptance='round_3_installed; round_4_axe_and_texture_review_pending',next_action={'owner':'orchestrator','action':'Review fixed-target axe and documented shared-gate limits; integrate only the staged body/axe if accepted. Shield and actors.yml unchanged.'})
progress['review_round_4']={'axe_counts':counts['mm6_figc_axe.glb'],'combined_counts':combined,'body_geometry_unchanged':True,'shield_byte_identical':True,'actors_yml_changed':False,'credits_used':0,'shared_gates':{'before':old['counts'],'after':new['counts'],'verdict':new['status'],'report':'review/round4/gates/gates.md'},'grip_comparison':'review/round4/grip_comparison.json','files':'review/round4/changed_files.json','storage':'review/round4/storage.json'}
progress['open_limits']=['Shared runner reports FAIL on both accepted and reduced exports; 13 UNVERIFIED rows remain, including cloth inventory.','Axe LOD0 grip maximum 5.243 mm exceeds 3 mm, improved from accepted 5.307 mm.','Axe LOD3 grip maximum 17.736 mm exceeds accepted 16.248 mm by 1.488 mm.','Historical round3 distant silhouette gate remains open; this scope permits one fixed-target axe pass, no search.','Game integration and real-GPU checks belong to the orchestrator.'];(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2))
model_rows='\n'.join(f'| export/{n} | {v["sha256"]} |' for n,v in files.items())
size_rows='\n'.join(f'| {n} | {v["before"]["images"]} → {v["after"]["images"]} | {v["before"]["bytes"]/1e6:.2f} → {v["after"]["bytes"]/1e6:.2f} |' for n,v in storage.items())
grip_rows='\n'.join(f'| {x["lod"]} | {x["before"]["gap_mm"]:.3f} → {x["after"]["gap_mm"]:.3f} | {x["before"]["penetration_mm"]:.3f} → {x["after"]["penetration_mm"]:.3f} |' for x in comparison)
head=f"""# FighterChain handoff — review round 4

## Review round 4

Fixed-target axe reduction and texture consolidation are staged. Axe LOD0 is **796 triangles, down 62.49% from 2,122**. The body geometry, all weights/normals, skeleton and eight clips are unchanged; the shield is byte-identical to the installed file. **integration/actors.yml did not change** (SHA-256 {sha(P/'integration/actors.yml')}). 30/100 credits used overall; zero this round. No game launch, build, assets_dev installation or commit.

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body, unchanged | 6797 | 3610 | 1725 | 694 |
| Axe before | 2122 | 945 | 356 | 118 |
| Axe after | 796 | 432 | 196 | 78 |
| Shield, unchanged | 1328 | 634 | 303 | 86 |
| Combined after | 8921 | 4676 | 2224 | 858 |

The 24-point bit outlines, beard curves, bevels and socket retain the silhouette. The shaft uses eight sides; the fitted grip uses twelve. Wrap turns, rivets and forged wear are baked from the accepted axe into base colour and tangent normals. Removing the raised langets exposed a connection gap; extending the bit necks closes it without changing the fixed counts. The UV gutters were corrected after a pixel audit. These were implementation repairs to one fixed target, not a reduction search or curve.

[Close-up comparison](review/round4/axe_closeup.png), [same in-game scale](review/round4/axe_ingame.png), [eight body views](review/round4/body_eight_views.png), [LOD1 texture comparison](review/round4/body_lod1.png), [lower levels](review/round4/lower_lods.png). Gameplay-scale axe height corresponds to a 700-pixel actor; these are offline renders, not game captures. Fresh clip sheets contain 168 frames. The viewer passes 24 tier/clip switches and all eight clips advance at 1x and 0.5x.

### Texture memory

| File | Embedded images before → after | GLB MB before → after |
|---|---:|---:|
{size_rows}

All four body LODs reference ONE 2304×2608 set: base colour, ORM/specular mask, tangent normal and region mask. 458 islands are packed by shape without rotation, scaling or resampling. Existing LOD0 texels are copied at 1:1 density with at least 16 pixels of dilation. Black base-colour pixels fall from 51.26% to 28.08%. Lower LODs use their retained original UV-chart lineage to address this shared atlas; tiny charts absent from LOD0 are explicitly mapped to the nearest surviving surface. Body positions, normals and skin weights remain exactly equal per triangle corner across colour and shadow LODs.

The axe uses ONE shared 1024×1024 four-map set for all LODs. Its measured 16-pixel island dilations do not overlap, and the image border is 16.89 pixels. Average surface texel density is {density['after']['linear_texels_per_m']:.1f} texels/m versus {density['before']['linear_texels_per_m']:.1f} before. Maps are in textures/round4_body/ and textures/round4_axe/. Estimated unmipped RGBA8 image storage: body 146.67 → 96.14 MB; axe 67.11 → 16.78 MB. These are pixel estimates, not a hardware VRAM measurement. [Storage](review/round4/storage.json), [atlas](review/round4/body_atlas.json), [padding](review/round4/axe_padding.json), [density](review/round4/axe_density.json), [invariance proof](review/round4/invariance.json).

### Shared gates and open limits

**Shared runner verdict: FAIL**, on both the accepted and revised exports. The accepted baseline has {old['counts']['FAIL']} FAIL rows; the revision has {new['counts']['FAIL']}. Both retain 13 UNVERIFIED rows. The full [current report](review/round4/gates/gates.md) and [accepted baseline](review/round4/accepted_gates/gates.md) include the unchanged body/hand motion findings; thresholds were not relaxed. Cloth containment is unverified, outside this axe/texture-only scope.

All 16 axe strike checks pass (four checks at four LODs): the shared 48-Hz runner selects **0.697917 s** on both exports, versus unchanged impact binding **0.715 s** (17.083 ms error, below 20.833 ms). Edge share is **0.999544** and signed lead **0.833311**. The node Axe and local grip point [0,0,0] remain fixed. Maximum measured axe/body penetration improves from 13.731 to 6.161 mm but remains above the runner's 2-mm limit.

| LOD | Maximum grip gap, mm: before → after | Grip penetration, mm: before → after |
|---|---:|---:|
{grip_rows}

**Grip does not receive a false PASS.** LOD0's middle-finger gap improves but remains over 3 mm; LOD3's gap grows by 1.488 mm. The body/hands remain untouched as requested. The selector includes the whole narrow haft so coarse triangles spanning the grip are actually measured. The fixed-target pass stops here under the cost controls. The older round-3 distant silhouette failure is historical and was not remeasured as a new curve.

check_bindings.py prints no BAD line and weight-sum error is zero for all three runtime files. [Binding result](review/round4/bindings_check.txt), [viewer check](review/round4/viewer_check.json), [playback](review/round4/viewer/playback_review.json).

### Files and hashes

Install candidates are export/mm6_figc.glb and export/mm6_figc_axe.glb. The shield is listed for verification and remains identical. The portable GLB is the tier-A review; the packed authoring blend reflects the current un-ramped scene. review/round4/axe_authoring.blend contains the editable axe and its LODs. [All changed delivery hashes](review/round4/changed_files.json).

| File | SHA-256 |
|---|---|
{model_rows}

Reproduction, under a reclaimed lease: scripts/axe_reduce_r4.py creates the fixed axe/maps; scripts/body_atlas_r4.py and body_source_uv_r4.py/body_uv_r4.py preserve and share the body atlas; scripts/package_r4.py produces runtime and viewer GLBs without round-tripping the body animation; scripts/review_r4.py refreshes the editable snapshot and sheets. Call the shared gate runner with gates.json, then record_round4.py and validate_handoff.py. The earlier round-3 runtime_finish.py/lods.py pipeline is historical and would restore per-LOD textures.

The lease is released at handoff. The orchestrator owns integration, game checks and review of the recorded limits.

## Historical handoffs

The sections below are retained as history; their counts, hashes, completion claims and reproduction commands are superseded by review round 4.

"""
(P/'HANDOFF.md').write_text(head+(R/'before/HANDOFF.md').read_text())
readme=f"""# Current delivery: review round 4

Axe: **796 / 432 / 196 / 78 triangles**, down from 2122 / 945 / 356 / 118. Body and shield geometry, clips, tiers and bindings are unchanged. The shield GLB is byte-identical to assets_dev. Body and axe each use one shared four-map set across all LODs; body images 16 → 4, axe maps 2K → 1K. Runtime sizes: body 18.67 → 11.71 MB; axe 9.88 → {storage['mm6_figc_axe.glb']['after']['bytes']/1e6:.2f} MB.

See [HANDOFF.md](HANDOFF.md) for counts, hashes, reproduction, comparisons and the shared runner's FAIL verdict. The accepted baseline also fails; blade/timing checks pass, while grip/body limits remain. LOD3 grip gap increases by 1.488 mm. This was one fixed triangle target with connection/padding repairs, no triangle search; 0 Meshy credits used (30/100 total). No game, build, install or commit.

The authoritative current runtime builder is scripts/package_r4.py. The round-3 per-LOD texture builders below are historical. Current textures are under textures/round4_body and textures/round4_axe; accepted source files are retained in review/round4/before. [Close-up](review/round4/axe_closeup.png), [in-game scale](review/round4/axe_ingame.png), [viewer](review/viewer/index.html).

## Earlier project record (superseded)

"""
previous=(P/'README.md').read_text()
if previous.startswith('# Current delivery: review round 4'):previous=previous.split('## Earlier project record (superseded)\n\n',1)[1]
(P/'README.md').write_text(readme+previous)
print('ROUND4_RECORDS_WRITTEN',combined,new['status'],files,flush=True)

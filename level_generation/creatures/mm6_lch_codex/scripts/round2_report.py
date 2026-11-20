import os,sys,json,hashlib,csv,datetime
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';sys.dont_write_bytecode=True
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(R/'packaged_metrics.json');v=read(P/'export/validation.json');proof=read(R/'preservation.json');sel=read(R/'selected.json')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for level in range(4):
 res=[896,704,320,160][level];width=[448,360,176,112][level];sheet=Image.new('RGB',(width*8,(res+30)*2),(100,100,100));draw=ImageDraw.Draw(sheet)
 for row,label in enumerate(['baseline','final']):
  for k in range(8):
   im=Image.open(R/f'textured/{label}/tier0/lod{level}/{k}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(100,100,100,255));bg.alpha_composite(im)
   sheet.paste(bg.convert('RGB').crop(((res-width)//2,0,(res+width)//2,res)),(width*k,(res+30)*row+30));draw.text((width*k+4,(res+30)*row+5),f'{label} {k*45} deg',font=font,fill='white')
 sheet.save(R/f'eight_views_lod{level}.png')
sheet=Image.new('RGB',(448*6,926),(100,100,100));draw=ImageDraw.Draw(sheet)
for tier in range(3):
 for col,label in enumerate(['baseline','final']):
  im=Image.open(R/f'textured/{label}/tier{tier}/lod0/0.png').convert('RGBA');bg=Image.new('RGBA',im.size,(100,100,100,255));bg.alpha_composite(im);x=(tier*2+col)*448
  sheet.paste(bg.convert('RGB').crop((224,0,672,896)),(x,30));draw.text((x+8,5),f'Tier {tier+1} / {label}',font=font,fill='white')
sheet.save(R/'tier_comparison_700px.png')
def grid(files,path,n):
 ims=[Image.open(f).convert('RGB')for f in files];w=max(i.width for i in ims);h=max(i.height for i in ims);out=Image.new('RGB',(w*n,(h+25)*((len(ims)+n-1)//n)),(190,190,190));d=ImageDraw.Draw(out)
 for k,(f,im)in enumerate(zip(files,ims)):
  x=k%n*w;y=k//n*(h+25);out.paste(im,(x,y+25));d.text((x+5,y+3),f.stem,fill='black')
 out.save(path)
grid([P/f'review/tiers/lch_{t}_{view}.png'for t in 'abc'for view in ['front','left','three_quarter']],P/'review/tiers.png',3)
grid([P/f'review/closeups/head_{view}.png'for view in ['front','left','back','three_quarter']],P/'review/head.png',4)
grid(sorted((P/'review/closeups').glob('hands_*.png')),P/'review/hands.png',8)
rows=[]
for file in ['curve.json','direct_far.json','direct_far_weighted.json','piece_far.json','head_surface_far.json','ceiling_far.json','union_far.json']:
 for x in read(R/file):
  q=x['metrics'];rows.append([file,x['level'],x.get('step',''),x.get('factor',x.get('power','')),x['triangles'],q['pooled_iou'],q['min_iou'],'not measured',q['pass'],'silhouette trial; final gates separately'])
for x in m:rows.append(['packaged final',x['level'],'final','',x['triangles'],x['pooled_iou'],x['min_iou'],x['min_ssim'],x['silhouette_pass']and x['ssim_ge_095'],'absolute elbow/contact failures'])
with (R/'reduction_curve.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['profile','LOD','step','factor','triangles','pooled_IoU','minimum_IoU','minimum_SSIM','visual_pass','rig_notes']);w.writerows(rows)
for level in [1,2,3]:
 f=R/f'bake_lod{level}.json';d=read(f);d['target']=sel['levels'][level]['blend'];d['method']='Cycles selected-to-active; corresponding rigid bone groups translated apart; accepted texels projected to target UVs, then packed into shared LOD rectangles';f.write_text(json.dumps(d,indent=2)+'\n')
f=P/'scripts/round2_bake_lod.py';f.write_text(f.read_text().replace("'target':'work/round2/lod0_selected.blend'","'target':entry['blend']"))
files=['export/mm6_lch.glb','export/mm6_lch_runtime_lod0.glb','export/mm6_lch_lods.glb','export/mm6_lch_lods_shadowfix.glb','review/viewer/manifest.json','review/viewer/mm6_lch_a.glb','review/viewer/mm6_lch_b.glb','review/viewer/mm6_lch_c.glb','integration/actors.yml']+[e['blend']for e in sel['levels']]
files += [str(f.relative_to(P))for f in sorted((P/'textures/round2').glob('*.png'))if 'coverage'not in f.name]
hashes={f:sha(P/f)for f in files};(R/'artifact_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
counts=v['triangles'];before=[16274,8135,2907,897];round1=[7824,7787,6916,6710]
table='| LOD | Accepted before | Round 1 | Round 2 | % LOD0 | Actor px | Pooled IoU | Min IoU | Min SSIM, all tiers |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
for i,q in enumerate(m):table+=f'| {i} | {before[i]:,} | {round1[i]:,} | {counts[i]:,} | {counts[i]/counts[0]*100:.1f}% | {q["actor_height_px"]} | {q["pooled_iou"]:.6f} | {q["min_iou"]:.6f} | {q["min_ssim"]:.6f} |\n'
rigtable='| Clip | Max G4 | Max G5 | Max head mm | Cloth mm LOD0 / 1 / 2 / 3 | Other failure |\n|---|---:|---:|---:|---|---|\n'
for clip in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 gs=[read(R/f'lod_{i}_rig.json')[clip]for i in range(4)];cs=[read(R/f'lod_{i}_contacts.json')[clip]for i in range(4)];cloth=' / '.join(f'{x.get("legs_cloth",[0])[0]*10:.3f}'for x in cs)
 other='LOD2 right hand 48.131 mm'if clip=='Attack'else 'none'
 rigtable+=f'| {clip} | {max(x["g4_arm_edge_max"]for x in gs):.6f} | {max(x["g5_hand_edge_max"]for x in gs):.6f} | {max(x.get("head",[0])[0]for x in cs)*10:.3f} | {cloth} | {other} |\n'
method='''The reference at every switch size is the unreduced accepted 16,274-triangle LOD0. Eight yaw views at 45-degree intervals; orthographic actor heights 700 / 550 / 220 / 88 px. Final comparisons import the packaged GLBs, use the exact engine linear-luminance tier ramps, and render base color, ORM and tangent normals under identical Cycles lighting (24 samples, fixed seed, no denoising). SSIM uses the joint object crop plus eight pixels. No cheaper reference or subjective override turns a failing measurement into a pass.

The close-up search collapses in approximately 10% steps with weighted face, fingers, joint ends and eight-view outlines, retaining original leg/tatter contact pieces. LOD0 stops at 6,290; the next 5,660 step has minimum IoU 0.987633 and is rejected. All bone weights and clips remain unchanged. There is no held weapon, staff or shield. The attached crown is included in body reduction, silhouette checks, rebakes and the head review.

Base color, region mask, ORM (R specular class, G roughness, B zero) and tangent +Y normals were projected from the accepted source onto every selected LOD. Corresponding parts are exploded for LOD0; corresponding rigid bone groups for LOD1-3. A white ray-hit bake supplies padding coverage. Each LOD occupies a padded rectangle in the same shared 1024x1024 body and 1024x1024 head sets; full 1K individual bakes remain in textures/round2/lod0..3/. Runtime has four 2080x1024 atlases and the unchanged three variant materials. Effective texels per set are 752x1008 / 224x480 / 224x224 / 224x224; this allocation limits distant texture fidelity and is not claimed lossless. UVs retain their parameterization for baking, then receive an affine atlas mapping.

Weighted/direct collapse, piece allocation, surface/bounds fitting and voxel-union trials did not produce acceptable cheap far silhouettes. LOD2/3 therefore retain the previous accepted geometry at 2,907 / 897; positions, normals, weights and index bytes are verified unchanged. Their new 25% / 10% ratios and pooled IoU >=0.97 are NOT achieved. LOD1 passes pooled silhouette, but its textured SSIM is only about 0.883. No distant LOD was made denser. A rest-normal-transfer trial did not improve LOD1 and was reverted.
'''
gates='''G4/G5 and whole-mesh edge preservation pass on every clip at 48 Hz; the final exported source-relative rotation trace has no flags. Rig nodes, 54 joints including both sockets, inverse binds and every animation sample byte are identical to the accepted export. Palm directions, elbow planes and forearm roll remain unchanged; maximum forearm roll is 12.402 degrees.

Absolute rig criteria still fail. Accepted Attack hyperextension is 14.657 degrees left / 9.643 right against a 5-degree limit. LOD0 cloth crossings match the accepted baseline exactly, up to 17.615 mm against 2 mm. The old cheap far geometry also fails contacts: LOD2 Attack right hand 48.131 mm and LOD3 Walking cloth 32.612 mm. These failures are not waived. The contact test samples nearest faces and edge crossings on open tatters at 48 Hz, not continuous collision. Whole-mesh lowest points across clips are -0.517 / -6.936 / -1.345 / -5.944 mm for LOD0-3. Frozen accepted clips were not silently reposed to repair the inherited elbow failure.
'''
evidence='[700px tier pairs](review/triangle_rebake/tier_comparison_700px.png), [LOD0 eight views](review/triangle_rebake/eight_views_lod0.png), [550px](review/triangle_rebake/eight_views_lod1.png), [220px](review/triangle_rebake/eight_views_lod2.png), [88px](review/triangle_rebake/eight_views_lod3.png).\n[Curve CSV](review/triangle_rebake/reduction_curve.csv), [per-view metrics](review/triangle_rebake/packaged_metrics.json), [preservation](review/triangle_rebake/preservation.json).'
hash_table='| File | SHA-256 |\n|---|---|\n'+''.join(f'| [{f}]({f}) | `{h}` |\n'for f,h in hashes.items())
checks='''- [Bindings](review/check_bindings.log): return 0, no BAD line, worst weight-sum error 0.
- [Viewer](review/check_viewer.log): 24 tier/clip switches pass, no console errors; four browser captures; checker-owned Chrome processes closed.
- [Structural validation](export/validation.json), [48Hz gates](review/triangle_rebake/gate_summary.json), [rotation trace](work/trace_export.json), [trace hash](work/trace_source.json).
- Updated [front](review/clips_front.png), [side](review/clips_left.png), [three-quarter](review/clips_three_quarter.png), [tiers](review/tiers.png), [head/crown](review/head.png), [hands](review/hands.png).
- Further far-LOD geometry/material refinement is required. Absolute elbow/cloth gates also remain unmet for the frozen accepted clips. Do not treat this candidate as satisfying the full batch done criteria.
- No native game checks or builds: the batch rules reserve regression and indoor/outdoor captures for the orchestrator.
'''
text=f'''# MM6 BLich / lch — review round 2

**PARTIAL — not ready for integration.** LOD0 passes close-up visual thresholds; the complete round-2 done criteria are not met. This staged package is for review and is not installed.
Budget: **30/100 credits consumed; 0 new; 70 remaining**. No commits, builds, game launches, shared-file edits or writes to assets_dev.

## Triangle reduction (rebake)

{table}

The chain is **6,290 / 3,466 / 2,907 / 897**. LOD0 is **61.3% smaller** than the accepted master and 19.6% smaller than round 1. Its minimum 700px IoU is **{m[0]['min_iou']:.6f}** and minimum SSIM across all three tiers **{m[0]['min_ssim']:.6f}**. LOD1 passes silhouette but fails textured comparison. LOD2/3 fail the new silhouette and ratio targets. No far LOD exceeds its previous count.

{evidence}

{method}

{gates}
{rigtable}

## Review round 2

Changed project files: runtime/intermediate GLBs below; selected LOD geometry; base-color, mask, ORM and normal rebakes in textures/round2/; atlas UV layout; tier viewer GLBs and manifest; comparison/clip/head/hand sheets; project-local scripts, validation, progress, README and this handoff. The runtime is **{v['bytes']:,} bytes**, 54 joints, eight unchanged clips, three unchanged tier definitions, four color LODs and four shadow LODs.

**integration/actors.yml did not change. No integration file or assets_dev file was changed.** Sockets, scales, impacts, clip bindings and accepted props are unchanged. Exact animation/bind/material preservation and atlas bounds are asserted in preservation.json.

{hash_table}

[All hashes JSON](review/triangle_rebake/artifact_hashes.json). Previous round-1 runtime: `d2b1010b8f16f37b7a31cf8d0f9b39b90c869d9452d79bbed62128bf4d1c6d75`. Accepted source runtime: `4bdedce0ec3f051cbc01e9d27ebad9c2dd4bbc4bf440846a48da622ef8dbcee9`.

## Checks and remaining work

{checks}

## Integration contract

Keep integration/actors.yml: BLich A/B/C IDs 568/569/570, tiers lch_a/b/c, scale 111.6, yaw -pi/2, stride 1.284 m, Running aliases Walking. Attack release 0.729 s from right palm; Cast 0.625 s from left palm; Hit 0.733 s. The [local viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_lch_codex/review/viewer/) shows the staged close-up; it is not evidence that far LODs pass.

## Review round 1

[Archived handoff](review/triangle_rebake/round1_archive/HANDOFF.md) and [round-1 measurements](review/triangle_reduction/README.md) are historical. Its 7,824 / 7,787 / 6,916 / 6,710 chain is superseded and must not be integrated.
'''
(P/'HANDOFF.md').write_text(text)
(R/'README.md').write_text('# Round-2 triangle minimisation: partial result\n\n'+table+'\n'+evidence.replace('review/triangle_rebake/','')+'\n\n'+method+'\n'+gates+'\n'+rigtable+'''\n## Sources and reproduction

Source: ../triangle_reduction/baseline/work/rig_textured.blend and its accepted runtime; original maps and tier ramps in the project textures/. Raw trials, selection and per-view metrics are JSONs here. Workbench silhouettes live under silhouette/, final material pairs under textured/. visible_far.json and hull_far.json are discarded implementation diagnostics, not acceptance evidence.

Project scripts round2_geometry.py and round2_far_*.py hold trials. round2_bake.py, round2_coverage.py and round2_bake_far.py bake maps; round2_pad.py and round2_texture_layout.py pad and pack them. round2_gates_export.py supplies raw geometry; retain unpacked exports before texture-layout mapping. round2_pack.py, round2_pack_runtime.py and round2_preserve_far.py assemble the accepted rig with revised meshes/maps. round2_render_inputs.py, round2_render.py, round2_verify.py and round2_report.py produce evidence. Every mutation uses the workspace lease; Blender uses the shared wrapper with four threads.

The read-only installed snapshot taken at round start had hash 0676041c2a4306a0edeb518f3e4427d2c4374483fa979c7c6c5f8758e6b8dfa1 and counts 17,162 / 8,777 / 3,259 / 897, differing from the explicit user reference. The user's lower caps and accepted authoring archive were used. Nothing was copied to assets_dev.
''')
(P/'README.md').write_text(f'''# MM6 BLich (lch) — Codex project

**Review round 2 is partial, not ready for integration.** LOD0 passes the 700px visual gate after accepted-surface rebaking. Far quality and absolute rig criteria remain unmet; read [HANDOFF.md](HANDOFF.md) before using the staged export.

{table}

Native identity is a crowned skeletal caster with breastplate, bracers, boots and ochre tatters; no added robe, staff or shield. The source restoration project ../mm6_lch/ is read-only. Accepted clips, tiers, sockets and bindings are unchanged. Installation is orchestrator-owned. Budget remains 30/100 credits, no new jobs.

[Method, curves and renders](review/triangle_rebake/README.md), [artifact hashes](review/triangle_rebake/artifact_hashes.json), [bindings](integration/actors.yml), [regression proposal](integration/regression.md), [viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_lch_codex/review/viewer/).

Unattended decisions: honor the user's lower historical count caps despite the differing installed snapshot; preserve accepted cheap LOD2/3 geometry after cheaper trials failed; rebake each selected LOD and fit maps into the existing shared body/head set dimensions; preserve frozen clips and explicitly report failures. No failed threshold is treated as a pass. Round-1 records are archived in review/triangle_rebake/round1_archive/.
''')
(P/'review/GATES.md').write_text('# Round-2 gates — incomplete quality pass\n\n'+gates+'\n'+rigtable+'\n[Preservation](triangle_rebake/preservation.json), [anatomy](triangle_rebake/anatomy.json), [visual metrics](triangle_rebake/packaged_metrics.json).\n')
d=read(P/'creature_3d_progress.json');d.update(stage='review_round_2',substep='staged partial result; far quality unresolved',status='needs_further_work',updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
a=d['selected_artifacts'];a['rig']={'path':sel['levels'][0]['blend'],'sha256':sha(P/sel['levels'][0]['blend'])};a['uv_animation_master']=a['rig'].copy();a['runtime']={'path':'export/mm6_lch.glb','sha256':v['sha256']};a['viewer_manifest']={'path':'review/viewer/manifest.json','sha256':sha(P/'review/viewer/manifest.json')};a['lod_masters']=[{'path':e['blend'],'sha256':sha(P/e['blend'])}for e in sel['levels']]
d['review_round_2'].update(before_triangles=before,round1_triangles=round1,after_triangles=counts,report='review/triangle_rebake/README.md',actors_changed=False,integration_changed=False,installed=False,new_credits=0,runtime_sha256=v['sha256'],all_done_criteria_pass=False,quality=[{k:v for k,v in q.items()if k not in ['tiers','versus_same_accepted_far_geometry']}for q in m])
d['open_findings']=[{'type':'far_visual_failure','finding':'LOD1 SSIM; LOD2/3 high-detail silhouette, SSIM and requested ratios not met.'},{'type':'inherited_rig_failure','finding':'Frozen Attack elbow and cloth contacts; old cheap LOD2/3 contact failures remain.'}]
d['next_action']={'owner':'orchestrator','action':'Further far-LOD geometry/material work required; do not integrate as a completed quality pass.'};d['handoff']={'path':'HANDOFF.md','status':'partial_not_ready_for_integration','static_checks':'bindings, viewer, trace, rig/material/actor preservation pass; absolute quality gates fail','lease':'release after final receipt review'}
(P/'creature_3d_progress.json').write_text(json.dumps(d,indent=2)+'\n');(P/'export/selected_artifacts.json').write_text(json.dumps(a,indent=2)+'\n')
print('ROUND2_HANDOFF_WRITTEN',v['sha256'],'partial, not ready for integration')

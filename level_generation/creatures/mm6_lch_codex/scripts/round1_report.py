"""Review receipts and handoff for topology-only round 1; report inherited failures explicitly."""
import json,hashlib,csv,datetime
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(R/'selected.json');m=read(R/'packaged_metrics.json');v=read(P/'export/validation.json');proof=read(R/'preservation.json')
h=sha(P/'export/mm6_lch.glb');before=s['before'];counts=v['triangles']
assert counts==[x['triangles']for x in s['levels']]
rows=[]
for profile in ['pooled','adaptive_fine_lod1','adaptive_lod2','adaptive_pooled_lod3']:
    d=read(R/profile/'curve.json')
    for q in d['curve']:
        levels=q.get('levels',{str(d.get('level',0)):q.get('metrics',{})})
        for level,metric in levels.items():
            views=metric.get('views',[])
            pooled=metric.get('pooled_iou','')
            if pooled=='' and views and all('intersection'in x for x in views):pooled=sum(x['intersection']for x in views)/sum(x['union']for x in views)
            rows.append([profile,level,q['step'],q.get('trial',0),q['triangles'],pooled,metric['min_iou'],metric['min_ssim'],metric['pass'],'rigid single-bone weights; final contact gates separately'])
for filename in ['next_step.json','chain_fit.json','chain_fine.json']:
    for q in read(R/filename)['levels']:
        mm=q['metrics'];rows.append([filename,q['level'],'post-contact',0,q['triangles'],mm['pooled_iou'],mm['min_iou'],mm['min_ssim'],mm['pass'],'final contact regions protected'])
for level in range(4):
    mm=m[level];rows.append(['selected shipping GLB',level,'final',0,counts[level],mm['pooled_iou'],mm['min_iou'],mm['min_ssim'],mm['pass'],'G4/G5/G6 legacy pass; inherited elbow and cloth fail'])
with (R/'reduction_curve.csv').open('w')as f:
    writer=csv.writer(f);writer.writerow(['profile','LOD','step','trial','triangles','pooled_IoU','minimum_view_IoU','minimum_view_SSIM','visual_pass_pooled','gates']);writer.writerows(rows)
table='| LOD | Before | After | Change | Pooled IoU | Min view IoU | Min view SSIM |\n|---|---:|---:|---:|---:|---:|---:|\n'
for level in range(4):
    mm=m[level];table+=f"| {level} | {before[level]:,} | {counts[level]:,} | {(counts[level]/before[level]-1)*100:+.1f}% | {mm['pooled_iou']:.6f} | {mm['min_iou']:.6f} | {mm['min_ssim']:.6f} |\n"
anatomy=read(R/'anatomy.json')['clips'];baseline=read(R/'lod_baseline_contacts.json')
rigtable='| Clip | G4 max, all LODs | G5 max, all LODs | Head max mm | Cloth mm (baseline = final) | Elbow hyperextension L/R ° |\n|---|---:|---:|---:|---:|---:|\n'
for clip in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
    g=[read(R/f'lod_{i}_rig.json')[clip]for i in range(4)];c=[read(R/f'lod_{i}_contacts.json')[clip]for i in range(4)]
    rigtable+=f"| {clip} | {max(x['g4_arm_edge_max']for x in g):.6f} | {max(x['g5_hand_edge_max']for x in g):.6f} | {max(x.get('head',[0])[0]for x in c)*10:.3f} | {baseline[clip].get('legs_cloth',[0])[0]*10:.3f} | {anatomy[clip]['L']['max_hyperextension_deg']:.3f} / {anatomy[clip]['R']['max_hyperextension_deg']:.3f} |\n"
metric_note="""Metrics use paired imports of the actual accepted and final runtime GLBs, with the accepted **LOD0** as the reference at every distance. Eight yaw views at 45° intervals; 960×960; perspective 35°; camera target (0, 0.15, 0.9) m. Distances are 4.4 / 6.9995 / 16.0178 / 38.5636 m, corresponding to viewer distance and nominal 500 / 200 / 80 pixel engine switches. Workbench textured studio with 32-sample alpha; SSIM uses the object bounding crop plus 8 px, neutral background, 7×7 windows. No large blank canvas is averaged into SSIM.

**Aggregation decision:** silhouette IoU is pooled intersection/union over the eight views, threshold 0.995. SSIM must be >=0.98 in every view. All per-view values are retained. LOD0–2 also pass minimum-per-view IoU >=0.995. **LOD3 does not:** minimum 0.992308 (five differing pixels out of 650 in its worst view). Pooled LOD3 IoU passes. This is an explicit interpretation of “IoU from 8 views,” not a claim that each LOD3 view passes. If the criterion means every individual silhouette, this candidate does not fully satisfy it.

Contact-sensitive cloth and leg pieces were restored exactly from the accepted authoring master. UV loops and rigid bone weights are retained; face/hands/fingers, joint caps, open boundaries, UV seams and eight-view silhouettes are protected or weighted during planar dissolve and QEM collapse. Rest normals are transferred from the original surface. No held weapon or shield exists; the attached crown is included in body reduction and visual checks.

**Stopping evidence:** from the final contact-preserved candidates, another ~10% yields LOD0 7,036 (IoU 0.994543, SSIM 0.977963), LOD1 7,005 (SSIM 0.978523), LOD3 6,030 (IoU 0.992505): rejected. LOD2 6,552 has pooled visual pass but falls below LOD3's count and minimum view IoU is 0.994409. A 6,770-triangle fit still has minimum IoU 0.994935; the 6,916-triangle fit passes each view. The pipeline requires strictly decreasing LOD counts. Raw curves retain each trial, including unsuccessful adaptive protection.

The distant levels are denser than the old fixed-ratio exports because those ratios were replaced with fits against full-detail LOD0. This reduces close-range work by 51.9%, but increases LOD2/3 draw cost and total stored geometry. No native runtime performance claim is made.
"""
gate_note="""**Absolute new batch criteria do not all pass.** The accepted baseline already has Attack elbow hyperextension (left 14.657°, right 9.643°; limit 5°) and leg/loincloth crossings above the 2 mm cloth limit. The user froze the accepted clips and visible shape. They were preserved, and all cloth measurements match the accepted baseline exactly on all four LODs; these are inherited failures, not waived passes.

G4/G5 and whole-mesh edge ratios pass on every clip at 48 Hz (whole-mesh maximum 1.000236, floating-point noise on rigid pieces). Source-relative exported G6 rotation trace has zero flags. Arm/hand-versus-body and hand-versus-cloth intersections are 0 mm; head remains within its 10 mm gate. Palm trajectories, elbow planes and forearm roll are unchanged; maximum forearm roll is 12.402°. At rest the palms face toward the thigh (Standing angles approximately 44–49°). No grip/blade gate applies. Original feet and leg surfaces are retained; whole-mesh minimum after collapse can reach -0.566 mm in the corpse/transition geometry, while ordinary floor-standing clips retain their accepted support.

The cloth test checks actual leg/hand edge crossings of posed cloth triangles and reports signed-normal endpoint depth; a naive inside test is invalid for open tatters. It is sampled at 48 Hz and is not a continuous collision proof. Detailed numeric sources: lod_*_rig.json, lod_*_contacts.json, anatomy.json, gate_summary.json. Elbow/palm trajectories are identical by rig/action signature; the final GLB animation sampler bytes and bind matrices are also identical to the accepted GLB.
"""
report='# Triangle reduction — review round 1\n\n'+table+'\n'+metric_note+'\n'+gate_note+'\n'+rigtable+f'\nRuntime SHA-256: `{h}`.\n\n[Curve CSV](reduction_curve.csv), [packaged metrics](packaged_metrics.json), [preservation assertions](preservation.json), [selected masters](selected.json), [eight-view comparison](eight_views.png).\n'
(R/'README.md').write_text(report)
(P/'review/GATES.md').write_text('# Review round 1 gates\n\n'+gate_note+'\n'+rigtable+f'\nFinal runtime SHA-256: `{h}`.\n\nSee [triangle report](triangle_reduction/README.md) and [validation](../export/validation.json).\n')
# The final sheets are rebuilt from the new runtime viewer models.
import subprocess,sys
for view in ['front','left','three_quarter']:
    subprocess.run([sys.executable,str(P/'scripts/compose_sheet.py'),str(P/f'review/clips_{view}'),str(P/f'review/clips_{view}.png')],check=True)
def grid(files,out,cols):
    images=[Image.open(f).convert('RGB')for f in files];w,h=images[0].size;canvas=Image.new('RGB',(cols*w,((len(images)+cols-1)//cols)*(h+24)),(210,210,210));draw=ImageDraw.Draw(canvas)
    for i,(f,im)in enumerate(zip(files,images)):
        x=i%cols*w;y=i//cols*(h+24);canvas.paste(im,(x,y+24));draw.text((x+5,y+5),f.stem,fill='black')
    canvas.save(out)
grid([P/f'review/tiers/lch_{tier}_{view}.png'for tier in 'abc'for view in ['front','left','three_quarter']],P/'review/tiers.png',3)
grid([P/f'review/closeups/head_{view}.png'for view in ['front','left','back','three_quarter']],P/'review/head.png',4)
grid(sorted((P/'review/closeups').glob('hands_*.png')),P/'review/hands.png',8)
canvas=Image.new('RGB',(8*260,2*360),(128,128,128));draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['baseline','final']):
    for k in range(8):
        im=Image.open(R/f'packaged/{label}/lod0/{k}.png').convert('RGBA');im.thumbnail((320,320));bg=Image.new('RGBA',im.size,(128,128,128,255));bg.alpha_composite(im)
        # Center crop around the figure retains the exact common camera scale.
        canvas.paste(bg.convert('RGB').crop((30,0,290,320)),(k*260,row*360+30))
        draw.text((k*260+6,row*360+8),f'{label} {k*45} deg',fill='white')
canvas.save(R/'eight_views.png')
files=['export/mm6_lch.glb','export/mm6_lch_runtime_lod0.glb','export/mm6_lch_lods.glb','export/mm6_lch_lods_shadowfix.glb',
       'review/viewer/mm6_lch_a.glb','review/viewer/mm6_lch_b.glb','review/viewer/mm6_lch_c.glb','review/viewer/manifest.json','integration/actors.yml']
files += [r['blend']for r in s['levels']]
hashes={f:sha(P/f)for f in files};(R/'artifact_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
hash_table='| File | SHA-256 |\n|---|---|\n'+''.join(f'| [{f}]({f}) | `{x}` |\n'for f,x in hashes.items())
handoff=f"""# MM6 BLich / lch — review round 1 handoff

**Topology revision staged; accepted appearance and animation data preserved. New absolute elbow/cloth criteria have inherited failures; LOD3 passes pooled, not every-view, silhouette IoU.**
Round 0 was accepted by the user and installed by the orchestrator. This revision is **not installed**.
No shared files, builds, game launches or commits. Project `mm6_lch_codex`, identity `mm6:lch`.
Budget unchanged: **30/100 credits consumed; 0 new; 70 remaining**.

## Triangle reduction

{table}
Close-range LOD0 is **51.9% smaller**. LOD1 is smaller; LOD2/3 are denser than the previous fixed-ratio exports.
See [full reduction curve and methodology](review/triangle_reduction/README.md),
[CSV](review/triangle_reduction/reduction_curve.csv), [eight views](review/triangle_reduction/eight_views.png),
[per-view packaged measurements](review/triangle_reduction/packaged_metrics.json).

{metric_note}
{gate_note}
{rigtable}

## Review round 1

Changed only project geometry exports, selected authoring meshes, validation/review scripts and evidence.
The runtime file is **{v['bytes']:,} bytes**, **54 joints**, **8 clips**, **three tiers**, four color and four shadow LODs.
LOD geometry and its corresponding shadow meshes changed. The rebuild copies the accepted rig, sockets, bind matrices,
all animation sampler bytes, material definitions, variant ramps and decoded atlas pixels exactly; preservation assertions passed.

**`integration/actors.yml` did not change** (SHA-256 below). No files were copied to `assets_dev`.
Props: no separate weapon, staff or shield exists. Crown geometry is part of the main mesh and was checked with it.

{hash_table}
[Artifact hashes JSON](review/triangle_reduction/artifact_hashes.json). Baseline hash:
`4bdedce0ec3f051cbc01e9d27ebad9c2dd4bbc4bf440846a48da622ef8dbcee9`.
The immutable [baseline archive](review/triangle_reduction/baseline/hashes.json) includes its original handoff and masters.

## Validation and review

- [Binding check](review/check_bindings.log): no BAD line; all referenced clips, sockets and material/weight rules checked.
- [Viewer check](review/check_viewer.log): 24 tier × clip switches, zero console errors.
- [Structural validation](export/validation.json), [preservation proof](review/triangle_reduction/preservation.json),
  [gate report](review/GATES.md), [exported trace](work/trace_export.json), [trace hash](work/trace_source.json).
- Refreshed [front](review/clips_front.png), [side](review/clips_left.png), [three-quarter](review/clips_three_quarter.png),
  [tiers](review/tiers.png), [head](review/head.png), [hands](review/hands.png); browser body/head captures in `review/browser_*.png`.
- [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_lch_codex/review/viewer/).
  Review GLBs bake tier colors for three.js; install only `export/mm6_lch.glb`.

## Integration contract and remaining limits

Use [integration/actors.yml](integration/actors.yml) unchanged: BLich A/B/C, IDs **568/569/570**, tiers `lch_a/b/c`,
scale **111.6**, yaw **−π/2**, stride **1.284 m**, Running aliases Walking. Attack releases from right palm at
**0.729 s**; Cast from left palm at **0.625 s**. Hit remains **0.733 s**.
[Regression proposal](integration/regression.md) and [production notes](integration/playbook_notes.md) remain available.

The orchestrator owns installation and native indoor/outdoor regression/captures. The denser far LODs need performance
review. The frozen accepted Attack hyperextension and cloth intersections prevent an unconditional “all new gates pass”
claim; resolving them would change the accepted motion or visible geometry. LOD3's per-view IoU limit is separately
documented above. No approval or input was awaited in this unattended round.

The crown remains attached in Death and minor tier accents remain simplified, as in the accepted model.
No additional artistic changes were made. Claim a new project lease before resuming; use one background Blender at four threads.
"""
(P/'HANDOFF.md').write_text(handoff)
art=read(P/'export/selected_artifacts.json')
for key,path in [('rig',s['levels'][0]['blend']),('uv_animation_master',s['levels'][0]['blend']),('runtime','export/mm6_lch.glb'),('viewer_manifest','review/viewer/manifest.json')]:
    art[key]={'path':path,'sha256':sha(P/path)}
art['lod_masters']=[{'path':r['blend'],'sha256':sha(P/r['blend'])}for r in s['levels']]
(P/'export/selected_artifacts.json').write_text(json.dumps(art,indent=2)+'\n')
progress=read(P/'creature_3d_progress.json')
progress.update(status='review_handoff_with_inherited_gate_failures',stage='review_round_1_handoff',substep='Topology revision exported and reviewed',updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),selected_artifacts=art)
progress['gates']={'status':'legacy_pass_new_absolute_failures_inherited','report':'review/GATES.md','runtime_sha256':h,'g4_g5':'all 8 clips / all 4 levels at 48 Hz pass','g6':'zero exported rotation flags; arm/hand 0 mm; head <=10 mm','exceptions':['Attack hyperextension L14.657/R9.643 degrees already present','cloth intersections 2.445–17.615 mm already present, identical on all levels']}
progress['review_round_1'].update(before_triangles=before,after_triangles=counts,report='review/triangle_reduction/README.md',actors_changed=False,installed=False,runtime_sha256=h,visual_metric_policy=s['metric_policy'],lod3_minimum_view_iou=m[3]['min_iou'])
progress['next_action']={'owner':'orchestrator','action':'Review inherited gate failures and pooled LOD3 IoU interpretation; integrate topology revision and run reserved native checks if accepted.'}
progress['handoff']={'path':'HANDOFF.md','status':'ready_with_explicit_limits','static_checks':'bindings, viewer, exact accepted data preservation, packaged visuals and legacy rig gates'}
progress['integration'].update(installed=False,status='round0_installed_by_orchestrator_round1_staged')
progress['open_findings']=[{'type':'inherited_gate_failure','finding':x}for x in progress['gates']['exceptions']]+[{'type':'metric_interpretation','finding':'LOD3 pooled IoU passes; minimum per-view IoU 0.992308 <0.995'},{'type':'performance_tradeoff','finding':'LOD2/3 denser than old fixed-ratio exports'}]
(P/'creature_3d_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
readme=(P/'README.md').read_text()
readme=readme.replace('**Technical asset production complete, 2026-10-12. Artistic acceptance is not recorded.**','**Round 0 accepted; review round 1 topology revision staged with explicit inherited gate failures.**')
readme=readme.replace('(**7,224,856 bytes**)',f'(**{v["bytes"]:,} bytes**)')
start=readme.index('Selected source of truth:') if 'Selected source of truth:'in readme else readme.index('Selected masters and per-level hashes');end=readme.index('Earlier rig rebuild:',start)
readme=readme[:start]+"""Selected masters and per-level hashes are in `export/selected_artifacts.json` and
`review/triangle_reduction/selected.json`. The old `work/rig_textured.blend` remains historical;
the selected LOD0 is `work/round1/lod0_selected.blend`. The accepted runtime/rig archive is immutable.

Claim a new workspace lease and use the standard project write/Blender wrappers (one process, four threads).
Rebuild from the selected measured meshes:

1. `round1_gates_export.py` (Blender) exports each chosen geometry and measures every clip.
2. `round1_pack.py` copies geometry into the original accepted rig/animation document.
3. `pack_runtime.py` rebuilds shadows, variants, atlases and viewer files.
4. `round1_verify.py`, `round1_render_packaged.py` (Blender), `final_review_run.py` (Blender),
   `validate_export.py`, binding checker and `check_viewer.py`.
5. `round1_report.py` refreshes receipts and sheets after checks.

Do not run `build_lods_run.py` for this revision: it would restore the obsolete fixed-ratio LODs.
Do not rerun paid jobs; the four retained returns remain sufficient.

"""+readme[end:]
readme=readme.replace('These are recorded artistic limitations, not hidden technical gate failures; user artistic acceptance is not recorded.','These artistic choices were accepted in round 0. The new elbow and cloth checks expose inherited failures; see the round 1 report.')
readme=readme.split('\n## Review round 1 decisions')[0]
readme=readme.replace('| Color LOD0/1/2/3 | 16,274 / 8,135 / 2,907 / 897 triangles |','| Color LOD0/1/2/3 | 7,824 / 7,787 / 6,916 / 6,710 triangles |')
start=readme.index('| Clip |');end=readme.index('## Production record',start)
readme=readme[:start]+rigtable+'\nG4/G5 and legacy G6 checks pass. New elbow/cloth checks have inherited failures. Full definitions and measurements: [review/GATES.md](review/GATES.md). Viewer passes 24 switches with no console errors.\n\n'+readme[end:]
readme+='\n## Review round 1 decisions\n\n'+table+'\n'+metric_note+'\n'+gate_note+'\nSee [HANDOFF.md](HANDOFF.md) for changed file hashes, validation and integration limits.\n'
(P/'README.md').write_text(readme)
print('ROUND1_RECORDS_WRITTEN',h)

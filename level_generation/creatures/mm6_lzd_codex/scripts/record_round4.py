import sys,json,hashlib,struct,datetime,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P/'work/python')]
from rebake_measure import measure
def read(n):return json.loads((P/n).read_text())
def write(n,d):(P/n).write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tags={0:'r4_candidate',1:'r4_candidate',2:'round4_contact_final',3:'round4_refine_0_0.001'}
metrics={str(l):measure(tags[l],l,parts=('body','bow')if l==0 else('actor',),reference='r4_reference128'if l==3 else'r4_reference')for l in range(4)}
write('review/round4/reduction_metrics.json',metrics)
assert all(v['passed']for m in metrics.values()for v in m.values()),metrics
g=read('review/round4/gates/gates.json');assert g['status']=='PASS'
viewer=read('review/viewer_check.json');assert viewer['switched']==27 and not viewer['failed']and not viewer['consoleErrors']
for n in ['check_weights.txt','check_bindings.txt']:assert 'BAD'not in(P/'review/round4'/n).read_text()
ex=read('review/round4/exports.json');info=read('export/export_info.json');intent=read('work/round4/authoring_intent.json')
for name,x in ex.items():assert sha(P/f'export/{name}.glb')==x['sha256']
files={}
for p in sorted((P/'export').glob('*.glb'))+sorted((P/'review/viewer').glob('*.glb')):
 if p.name=='mm6_lzd_lods.geometry.glb':continue
 b=p.read_bytes();d=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]])
 files[str(p.relative_to(P))]={'sha256':sha(p),'bytes':len(b),'triangles_per_mesh':[sum(d['accessors'][q['indices']]['count']//3 for q in m['primitives'])for m in d['meshes']],'images':len(d.get('images',[]))}
rows=g['gates'];gait=[r for r in rows if '/colour'in r['lod']and r['clip']in['Standing','Fidget','Walking','Running']and r['gate']in['foot_yaw_deg','lowest_sole_m','walking_lift_min_mm','walking_lift_max_mm','running_contact_pct','running_airborne_mm']]
write('review/round4/gait.json',gait)
n=intent['native_rest'];a=np.array(n['B_L_UpperArm']['head']);b=np.array(n['B_R_UpperArm']['head'])
native={'shoulder_line_yaw_deg':float(np.degrees(np.arctan2((a-b)[1],(a-b)[0]))),'pelvis_yaw_relative_bind_deg':0,'ankle_spacing_m':float(np.linalg.norm(np.array(n['B_L_Foot']['head'])-n['B_R_Foot']['head'])),'right_wrist_m':n['B_R_Hand']['head'],'left_wrist_m':n['B_L_Hand']['head'],'bow_long_axis_elevation_deg':0,'string_side':'above limbs at rest; toward archer during draw','reference':'User image 58; native front is a visual proportion reference, not a metric 3D reconstruction.'}
write('review/round4/native_comparison.json',native)
history=read('review/reduction/curve.json')
curve={'historical_round3_near_search':history,'current_triangles':{k:v['triangles']for k,v in ex.items()},'round4_shared_texture_validation':metrics,'rig_gates':'PASS: shared runner on all runtime colour/shadow LODs and 9 clips'}
write('review/round4/curve.json',curve)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4))
for ax,part in zip(axes,['body','bow']):
 rr=sorted([r for r in history if r['part']==part],key=lambda r:r['triangles'])
 for k in ['min_iou','min_ssim']:ax.plot([r['triangles']for r in rr],[r[k]for r in rr],'o-',label='round 3 '+k)
 c=ex['mm6_lzd'if part=='body'else'mm6_lzd_bow']['triangles'][0];ax.scatter([c,c],[metrics['0'][part]['min_iou'],metrics['0'][part]['min_ssim']],marker='x',s=85,label='round 4 shared rebake')
 ax.set_title(part);ax.set_xlabel('Triangles');ax.set_ylim(.90,1.005);ax.legend(fontsize=7)
fig.tight_layout();fig.savefig(P/'review/round4/curve.png',dpi=150);plt.close(fig)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for l in range(4):
 for part in (('body','bow')if l==0 else('actor',)):
  sheet=Image.new('RGB',(1400,1485),(40,42,45));draw=ImageDraw.Draw(sheet);draw.text((12,8),f'LOD{l} {part}: reference left / current right; eight views',font=font,fill='white')
  for i in range(8):
   for j,tag in enumerate(['r4_reference128'if l==3 else'r4_reference',tags[l]]):
    im=Image.open(P/f'review/rebake/{tag}_{part}_l{l}_{i}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(46,48,51,255));bg.alpha_composite(im);bg=bg.convert('RGB');bg.thumbnail((350,350));sheet.paste(bg,((i%2)*700+j*350+(350-bg.width)//2,45+(i//2)*360+(350-bg.height)//2))
  sheet.save(P/f'review/round4/comparison_{part}_lod{l}.jpg',quality=93)
countrows='\n'.join(f"| export/{k}.glb | {' / '.join(map(str,v['triangles']))} | {v['bytes']:,} | {v['sha256']} |"for k,v in ex.items())
foot='\n'.join(f"| {c} | {s} | {max(r['worst']for r in gait if r['clip']==c and r['region']==s and r['gate']=='foot_yaw_deg'):.3f} |"for c in ['Standing','Fidget','Walking','Running']for s in'LR')
image_rows='\n'.join(f"| {l} | {part} | {m['min_iou']:.6f} | {m['pooled_iou']:.6f} | {m['min_ssim']:.6f} |"for l,parts in metrics.items()for part,m in parts.items())
(P/'review/round4/README.md').write_text(f"""# Round 4 reduction and validation

[Curve](curve.png), [body](comparison_body_lod0.jpg), [bow](comparison_bow_lod0.jpg),
[LOD1](comparison_actor_lod1.jpg), [LOD2](comparison_actor_lod2.jpg), [LOD3](comparison_actor_lod3.jpg),
[shared gates](gates/gates.md), [complete gate data](gates/gates.json).

The historical near search reduced body 12,987 to 9,858; 9,545 failed SSIM (0.928681).
Bow 2,236 to 2,012 to 1,788; 1,564 failed silhouette IoU (0.986866).
Round 4 removes four coplanar body triangles, fixes anatomy/waist, and migrates to one shared texture set.
The chart identifies historical reduction and current shared-map validation separately.

Near compares the current mesh/rebake against accepted near geometry before UV repacking, using actual tier-A ramps
at 700 px from eight views. Distance comparisons use the assembled actor at 550/220/88 px, pooled IoU >=0.97.
Near/LOD1/LOD2 use 32 samples; the 88 px pair uses 128 samples and the standard Cycles filter on both meshes.
Earlier rejected far candidates, including the 0.969594 result and filter trials, remain under review/rebake.
The selected far geometry adds a 1 mm vertical surface offset outside the held grip; shared floor gates are rerun.

| LOD | Part | Minimum IoU | Pooled IoU | Minimum SSIM |
|---|---|---:|---:|---:|
{image_rows}

Maps retain 2048 body / 1024 head / 1024 bow resolution with 16 px EXTEND dilation.
The head uses two large charts instead of fragmented islands. All LODs share the near maps/material indices.
The existing atlas helper merges body/head without downsampling. Embedded images: body 32 to 8; bow 16 to 4.
No skin recolour was introduced. Controlled renders establish review appearance, not native game lighting.
GLB export removes degenerate triangles only; the shared gate runner checks the exact runtime colour/shadow geometry.
""")
now=datetime.datetime.now(datetime.timezone.utc).isoformat();actors=sha(P/'integration/actors.yml')
receipt={'status':'passed','completed_at':now,'files':files,'runtime':ex,'actors_changed':True,'actors_sha256':actors,'sources':{k:v for k,v in intent.items()if k.startswith('source_')},'native_comparison':native,'shared_gates':{'status':g['status'],'counts':g['counts'],'runner_sha256':g['runner_sha256'],'path':'review/round4/gates/gates.json'},'gait':gait,'reduction':curve,'viewer':viewer,'cast':'Exact Attack channels/accessors; Socket_Arrow at 0.734375 s','body_boundaries':read('review/round4/body_boundaries.json'),'budget_credits':100,'credits_spent':60,'credits_added':0,'integration_executed':False}
write('review/review_round4.json',receipt)
hashrows='\n'.join(f"| {k} | {v['sha256']} | {' / '.join(map(str,v['triangles_per_mesh']))} |"for k,v in files.items())
summary=f"""# HANDOFF — MM6 LizardArch (mm6:lzd)

**Review round 4 technical work complete.** Artistic acceptance and native integration remain with the orchestrator.
No commit, build, game launch or assets_dev write. Meshy **60 / 100 credits**, zero added this round.

Replace both runtime GLBs and merge [integration/actors.yml](integration/actors.yml).
Native rest: square shoulders/pelvis, broad flat feet, free claw beside thigh, horizontal hip bow with string above.
Cast is an exact named Attack copy: **Socket_Arrow at 0.734375 s**; both clips last **1.7 s**.
Scale **{info['scale']:.9f}**, stride **{info['stride_length_m']:.9f} m**, descriptors 571/572/573.

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
{countrows}

Review: [viewer](review/viewer/index.html), [front](review/clips_front.jpg), [side](review/clips_left.jpg),
[three-quarter](review/clips_three_quarter.jpg), [hands](review/exported_hands.jpg),
[release](review/release_sheet.jpg), [curve and gates](review/round4/README.md),
[receipt](review/review_round4.json). Historical sections below are superseded by Review round 4.

"""
old=(P/'HANDOFF.md').read_text();history_text=old[old.index('## Review round 1'):].split('## Review round 4')[0]
details=f"""## Review round 4

- Library RelaxIdle fitted to native image 58: shoulder-line yaw {native['shoulder_line_yaw_deg']:.6f} degrees,
  pelvis yaw relative to bind 0, ankle spacing 0.450 m, wrist heights R 0.925 / L 0.960 m, bow elevation 0 degrees.
  The horizontal carry supersedes round 3's incorrect vertical carry.
- Library UnarmedGetHitF1 supplies backward recoil and recovery. Walking has a neutral free wrist/palm toward thigh.
  UnarmedRunForward replaces RelaxRunForward. Active clips meet the new rest at their boundaries.
- Mixamo Shooting Arrow supplies the draw/release motion, with planted legs and anatomical arm fitting.
  Global yaw is bounded to pelvis 32 / shoulders 72 degrees; the head faces the target.
  The drawing hand anchors by the cheek with a straight wrist, and the string faces the archer.
  Arrow visibility begins after nocking. Cast option (b) remains a byte-exact copy, verified by the packer.
- Lower-body waist extends beneath the tunic, and lower tunic weights blend into the pelvis.
  The former draw gap is covered. Welded body boundary inventory records 20 lower-body edges at the\n  covered waist (z 1.049–1.156 m), 22 left-arm and 20 right-arm edges at the covered shoulder/sleeve\n  interfaces; these are intentional component openings. No open lower-leg boundary was found.\n  See review/round4/body_boundaries.json and exported draw/side captures.
- Death uses the library backward fall; the bow drops as fingers open at 1.0 s.
  Reduced feet and grip surfaces are fitted geometrically. Gate thresholds were not loosened.
- All LODs now share the near texture set, accepted resolutions, and 16 px dilation.
  Body embedded images 32 to 8; bow 16 to 4. See the linked reduction curve and paired images.
- integration/actors.yml **changed**: updated scale/stride metadata and round marker.
  Attack/cast release remains **0.734375 s**, socket **Socket_Arrow**, cast **Cast** on all tiers.
  Actors SHA-256: {actors}.
- Shared runner **PASS: 7,416 passing checks, zero FAIL, zero UNVERIFIED**, all nine clips and all colour/shadow LODs.
  check_bindings.py and check_weights.py print **no BAD lines**, worst weight-sum error 0.000000.
  Viewer **27/27** tier/clip switches, zero console errors; clip sheets and browser captures regenerated.

Worst per-foot yaw over each cycle, across all colour LODs:

| Clip | Foot | Maximum absolute yaw (degrees) |
|---|---|---:|
{foot}

Walking swing peaks are about 97–98 mm; Running has about 97.4% contact and at most 34.5 mm brief flight.
Full per-clip/LOD wrist, elbow, palm, stretch, penetration and floor metrics are in the shared gate report.

Exported file receipt (triangle lists include colour and shadow meshes where present):

| File | SHA-256 | Triangles per mesh |
|---|---|---|
{hashrows}

Current inputs: scripts/round4_author.py and round4_repair.py; maps from round4_textures.py;
review/round4/lod_selection.json; near motion/geometry in round4_refit.py;
selected distance geometry exported by round4_distance_export.py; packaging in round4_pack.py. work/master.blend and work/master_export.blend are current editable/export checkpoints.
Source provenance is recorded in work/round4/authoring_intent.json. Historical round-3 exporters are not current inputs.

Remaining limits: bow limbs are rigid while string/arrow animate; far silhouettes are judged at their switch sizes.
No native install, game lighting comparison, indoor/outdoor capture or runtime regression was run:
Batch rules delegate these to the orchestrator. Artistic acceptance remains pending.
"""
(P/'HANDOFF.md').write_text(summary+history_text+'\n'+details)
(P/'README.md').write_text("""# MM6 Lizard Archer — review round 4

Technical handoff is ready; artistic acceptance and game integration remain pending.
[HANDOFF](HANDOFF.md#review-round-4) lists current hashes, counts, bindings and limitations.

- Native square stance, flat feet, relaxed free claw; horizontal bow with string above its limbs.
- Library idle/hit/run/shot/death, anatomical arm fitting, closed waist overlap.
- Cast is an exact Attack copy; Socket_Arrow at 0.734375 s; duration 1.7 s.
- Body LODs 9,854 / 5,141 / 2,172 / 691; bow 1,788 / 964 / 388 / 110.
- One shared LOD texture set, 2048/1024/1024 source resolutions and 16 px dilation.
- Shared gates pass all runtime LODs/clips; bindings and weights clean; viewer 27/27.
- [Curve and comparisons](review/round4/README.md), [viewer](review/viewer/index.html),
  [complete receipt](review/review_round4.json). Meshy 60 / 100, zero new credits.

Resume only after reclaiming the workspace lease. Current scripts and inputs are listed in HANDOFF.
Round 3's vertical carry and per-LOD maps are superseded. No install, build, game launch or commit was made.
""")
progress=read('creature_3d_progress.json');progress.update(status='complete',stage='batch_handoff_ready',substep='review_round_4_complete',updated_at=now,completed_at=now,exports={k+'.glb':v for k,v in ex.items()},clips=info['clips'],gates={'status':'technical_pass','receipt':'review/round4/gates/gates.json'},open_faults=['Rigid bow limbs; animated string and arrow.','Far silhouette is close to its 0.97 threshold at 88 px.','Native integration, lighting, captures and regressions are delegated to the orchestrator.'],next_action={'owner':'orchestrator','action':'Replace both round 4 GLBs, merge staged bindings, run registry and native indoor/outdoor/shared-world checks.'});progress['review_round_4']={'status':'passed','completed_at':now,'receipt':'review/review_round4.json','runtime_files':ex,'actors_changed':True,'actors_sha256':actors,'additional_credits':0}
progress['integration']['status']='revised_body_bow_and_bindings_pending_orchestrator'
progress['correction_ledger'].append({'finding':'Round 4 native stance, wrist, draw anatomy, waist gap and texture memory','repair':'Square horizontal-bow rest; library motion; anatomical grip/draw; waist overlap; shared LOD maps and shared gates.','status':'resolved'})
progress['triangle_budget']={'body_lods':ex['mm6_lzd']['triangles'],'bow_lods':ex['mm6_lzd_bow']['triangles'],'combined_lods':[a+b for a,b in zip(ex['mm6_lzd']['triangles'],ex['mm6_lzd_bow']['triangles'])],'minimisation_receipt':'review/round4/README.md'}
write('creature_3d_progress.json',progress)
print('ROUND 4 RECORDED')

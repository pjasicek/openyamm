"""Create the self-contained project review metadata and exact integration proposals."""
import sys,json,hashlib,copy,struct,io,re
from pathlib import Path
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'));from build_actor_lods import read_glb,write_glb
V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True);(V/'feedback').mkdir(exist_ok=True)
for file in ['index.html','review.js']:
 s=(P.parent/'mm6_arc1_codex/review/viewer'/file).read_text().replace('MM6 Archer','MM6 PeasantF3').replace('mm6-arc1-codex','mm6-mfp-codex').replace('mm6:arc1','mm6:mfp').replace('mm6_arc1','mm6_mfp')
 s=s.replace('Native blue, red and green cloth tiers. Inspect the bow draw, arrow/fireball release and eight animations; use frame stepping and close cameras for grip and face details.','Cutpurse, Bounty Hunter and Assassin: native green, red and blue blouses. Inspect the relaxed rest, reverse-grip knife attack and eight animations.')
 if file=='review.js':
  s=s.replace('controls.maxDistance = 12','controls.maxDistance = 30')
  s=s.replace('model=gltf.scene;model.animations=gltf.animations;scene.add(model);', 'model=gltf.scene;model.animations=gltf.animations;model.traverse(o=>{if(o.isMesh)o.frustumCulled=false;});scene.add(model);')
 (V/file).write_text(s)
(V/'feedback/user_feedback.json').write_text(json.dumps({'creature':'mm6:mfp','findings':[]}))
sel=json.loads((P/'review/reduction_soft/selection.json').read_text());tex=Path(sel['0']['textures']);info=json.loads((P/'export/export_info.json').read_text())['0'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runtime_doc,_=read_glb(P/'export/mm6_mfp_level0.glb')
info['durations']={a['name']:max(runtime_doc['accessors'][sampler['input']]['max'][0] for sampler in a['samplers']) for a in runtime_doc['animations']}
manifest={'revision':'mm6_mfp_codex_review2','default_clip':'Standing','default_model':'mfp_a','model':'mm6_mfp_a.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for variant,label in zip(['mfp_a','mfp_b','mfp_c'],['Cutpurse — green','Bounty Hunter — red','Assassin — blue']):
 doc,data=read_glb(P/'export/mm6_mfp_level0.glb');data=bytearray(data)
 for mat in doc['materials']:
  name=mat['name'];stem={'PeasantF3_A':'mfp','PeasantF3Head_A':'mfp_head'}.get(name)
  if not stem:continue
  pixels=(tex/f'{stem}_{variant}.png').read_bytes();data.extend(b'\0'*(-len(data)%4));doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(pixels)});data.extend(pixels);doc['images'].append({'bufferView':len(doc['bufferViews'])-1,'mimeType':'image/png'});t=mat['pbrMetallicRoughness']['baseColorTexture'];doc['textures'].append(dict(doc['textures'][t['index']],source=len(doc['images'])-1));t['index']=len(doc['textures'])-1
 file=V/f'mm6_{variant}.glb';write_glb(file,doc,data);h=sha(file);manifest['models'].append({'id':variant,'label':label,'revision':manifest['revision'],'url':file.name+'?v='+h[:12],'sha256':h})
provenance={'Standing':'Native upright relaxed pose; subtle breathing; authored gap fill','Walking':'Humanoid RelaxWalkFemale3, damped upper motion and planted native gait IK','Running':'Humanoid UnarmedRunForward2 arm swing over the planted native-size gait; stride 1.55 × walk','Attack':'Humanoid DaggerAttackR3; stance plant and discrete leg steps; reverse-grip knife; brisk recovery to rest by 1.125 s; blow .656250 s','Hit':'Humanoid UnarmedGetHitF1; planted native adaptation, retimed to .8125 s','Death':'Mixamo Falling Forward Death; paired knee/hand floor constraints and garment fit','Dead':'Exact last Death pose held','Fidget':'Native relaxed glance and 3 mm weight shift; authored gap fill'}
patterns={'Standing':'mfpstaa[024].png','Walking':'mfpwka[012].png','Running':'mfpwka[012].png','Attack':'mfpat*.png','Hit':'mfpwi*.png','Death':'mfpdi*.png','Dead':'mfpdi*.png','Fidget':'mfpf*.png'}
for name,duration in info['durations'].items():
 images=sorted((P.parent/'mm6_mfp/native').glob(patterns[name]))[:6] or [P.parent/'mm6_mfp/native/mfpstaa0.png']
 manifest['clips'][name]={'label':name,'duration':duration,'mode':'loop'if name in ['Standing','Walking','Running','Dead']else'once','provenance':provenance[name],'anchors':[{'time':0,'label':name,'phase':provenance[name],'source_images':['../../../mm6_mfp/native/'+f.name for f in images]}]}
manifest['model_sha256']=manifest['models'][0]['sha256'];(V/'manifest.json').write_text(json.dumps(manifest,indent=2))
# Use the exported measured Standing height rather than the model service's advertised height.
height=info['standing_height_m'];native_height=253*.699997;scale=native_height/height
I=P/'integration';I.mkdir(exist_ok=True);blocks=[]
for suffix,skin in zip('ABC',['mfp_a','mfp_b','mfp_c']):
 blocks.append(f'''- descriptor: PeasantF3 {suffix}
  model: worlds/mm6/models/mm6_mfp.glb
  scale: {scale:.9f}
  yaw_offset: -1.570796327
  skin: {skin}
  animation:
    cast: Attack
    run: Running
    stride_length: 0.9
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 60
      max_pitch_degrees: 35
    events:
      attack_melee: {{impact: 0.656250000000}}
      attack_ranged: {{impact: 0.656250000000}}
      cast: {{impact: 0.656250000000}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  attachments:
  - model: worlds/mm6/models/mm6_mfp_knife.glb
    node: Knife
''')
(I/'actors.yml').write_text('# Staged proposal only; Review round 2: Attack 1.125 s, impact unchanged .65625 s. Merge descriptors; orchestrator installs exports with tools/install_model.py.\n\n'+'\n'.join(blocks))
(I/'scale.json').write_text(json.dumps({'native_visible_px':253,'native_scale':.699997,'native_world_height':native_height,'export_standing_height_m':height,'scale':scale,'bounds_world':[native_height*.95,native_height*1.05]},indent=2))
(I/'regression.md').write_text(f"""# Orchestrator regression proposal

Case: mm6_mfp_peasantf3_codex. Outdoor: oute3.odm; indoor: 6d19.blv. Summon 601, 602 and 603 together.
Standing visible height {native_height:.6f} world units, allowed [{native_height*.95:.6f}, {native_height*1.05:.6f}].
All tiers share height within 0.1 world unit; green/red/blue blouse only. Confirm native-size lineup and quarter views.
Check all eight clips, upright relaxed Standing/Fidget, flat soles, 8–12 cm walk swing and mostly grounded Run.
Stride .9 m; runtime Running multiplier 1.55 gives 1.395 m. Check ordinary speeds 200/220/240 and boosted running.
Knife is visible only during Attack, attached to right hand; edge-first target blow at .656250 s.
Noncasters alias animation.cast to Attack. Test Hit, Fidget, death transition and exact held corpse, braid and skirt.
Inspect face, five fingers, head-look yaw/pitch bounds, head-look disabled during Death/Dead, and no contact through cloth.
Check all four colour/shadow LODs across switches, ramp colours, normals, dull grey steel and shadow acne.
Verify save/load, indoor/outdoor actor registry and unaffected legacy descriptors with the normal regression workflow.
No production session game launch, build, live registry edit or runtime installation was performed.
""")
(I/'playbook_notes.md').write_text("""# Production lessons

- Retarget Mixamo forward falls using initial yaw, not the projected pelvis yaw at every frame: projection becomes singular during a prone fall.
- Appending Blender actions can clear fake-user retention. Set fake users explicitly before saving candidates; assert all eight actions before export.
- Fit knife geometry to its actual handle axis. Meshy blade/handle axes need not match the object's axes; the Knife joint's local Z is the blade axis here.
- Weight necklaces by connected piece to head/neck/chest; a single height band can accidentally give low necklace vertices arm weights.
- Cap garment openings for inside/outside classification. Do not classify limbs after they exit the hem as penetration.
- Reduction must be checked with Eevee/PBR normals and rebaked tier textures. Workbench does not test tangent normals.
- Rebake each distance LOD and inspect animation. A visually passing collapse can expose a calf; fit affected under-garment vertices against all sampled poses.
- Keep source Attack speed as reference when measuring angular changes. DaggerAttackR3 contains a fast authored follow-through.
""")
sources=[]
for folder in [P.parent/'mm6_mfp/native',P.parent/'mm6_mfp/native_variants']:
 for file in sorted(folder.glob('*.png')):sources.append({'path':str(file.relative_to(ROOT)),'sha256':sha(file)})
for name in ['humanoid_set/1Hand.glb','humanoid_set/Relax.glb','humanoid_set/Unarmed.glb','mixamo/Falling Forward Death.fbx']:
 file=ROOT/'anim_library'/name;sources.append({'path':str(file.relative_to(ROOT)),'sha256':sha(file)})
(P/'source/native_inputs.json').write_text(json.dumps(sources,indent=2))
(P/'source/clip_candidates.json').write_text(json.dumps({'selected':provenance,'rejected':{'DaggerAttackR2':'R3 better actual blade direction and native arm arc','RelaxLaydownLayDown':'Not a native falling death; replaced by Mixamo Falling Forward Death'},'paid_animation_jobs':0},indent=2))
(P/'source/ANIMATION_STUDY.md').write_text((P/'source/ANIMATION_STUDY.md').read_text().split('\n\n## Final selected clips')[0]+'\n\n## Final selected clips\n\n'+'\n'.join(f'- {k}: {v}.'for k,v in provenance.items())+'\n')
# A colour mesh at each level, with LOD0 animations and the same verified inverse binds.
doc,data=read_glb(P/'export/mm6_mfp_lods.glb')
for level in range(4):
 clone=copy.deepcopy(doc);next(n for n in clone['nodes']if n.get('name')=='PeasantF3')['mesh']=level;write_glb(P/f'work/final_check_lod{level}.glb',clone,data)
print('REVIEW_READY',scale,manifest['models'],flush=True)

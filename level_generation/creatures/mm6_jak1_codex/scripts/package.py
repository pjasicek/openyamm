"""Build the two runtime candidates, viewer manifest and static integration entries."""
from pathlib import Path
import sys,subprocess,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];E=P/'export'
def run(script,*args):
 subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
# Shadow geometry matches each measured colour LOD; animation and skin are shared.
sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array
import copy
run(ROOT/'level_generation/creatures/claude_shared/region_variants.py',E/'mm6_jak1_lods.glb',E/'mm6_jak1_combined.glb',P/'textures/jak1_ramps_runtime.json','--extra','Jackalman','openyamm_specular=1','--extra','Jackalman','openyamm_specular_mask=true','--extra','Jackalman','pbr.metallicFactor=0','--extra','HookedStaff','openyamm_specular=1','--extra','HookedStaff','openyamm_specular_mask=true','--extra','HookedStaff','pbr.metallicFactor=0')
# Review each actual final colour LOD, including the protected staff silhouette.
preview_doc,preview_binary=read_glb(E/'mm6_jak1_combined.glb')
for level in range(4):
 preview=copy.deepcopy(preview_doc);next(n for n in preview['nodes']if n.get('name')=='Jackalman')['mesh']=level
 write_glb(P/f'work/lod_preview_{level}.glb',preview,preview_binary)
run(ROOT/'tools/split_attachment.py',E/'mm6_jak1_combined.glb','--joint','Staff','--body',E/'mm6_jak1_body_unmerged.glb','--attachment',E/'mm6_jak1_staff.glb')
run(ROOT/'tools/merge_head_material.py',E/'mm6_jak1_body_unmerged.glb',E/'mm6_jak1.glb')
run(P/'scripts/viewer_tiers.py')
run(P/'scripts/make_sheets.py','clips')
shutil.copyfile(P/'references_hd/staff_design.png',P/'review/staff_design.png')
info=json.loads((E/'export_info.json').read_text());cast=json.loads((P/'review/cast_gate.json').read_text())
provenance={
'Standing':'Local Mixamo Standard Idle, fitted source-frame retarget; right staff grip and relaxed free arm.',
'Walking':'Local humanoid ArmedWalk with upright staff carry. Runtime run deliberately aliases this native gait.',
'Attack':'Local 2Hand Staff / StaffAttack2; two-handed fixed grip, discrete planted step, library weight shift and follow-through.',
'Cast':'Local 2Hand Staff / StaffCastLAttack1; planted step, staff thrust and free-hand gesture; StaffTip launch.',
'Hit':'Local UnarmedGetHitF1 at 35% amplitude; planted feet and carried staff react with the body.',
'Death':'Local 2Hand Staff / StaffDeath1; library forward fall, hand release and secondary staff drop, grounded corpse.',
'Dead':'Exact final Death pose held for one second.',
'Fidget':'Local Mixamo Standing Idle 02 Looking, planted stance, subtle knee dip and staff tilt.'
}
prefix={'Standing':'st','Walking':'wk','Attack':'at','Cast':'at','Hit':'wi','Death':'dy','Dead':'dy','Fidget':'fi'}
manifest={'revision':'mm6_jak1_codex_review_round2','model':'mm6_jak1_a.glb','default_clip':'Standing','default_model':'jak1_a','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Defender of VARN — blue','Sentinel of VARN — purple','Guardian of VARN — red']):
 path=P/f'review/viewer/mm6_jak1_{tier}.glb';sha=hashlib.sha256(path.read_bytes()).hexdigest()
 manifest['models'].append({'id':f'jak1_{tier}','label':label,'revision':manifest['revision'],'url':path.name+'?v='+sha[:12],'sha256':sha})
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 duration=info['clips'][role];letters='a' if role=='Standing' else ('f' if role=='Dead' else 'abcdef');anchors=[]
 for i,letter in enumerate(letters):
  images=[f'../../../mm6_jak1/native/jak1{prefix[role]}{letter}{view}.png' for view in (range(5) if role in ('Standing','Walking') else [0])]
  images=[s for s in images if (P/'review/viewer'/s).resolve().exists()]
  assert images,(role,letter)
  anchors.append({'time':duration*i/max(1,len(letters)-1),'label':role+' '+letter.upper(),'phase':'Native A palette; normalized phase reference, approximate pose correspondence. Cast uses a local staff-library gesture.','source_images':images})
 manifest['clips'][role]={'label':role,'duration':duration,'mode':'loop' if role in ('Standing','Walking','Dead') else 'once','provenance':provenance[role],'anchors':anchors}
manifest['model_sha256']=manifest['models'][0]['sha256'];(P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2))
post=json.loads((P/'review/posture.json').read_text());scale=294*.699997/post['Standing']['body_height_m'];blow=json.loads((P/'review/blow_gate.json').read_text())[0];I=P/'integration';I.mkdir(exist_ok=True)
blocks=[]
for tier in 'abc':
 d=tier.upper();ref='' if tier=='a' else '  scale_reference: Jackalman A\n'
 blocks.append(f"""- descriptor: Jackalman {d}
  model: worlds/mm6/models/mm6_jak1.glb
  scale: {scale:.6f}
{ref}  yaw_offset: -1.570796327
  skin: jak1_{tier}
  animation:
    cast: Cast
    run: Walking
    stride_length: {info['stride_m']:.9f}
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 25
      max_pitch_degrees: 12
    events:
      attack_melee: {{impact: {blow['impact_s']:.9f}}}
      attack_ranged: {{impact: {blow['impact_s']:.9f}}}
      cast: {{impact: {cast['launch_seconds']:.9f}, launch_socket: StaffTip}}
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
  - model: worlds/mm6/models/mm6_jak1_staff.glb
    node: Staff
""")
(I/'actors.yml').write_text('# Exact proposed entries; batch orchestrator merges them into the MM6 actors registry.\n'+'\n'.join(blocks))
(P/'review/calibration.json').write_text(json.dumps({'native_frame':'../mm6_jak1/native/jak1sta0.png','native_alpha_height_px':294,'native_descriptor_scale':.699997,'native_visible_height_units':294*.699997,'posed_body_height_m':post['Standing']['body_height_m'],'scale':scale,'stride_m':info['stride_m'],'impact_s':blow['impact_s']},indent=2))
print('Packaged two runtime GLBs, three-tier viewer manifest and exact actor entries.')


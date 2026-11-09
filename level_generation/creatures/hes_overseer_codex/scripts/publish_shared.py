from pathlib import Path
import sys,copy,json,yaml
P=Path('level_generation/creatures/hes_overseer_codex').resolve()
sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'hes_kept_codex/lodrep')]
from build_actor_lods import read_glb,write_glb,merge_shadow
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import _compact
from splice_lods import compact
from splice_lods import tuck_shadow
D,B=read_glb(P/'export/hes_overseer.glb');B=bytearray(B)
N=next(n for n in D['nodes'] if 'mesh' in n);base=D['meshes'][N['mesh']]
chain=[N['mesh']]+base['extras']['openyamm_lods']
for mi in chain:
 D['meshes'][mi]['primitives']=[p for p in D['meshes'][mi]['primitives'] if D['materials'][p['material']]['name'].startswith(('OV_Body_','OV_Head_'))]
 assert len(D['meshes'][mi]['primitives'])==2
for level,(mi,si) in enumerate(zip(chain,base['extras']['openyamm_shadow_lods'])):
 D['meshes'][si]={'name':f'Winged_Shadow{level}','primitives':copy.deepcopy(D['meshes'][mi]['primitives'])}
D,B=_compact(D,B)
assert all('openyamm_burn_map' in m.get('extras',{}) for m in D['materials'])
write_glb(P/'export/hes_kreegan_winged.glb',D,compact(D,B))
rows=[]
for desc,skin,scale in [('Overseer','ov_a',1),('Overseer Prime','ov_b',1.1),('Court Overseer','ov_c',1.15),('Overseer Krav','ov_krav',1.3),('Overseer Ghulkat','ov_ghulkat',1.3)]:
 gh=skin=='ov_ghulkat'
 def part(stem,node):return {'model':f'worlds/hesper/models/{stem}.glb','node':node}
 attachments=([part('overseer_arc_maul','ArcMaul'),part('overseer_collar_key','CollarKey'),part('overseer_pulse_pistol','HolsterPistol'),part('overseer_holster_hanger','HolsterPistol')] if gh else [part('overseer_collar_rod','CollarRod'),part('overseer_pulse_pistol','PulsePistol')])
 if skin=='ov_krav':attachments.append(part('overseer_plasma_saber','HipSaber'))
 row={'descriptor':desc,'model':'worlds/hesper/models/hes_overseer.glb','skin':skin,'scale':round(130*scale,6),'yaw_offset':-1.570796327,
  'death_effect':{'type':'burn','start':0.,'end':.9375,'char_width':.16,'edge_width':.035,'fire_width':.3,'color':[.75,.3,1.],'brightness':2.4,'flames_per_second':220,'flame_size':24,'flame_color':[185,95,255],'light':{'color':[190,120,255],'radius':450}},
  'animation':{'cast':'Overseer_Cast','run':'Overseer_Flight','stride_length':5.6,'gait_rate':[.8,1.5],'upper_body_root':'B_Spine',
   'sockets':{'muzzle':'Socket_Muzzle','rod':'Socket_Maul' if gh else 'Socket_Rod'},
   'events':{'attack_melee':{'impact':.84375 if gh else .864583333},'attack_ranged':{'impact':.84375 if gh else .45,'release':'rod' if gh else 'muzzle'},'cast':{'impact':.75,'release':'rod'}}},
  'clips':{'standing':'Overseer_Flight','walking':'Overseer_Flight','attack_melee':'Overseer_AttackMelee','attack_ranged':'Overseer_AttackMelee' if gh else 'Overseer_AttackRanged','hit':'Overseer_Hit','dying':'Overseer_Death','dead':'Overseer_Dead','fidget':'Overseer_Flight'},'attachments':attachments}
 rows.append(row)
(P/'integration/actors.yml').write_text('# Accepted winged Overseers; source DemonFly scale 130 times the design tier scale.\n# Ghulkat emits his ranged collar pulse from the Arc Maul; the pistol remains holstered.\n'+yaml.safe_dump(rows,sort_keys=False,width=120))
print('Published shared winged body and five binding entries')

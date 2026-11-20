import json,sys
from pathlib import Path
import yaml
P=Path(__file__).resolve().parents[1];d=json.loads((P/'review/final_intent.json').read_text());scale=d['scale'];impact=d['blow']['impact_seconds'];rows=[]
for letter,tier in zip('ABC','abc'):
 row={'descriptor':'Merchant '+letter,'model':'worlds/mm6/models/mm6_mer1.glb','scale':round(scale['scale'],9),'yaw_offset':round(scale['yaw_offset'],9),'z_offset':round(scale['z_offset'],9),'animation':{'cast':'Attack','run':'Running','stride_length':.84,'upper_body_root':'B_Spine','look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':25,'max_pitch_degrees':12},'events':{role:{'impact':round(impact,9)}for role in ['attack_melee','attack_ranged','cast']}},'clips':dict(zip(['standing','walking','attack_melee','attack_ranged','hit','dying','dead','fidget'],['Standing','Walking','Attack','Attack','Hit','Death','Dead','Fidget'])),'skin':'mer1_'+tier,'attachments':[{'model':'worlds/mm6/models/mm6_mer1_club.glb','node':'Club'}]}
 if letter!='A':row['scale_reference']='Merchant A'
 rows.append(row)
I=P/'integration';I.mkdir(exist_ok=True);(I/'actors.yml').write_text('# Staged only. Merchant ids 577/578/579; no spells, Cast aliases Attack.\n'+yaml.safe_dump({'actors':rows},sort_keys=False))
(I/'regression.md').write_text("""# Proposed integration case
- Name: mm6-mer1-codex
- World/map: mm6 / oute3.odm; repeat indoors on a normal MM6 BLV after outdoor verification.
- Summon ids: 577, 578, 579 (Merchant A, B, C).
- Native visible-height anchor: 177.099 game units. Broad regression size bounds: 140–220.
- Install export/mm6_mer1.glb and export/mm6_mer1_club.glb into worlds/mm6/models, then merge actors.yml.
- Exercise Standing, Walking, Running, Attack, Hit, Fidget, Death and Dead; Cast resolves to Attack.
- Confirm the belt-carried club draws with the right hand for Attack and drops beside the corpse; pouch stays at the right-front hip.
- Inspect all three native cloth palettes, unchanged pale skin/grey cap/blue collar/brown binding/dull grey clasp.
- Check walking stride .84 m, runtime running stride 1.302 m, sole contact and all LOD switches (550/220/88 projected bound pixels).
- Verify melee impact timing from actors.yml, look controls, save/load, shadows and attachments.
- Run the MM6 actor suite and native indoor/outdoor tour against the native sprites after merging, one creature at a time.
No runtime installation, build, game process, regression execution or game screenshot was performed by this batch session.
""")
(I/'playbook_notes.md').write_text("""# Production notes for the orchestrator
- Native mer1 carries the club at the belt in Standing/Walking/Fidget, then draws it for a right-handed attack. An always-held combat idle would lose that identity.
- Owned Mixamo Standard Idle and Sword And Shield Slash were suitable; the humanoid set's mace attacks were low-guard lunges and were rejected before modelling.
- Preserve the source-frame anatomical hinge; move forearm roll into the hand and helper twist bones. Use a fixed hand-local club frame instead of rebuilding a tracking quaternion each sample.
- The engine running multiplier is 1.55. With .84 m walking stride, the planted run must span 1.302 m.
- The source Death curls a boot through this long tunic. Review the actual clothed surface and adapt the leg path before approving the fall.
- Exposed boots beyond a deeply folded hem cannot be classified by one average cap plane. The final signed-distance cloth gate samples actual cloth triangles against closed boot volumes; physical intersections remain failures.
- QEM reduction can throw a thin belt vertex away from the source surface even while the actor silhouette passes. Distance candidates now project onto their corresponding original piece, with barycentric skin transfer.
- Fresh UVs require per-piece projection, tangent-normal transport at open boundaries and explicit full atlas coverage; otherwise unprojected black patches and pouch-to-tunic bleed can survive a silhouette-only test.
- Native skin is graded in linear luminance, comparing mean, p90 and p95, then checked again after the final bakes.
""")
print('Staged three descriptors; scale',scale['scale'],'impact',impact)

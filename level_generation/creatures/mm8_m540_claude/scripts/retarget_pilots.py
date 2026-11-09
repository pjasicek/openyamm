"""Reuse completed MM6 Ogre locomotion and the locally selected wand casting source."""
from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
def retarget(src,dst,items,turn):
 os.environ['SOURCE_TURN_DEG']=str(turn)
 script=p/'scripts/retarget.py'
 sys.argv=[str(script),'--',str(src),str(dst)]+items
 runpy.run_path(str(script),run_name='__main__')
ogre=p.parent/'mm6_ogr_claude/export/mm6_ogr.glb'
retarget(p/'work/rig_head.blend',p/'work/pilot_locomotion.blend',[f'{ogre}:{name}:{name}' for name in ['Standing','Walking','Running']],0)
armed=p.parents[2]/'anim_library/humanoid_set/Armed.glb'
retarget(p/'work/pilot_locomotion.blend',p/'work/pilot_sources.blend',[f'{armed}:ArmedCastRAttack1:CastSource'],180)

relax=p.parents[2]/"anim_library/humanoid_set/Relax.glb"
retarget(p/"work/pilot_sources.blend",p/"work/pilot_sources.blend",[f"{relax}:RelaxIdle:Standing"],180)

"""Preserve the seven authored fractional string keys that Blender's frame baker omits."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes
d,blob=read_glb(P/'export/mm6_lzd_raw.glb');blob=bytearray(blob);bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_export.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for clip in d['animations']:
 if clip['name'] not in ['Attack','Cast']:continue
 a=bpy.data.actions[clip['name']];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for name in ['StringTop','StringBottom','Arrow']:
  ni=next(i for i,n in enumerate(d['nodes'])if n.get('name')==name);channels=[c for c in clip['channels']if c['target']['node']==ni]
  curves=[fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves if fc.data_path.startswith(f'pose.bones["{name}"]')]
  times=sorted({float(np.float32(k.co.x/30))for fc in curves for k in fc.keyframe_points});values={'translation':[],'rotation':[],'scale':[]};prev=None
  for t in times:
   f=t*30;f=round(f)if abs(f-round(f))<1e-4 else f;sc.frame_set(int(f),subframe=f%1);bone=rig.pose.bones[name];m=bone.parent.matrix.inverted()@bone.matrix if bone.parent else bone.matrix;loc,q,scale=m.decompose()
   if prev is not None and prev.dot(q)<0:q.negate()
   prev=q.copy();values['translation'].append(list(loc));values['rotation'].append([q.x,q.y,q.z,q.w]);values['scale'].append(list(scale))
  ti=append_accessor(d,blob,{'componentType':5126,'count':len(times),'type':'SCALAR','min':[min(times)],'max':[max(times)]},np.array(times,dtype='<f4').tobytes())
  for channel in channels:
   kind=channel['target']['path'];old=clip['samplers'][channel['sampler']];at=append_accessor(d,blob,{'componentType':5126,'count':len(times),'type':'VEC4'if kind=='rotation'else'VEC3'},np.array(values[kind],dtype='<f4').tobytes());old.update(input=ti,output=at,interpolation='LINEAR')
write_glb(P/'export/mm6_lzd_raw.glb',d,blob)
print('FRACTIONAL_STRING_KEYS_EXPORTED',flush=True)

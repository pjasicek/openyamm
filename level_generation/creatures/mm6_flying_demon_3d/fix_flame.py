"""Source envelopes reconstructed as closed curved flame tongues, with portable morphs."""
from pathlib import Path
import bpy, numpy as np, json, math
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
effect=bpy.context.scene.objects['Flying_Demon_Disintegration'];old=effect.data
bpy.context.scene.objects['Flying_Demon_Visibility'].location.z=.16
effect.location.z=.16  # Airborne body and flame share the same hover offset; ash stays on the ground.
tracks=[(t.name,t.strips[0].action,t.strips[0].action_slot,t.mute) for t in old.shape_keys.animation_data.nla_tracks]
counts=(380,150,50);count=sum(counts);rng=np.random.default_rng(61007)
# Three crossed vertical ribbons per tongue: standard glTF alpha-blend geometry.
shape=[]
for angle in (0,math.pi/3,2*math.pi/3):
 for x,z in ((-1.2,-.9),(1.2,-.9),(1.2,1.85),(-1.2,1.85)):
  shape.append((x*math.cos(angle),x*math.sin(angle),z))
shape=np.array(shape);width=len(shape);faces=[]
for k in range(count):
 for plane in range(3):
  off=k*width+plane*4;faces.extend(((off,off+1,off+2),(off,off+2,off+3)))
base=np.tile(shape*.000001,(count,1));mesh=bpy.data.meshes.new('Flying_Curved_Flame_Morphs');mesh.from_pydata(base,[],faces);mesh.update()
for m in old.materials:mesh.materials.append(m)
effect.data=mesh
for f in mesh.polygons:
 i=f.index//6;f.material_index=i%4 if i<380 else 4 if i<530 else 5;f.use_smooth=True
uv=mesh.uv_layers.new(name='Flame_UV')
for face in mesh.polygons:
 for loop in face.loop_indices:
  corner=mesh.loops[loop].vertex_index%4
  uv.data[loop].uv=((0,0),(1,0),(1,1),(0,1))[corner]
effect.shape_key_add(name='Basis');pixels=np.load(P/'work/effect_pixels.npz')
depth=rng.uniform(-.52,-.18,count);angles=rng.uniform(-math.pi,math.pi,count)
for index,letter in enumerate('abcdefg'):
 coords=[];particle=0
 for category,amount in zip(('blue','white','dark'),counts):
  yy,xx=np.where(pixels[letter+'_'+category])
  if len(xx):
   order=np.lexsort((xx,yy));chosen=np.linspace(0,len(order)-1,amount).astype(int)
   points=np.column_stack((xx[order[chosen]],yy[order[chosen]]))
   size=min(.037,max(.004,.0066*math.sqrt(len(xx)/amount)))
  else:points=np.tile([225,150],(amount,1));size=.000001
  for point in points:
   angle=angles[particle]+index*.17;c,s=math.cos(angle),math.sin(angle)
   rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
   local=shape.copy();local[:,0:2]*=2.9 if category=='white' else 2.35
   local[:,2]*=2.6 if category=='white' else 2.8
   if category=='dark':local[:,0:2]*=.30;local[:,2]*=.18
   coords.extend((local*size*rng.uniform(.95,1.05))@rotation.T+np.array([(point[0]-225)*.0066,depth[particle]*(.5 if index<2 else 1),(355-point[1])*.0066+.16]))
   particle+=1
 key=effect.shape_key_add(name='Native_'+letter.upper());key.data.foreach_set('co',np.asarray(coords,np.float32).ravel())
key=effect.shape_key_add(name='End_Empty');key.data.foreach_set('co',base.astype(np.float32).ravel())
mesh.shape_keys.animation_data_create()
for name,action,slot,mute in tracks:
 t=mesh.shape_keys.animation_data.nla_tracks.new();t.name=name;s=t.strips.new(name,0,action);s.action_slot=slot;t.mute=mute
effect['source']='Native blue/white/charred pixel envelopes. Soft flame ribbons and depth are authored 3D extrapolation.'
manifest=json.loads((P/'work/effects_manifest.json').read_text());manifest.update(triangles=len(faces),fragments=count,vertices=len(base),geometry='Overlapping soft flame ribbons using analytic alpha gradients; three crossed planes per tongue, portable glTF materials.',limitation='Native-derived volumetric flame interpretation of a sprite effect, not recovered simulation.')
(P/'work/effects_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_uv_master.blend'),compress=True)
print('Corrected death flame:',len(faces),'triangles',count,'tongues; native morph actions retained.',flush=True)

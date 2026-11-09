"""Mage-specific anatomical islands; the wooden prosthesis has no ankle deformation."""
import bpy, sys, os
import numpy as np
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body=bpy.data.objects['Body']; rig=bpy.data.objects['Rig']; mesh=body.data
parts=np.array([a.value for a in mesh.attributes['piece'].data])
co=np.array([v.co[:] for v in mesh.vertices])
def put(i, values):
    values={n:float(w) for n,w in values.items() if w>1e-6}
    assert abs(sum(values.values())-1)<1e-5, values
    for g in body.vertex_groups:g.remove([i])
    for n,w in values.items():body.vertex_groups[n].add([i],w,'REPLACE')
def ramp(x,a,b):return float(np.clip((x-a)/(b-a),0,1))
for v in mesh.vertices:
    i=v.index; p=int(parts[i]); x,y,z=co[i]; side='L' if x>0 else 'R'
    if p in [2,7,8,15,16,17,19,20,21,22]:put(i,{'B_Head':1})
    elif p==1:
        h=ramp(z,1.32,1.40);put(i,{'B_Neck':1-h,'B_Head':h})
    elif p in [3,5]:put(i,{f'B_{side}_Hand':1})
    elif p==12:put(i,{'B_R_Calf':1})
    elif p==18:put(i,{'B_L_Foot':1})
    elif p==9:put(i,{'B_Pelvis':1})
    elif p==6:
        a=ramp(z,.10,.21);put(i,{'B_L_Foot':1-a,'B_L_Calf':a})
    elif p==4:
        hip=rig.data.bones[f'B_{side}_Thigh'].head_local.z
        knee=rig.data.bones[f'B_{side}_Calf'].head_local.z
        pelvis=ramp(z,hip-.08,hip+.06);calf=1-ramp(z,knee-.07,knee+.07)
        put(i,{'B_Pelvis':pelvis,f'B_{side}_Thigh':(1-pelvis)*(1-calf),f'B_{side}_Calf':(1-pelvis)*calf})
    elif p in [10,11,13,14]:
        # Shirt and coat cuffs follow the forearm, without borrowing fingers or the opposite hand.
        a=rig.data.bones[f'B_{side}_Forearm'].head_local; b=rig.data.bones[f'B_{side}_Hand'].head_local
        t=(v.co-a).dot(b-a)/(b-a).length_squared
        h=ramp(t,.86,1.06) if p in [10,11] else 0
        put(i,{f'B_{side}_Forearm':1-h,f'B_{side}_Hand':h})
    elif p==0 and z<1.09 and not (abs(x)>.26 and z>.88):
        # The split coat panels follow their own thigh; the waist remains sewn to the sash.
        t=(1-ramp(z,.60,1.08))*.85
        put(i,{'B_Pelvis':1-t,f'B_{side}_Thigh':t})
    elif p==0:
        # Keep the fitted sleeve weights, but remove distant influences through the open coat shell.
        allowed={'B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck',f'B_{side}_Clavicle',f'B_{side}_UpperArm',f'B_{side}_Forearm',f'B_{side}_Hand'}
        ws={body.vertex_groups[g.group].name:g.weight for g in v.groups if body.vertex_groups[g.group].name in allowed}
        total=sum(ws.values());assert total>0,(i,p)
        put(i,{n:w/total for n,w in ws.items()})
for v in mesh.vertices:
    assert abs(sum(g.weight for g in v.groups)-1)<1e-4, v.index
assert all(len(mesh.vertices[i].groups)==1 and body.vertex_groups[mesh.vertices[i].groups[0].group].name=='B_R_Calf' for i in np.where(parts==12)[0])
print('WEIGHTS: normalized all vertices; rigid right peg; independent head, hands, cuffs, sash and shoe buckle')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

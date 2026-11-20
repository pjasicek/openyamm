"""Repair this Meshy revision, measure rigid limb ownership, and compare LOD0 candidates."""
import json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import bulwark_common as common

def select(obs):
    for o in bpy.context.scene.objects: o.select_set(o in obs)
    bpy.context.view_layer.objects.active=obs[0]

def triangles(o): return sum(len(f.vertices)-2 for f in o.data.polygons)

def shade(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for f in bm.faces:f.smooth=True
    for e in bm.edges:
        e.smooth=len(e.link_faces)==2 and e.calc_face_angle(0)<math.radians(38)
        e.seam=not e.smooth
    bm.to_mesh(o.data);bm.free()

def render(tag,coloured=False):
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE' if coloured=='TEXTURE' else ('OBJECT' if coloured else 'SINGLE')
    scene.display.shading.single_color=(.65,.65,.63);scene.display.shading.show_cavity=True
    scene.render.resolution_x=scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    cam=bpy.data.objects.get('ReviewCam')
    if not cam:
        cam=bpy.data.objects.new('ReviewCam',bpy.data.cameras.new('ReviewCam'));scene.collection.objects.link(cam)
    scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=7.8
    for view,(az,el) in {'quarter':(-35,18),'side':(90,0),'front':(0,0),'back':(180,0)}.items():
        a,e=math.radians(az),math.radians(el)
        d=Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
        cam.location=Vector((0,-.4,1.9))+d*18;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(P/'review/geometry'/f'{tag}_{view}.png');bpy.ops.render.render(write_still=True)

LEG_SPECS={'LF':(120,36,68),'RF':(149,77,137),'LH':(51,6,145),'RH':(33,2,78)}

def build():
    obj=common.import_raw('bulwark')
    bm=bmesh.new();bm.from_mesh(obj.data);labels=common.component_labels(bm)
    co=np.array([v.co[:] for v in bm.verts]);rows={}
    for c in range(labels.max()+1):
        pts=co[labels==c]; rows[c]={'mid':pts.mean(0),'lo':pts.min(0),'hi':pts.max(0)}
    removed={c for c,r in rows.items() if abs(r['mid'][0])<.6 and r['mid'][1]>1 and r['mid'][2]<1.75}
    names=['B_Chassis','B_Head','B_Barrel','B_Recoil_Upper','B_Recoil_Lower']+[f'B_{l}_{s}' for l in LEG_SPECS for s in ('Upper','Lower','Foot')]
    owners={};leg_centres={l:rows[v[0]]['mid'][:2] for l,v in LEG_SPECS.items()}
    for c,r in rows.items():
        mid=r['mid'];x,y,z=mid
        if c in removed:continue
        if (z<1.4 or c in {19,22,106,114,151,157,163,169}) and abs(x)>.4 and c not in {1,30,94,91,103}:
            leg=min(leg_centres,key=lambda l:np.linalg.norm(mid[:2]-leg_centres[l]))
            part='Foot' if z<.48 else ('Upper' if abs(x)<1.4 else 'Lower')
            owners[c]=f'B_{leg}_{part}'
        elif c==108:owners[c]='B_Head'
        elif c==178:owners[c]='B_Barrel'
        elif y>-.65 and z>2.0 and abs(x)<.5:
            owners[c]='B_Recoil_Upper' if z>2.55 else 'B_Recoil_Lower'
        else:owners[c]='B_Chassis' if z<1.98 else 'B_Head'
    # Body-space transform: source barrels point +Y; ring centre is the reliable chassis anchor.
    ring=(co[labels==70].min(0)+co[labels==70].max(0))/2
    transform=Matrix.Translation((ring[0],ring[1],0))@Matrix.Rotation(math.pi,4,'Z')
    corrected=np.array([tuple(transform@Vector(v)) for v in co])
    def junction(a,b):
        pa=corrected[labels==a];pb=corrected[labels==b]
        d=((pa[:,None]-pb[None,:])**2).sum(2);idx=np.argsort(d,axis=None)[:20];i,j=np.unravel_index(idx,d.shape)
        return ((pa[i]+pb[j])/2).mean(0)
    joints={}
    for leg,(upper,lower,hip) in LEG_SPECS.items():
        fp=np.concatenate([corrected[labels==c] for c,n in owners.items() if n==f'B_{leg}_Foot'])
        lp=corrected[labels==lower]
        d=((lp[:,None]-fp[None,:])**2).sum(2);idx=np.argsort(d,axis=None)[:20];i,j=np.unravel_index(idx,d.shape)
        ankle=((lp[i]+fp[j])/2).mean(0)
        sole=fp[fp[:,2]<fp[:,2].min()+.04].mean(0)
        joints[leg]={'hip':corrected[labels==hip].mean(0).tolist(),'knee':corrected[labels=={'LF':4,'RF':83,'LH':121,'RH':139}[leg]].mean(0).tolist(),'ankle':ankle.tolist(),'sole':sole.tolist(),'floor':float(fp[:,2].min())}
    layer=bm.faces.layers.int.new('part')
    component=bm.faces.layers.int.new('source_component')
    for f in bm.faces:
        c=int(labels[f.verts[0].index]);f[component]=c;f[layer]=names.index(owners[c]) if c in owners else -1
    removed_tris=sum(len(f.verts)-2 for f in bm.faces if f[layer]<0)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[layer]<0],context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(obj.data);bm.free();obj.data.transform(transform)
    parts=[]
    for n,name in enumerate(names):
        me=obj.data.copy();part=bmesh.new();part.from_mesh(me);l=part.faces.layers.int['part']
        bmesh.ops.delete(part,geom=[f for f in part.faces if f[l]!=n],context='FACES')
        bmesh.ops.delete(part,geom=[v for v in part.verts if not v.link_faces],context='VERTS')
        bmesh.ops.remove_doubles(part,verts=list(part.verts),dist=.00001)
        part.to_mesh(me);part.free()
        o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);o['part_id']=n
        o.color=(*[.25+.65*float(x) for x in np.random.default_rng(n).random(3)],1)
        for a in list(me.color_attributes):me.color_attributes.remove(a)
        # Per-foot correction moves the complete foot rigidly by under 2 cm, preserving all toe parts.
        if name.endswith('_Foot'):
            leg=name.split('_')[1]; dz=-joints[leg]['floor']
            for v in me.vertices:v.co.z+=dz
            for key in ('ankle','sole'):joints[leg][key][2]+=dz
        shade(o);parts.append(o)
    bpy.data.objects.remove(obj,do_unlink=True)
    out={'source_sha256':'b02c00ae684b0051a9019f40e156c5c7a0773bdc1f499bfb0e6ce53f792d634b','removed_fifth_leg_components':sorted(removed),'removed_triangles':removed_tris,'components':owners,'part_names':names,'joints':joints,'triangles':{o.name:triangles(o) for o in parts},'transform':list(map(list,transform))}
    (P/'work/parts.json').write_text(json.dumps(out,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_parts.blend'))
    render('parts',True)

def study():
    results=[]
    for ratio in (1.,.8,.72,.65,.5):
        bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_parts.blend'))
        parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
        reference={o.name:[v.co.copy() for v in o.data.vertices] for o in parts}
        for o in parts:
            select([o])
            if ratio<1:
                m=o.modifiers.new('Reduction','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True
                bpy.ops.object.modifier_apply(modifier=m.name)
            shade(o)
        tag=f'candidate_{round(ratio*100)}'
        bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/f'{tag}.blend'))
        render(tag)
        distances=[]
        for o in parts:
            tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons])
            distances.extend(tree.find_nearest(v)[3] for v in reference[o.name])
        results.append({'surface_p99_m':float(np.percentile(distances,99)), 'surface_max_m':float(max(distances)), 'ratio':ratio,'triangles':sum(triangles(o) for o in parts),'by_part':{o.name:triangles(o) for o in parts}})
    (P/'review/geometry/reduction.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':
    if sys.argv[-1]=='build':build()
    elif sys.argv[-1]=='study':study()
    else:raise ValueError('build or study required')

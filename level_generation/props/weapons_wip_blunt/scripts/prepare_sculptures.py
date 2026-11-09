"""Rest the six Meshy sculptures on physical supports; retain UVs and material maps."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

P=Path(__file__).resolve().parents[1]
SPECS={'ares':['6mace7','mace5'],'breaker':['item247'],'root_club':['club1'],
       'crystal_club':['club2'],'primitive_club':['7item058'],'thornbark':['item077'],
       'moon_hammer':['6hammer4','hammer3'],'zealot':['7item052'],'temple':['item068','item340'],
       'trollish_mace':['item070'],'trollish_maul':['item075'],'thunder':['mace3'],
       'simple_mace':['mace1'],'wonder':['mace4'],'kings_scepter':['item249'],'mash':['7item232'],
       'dwarven':['7item057'],'dark_hammer':['hammer2'],'overlord':['item078'],'killer':['club3'],
       'sledge':['item071'],'crude':['7item050'],'sturdy':['item066'],'mekorig':['7item231']}


def main():
    out=P/'work/meshy';out.mkdir(exist_ok=True)
    only=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set(SPECS)
    for name,icons in SPECS.items():
        if name not in only:continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        folder=P/'meshy/meshy'/f'{name}_textured_v1'
        bpy.ops.import_scene.gltf(filepath=str(folder/'model_urls_glb.glb'))
        objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        points=np.array([v.co[:] for v in o.data.vertices]);_,axes=np.linalg.eigh(np.cov(points.T))
        along=axes[:,-1]
        if along[2]<0:along=-along
        up=np.array([0.,-1.,0.]);up-=along*np.dot(up,along);up/=np.linalg.norm(up)
        across=np.cross(along,up);rotation=np.stack([across,along,up]);assert np.isclose(np.linalg.det(rotation),1)
        points=points@rotation.T
        # A broad skull and a narrow grip need different heights to touch the floor.
        ylo,yhi=points[:,1].min(),points[:,1].max();span=yhi-ylo
        back=points[points[:,1]<ylo+.15*span];front=points[points[:,1]>ylo+.65*span]
        angle=math.atan2(back[:,2].min()-front[:,2].min(),.72*span)
        c,s=math.cos(angle),math.sin(angle)
        points=points@np.array([[1,0,0],[0,c,-s],[0,s,c]]).T
        lo,hi=points.min(0),points.max(0);points-=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]
        points/=max(hi[0]-lo[0],hi[1]-lo[1])
        for v,p in zip(o.data.vertices,points):v.co=p
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
        boundary=[e for e in bm.edges if e.is_boundary]
        uv_layer=bm.loops.layers.uv.active
        old_uv={v:[loop[uv_layer].uv.copy() for loop in v.link_loops] for v in bm.verts} if uv_layer else {}
        repairs=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces'] if boundary else []
        for face in repairs:
            for loop in face.loops:
                options=old_uv.get(loop.vert,[])
                if options:loop[uv_layer].uv=options[0]
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        remaining=[e for e in bm.edges if e.is_boundary]
        # Meshy's nonplanar gaps can defeat ngon triangulation.
        pending=set(remaining)
        while pending:
            first=pending.pop();component={first};vertices=set(first.verts);changed=True
            while changed:
                connected={e for e in pending if any(v in vertices for v in e.verts)}
                changed=bool(connected);component.update(connected);pending-=connected
                vertices.update(v for e in connected for v in e.verts)
            degrees=[sum(e in component for e in v.link_edges) for v in vertices]
            print('CLOSURE',name,len(vertices))
            assert len(vertices)<=64 and all(d==2 for d in degrees),(name,'complex boundary')
            ordered=[next(iter(vertices))];previous=None
            while True:
                neighbors=[e.other_vert(ordered[-1]) for e in ordered[-1].link_edges if e in component]
                nxt=next(v for v in neighbors if v!=previous)
                if nxt==ordered[0]:break
                previous=ordered[-1];ordered.append(nxt)
            center=sum((v.co for v in ordered),Vector())/len(ordered)
            inner=[bm.verts.new(center+(v.co-center)*.35) for v in ordered]
            for v,source in zip(inner,ordered):old_uv[v]=old_uv.get(source,[])
            triangles=[]
            for i in range(len(ordered)):
                j=(i+1)%len(ordered)
                triangles.extend([(ordered[i],ordered[j],inner[j]),(ordered[i],inner[j],inner[i])])
            ordered=inner
            left,right=0,len(ordered)-1
            while right-left>1:
                triangles.append((ordered[left],ordered[left+1],ordered[right]));left+=1
                if right-left>1:
                    triangles.append((ordered[left],ordered[right-1],ordered[right]));right-=1
            for triangle in triangles:
                face=bm.faces.new(triangle);repairs.append(face)
                if uv_layer:
                    options=[value for v in triangle for value in old_uv.get(v,[])]
                    for loop in face.loops:
                        own=old_uv.get(loop.vert,options)
                        if own:loop[uv_layer].uv=own[0]
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        remaining=[e for e in bm.edges if e.is_boundary]
        if remaining:
            report={'vertices':[list(v.co) for v in bm.verts],
                    'edges':[[list(v.co) for v in e.verts] for e in remaining],
                    'degree':[sum(edge.is_boundary for edge in v.link_edges) for e in remaining for v in e.verts]}
            (P/'review'/f'{name}_boundary_defects.json').write_text(json.dumps(report))
        assert not remaining,(name,'unclosed boundary',len(remaining))
        bm.to_mesh(o.data);bm.free()
        if o.data.has_custom_normals:
            o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        for face in o.data.polygons:face.use_smooth=True
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        o.data.update()
        normals=[n.vector.copy() for n in o.data.corner_normals]
        fixed_normals=0
        for face in o.data.polygons:
            average=sum((normals[i] for i in face.loop_indices),Vector())/len(face.loop_indices)
            if average.dot(face.normal)<.01:
                fixed_normals+=1
                for i in face.loop_indices:normals[i]=face.normal.copy()
        o.data.normals_split_custom_set(normals)
        assert len(o.data.polygons)<15000
        for icon in icons:
            path=out/f'{icon}_raw.glb'
            bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True)
            (out/f'{icon}.json').write_text(json.dumps({'icon':icon,'design':name,'triangles':len(o.data.polygons),
                'route':'imagegen HD master + Meshy Smart Topology textured + local PBR correction',
                'export':str(path.relative_to(P)),'texture_size':1024,
                'boundary_edges_repaired':len(boundary),'closure_faces':len(repairs),
                'corrected_shading_normals':fixed_normals},indent=2)+'\n')
            print('SCULPTURE',icon,len(o.data.polygons))


if __name__=='__main__':main()

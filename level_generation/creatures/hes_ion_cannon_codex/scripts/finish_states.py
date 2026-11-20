"""Add the Crown's c5-only prong arcs to the checked LOD master, then export its seven static states."""
import json
from pathlib import Path
import sys

import numpy as np

P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P.parents[2]/'tools'),str(P/'scripts')]
from merge_head_material import read_glb,write_glb,append_accessor,accessor_array
from export_states import export_states


def arc_paths():
    raw=np.load(P/'work/ion_cannon_uv_triangles.npz')
    vertices=raw['positions'][raw['zones']==7].reshape(-1,3)
    vertices=np.unique(vertices[vertices[:,1]<vertices[:,1].min()+.3],axis=0)
    centre=np.array([.04891700744628907,-31.846464157104492,11.505241280794145])
    angles=np.arctan2(vertices[:,0]-centre[0],vertices[:,2]-centre[2])
    groups=np.round(angles/(2*np.pi/3)).astype(int)%3
    tips=np.array([vertices[groups==i].mean(0) for i in range(3)])
    rng=np.random.default_rng(3);paths=[]
    for i,start in enumerate(tips):
        end=tips[(i+1)%3]
        a=np.arctan2(start[0]-centre[0],start[2]-centre[2]);b=np.arctan2(end[0]-centre[0],end[2]-centre[2])
        if b<a:b+=2*np.pi
        r0=np.linalg.norm(start[[0,2]]-centre[[0,2]]);r1=np.linalg.norm(end[[0,2]]-centre[[0,2]])
        points=[]
        for t in np.linspace(0,1,8):
            radius=(1-t)*r0+t*r1-.35*np.sin(np.pi*t)
            phi=(1-t)*a+t*b;depth=(1-t)*start[1]+t*end[1]
            if 0<t<1:radius+=rng.uniform(-.2,.2);phi+=rng.uniform(-.07,.07);depth+=rng.uniform(-.25,.25)
            points.append([centre[0]+radius*np.sin(phi),depth,centre[2]+radius*np.cos(phi)])
        points=np.array(points);points=points[:,[0,2,1]];points[:,2]*=-1
        paths.append(points)
    return paths,tips


def tubes(paths,keep):
    vertices=[];normals=[];faces=[]
    for path in paths:
        points=path[keep];offset=len(vertices)
        for i,point in enumerate(points):
            tangent=points[min(i+1,len(points)-1)]-points[max(i-1,0)];tangent/=np.linalg.norm(tangent)
            u=np.cross(tangent,[0,0,1]);u/=np.linalg.norm(u);v=np.cross(tangent,u)
            for angle in np.arange(4)*np.pi/2:
                normal=u*np.cos(angle)+v*np.sin(angle)
                vertices.append(point+.10*normal);normals.append(normal)
        for i in range(len(points)-1):
            for k in range(4):
                a=offset+i*4+k;b=offset+i*4+(k+1)%4;c=b+4;d=a+4
                faces.extend([(a,b,c),(a,c,d)])
        faces.extend([(offset,offset+2,offset+1),(offset,offset+3,offset+2)])
        end=offset+(len(points)-1)*4
        faces.extend([(end,end+1,end+2),(end,end+2,end+3)])
    co=np.asarray(vertices,np.float32);tri=np.asarray(faces,np.uint16)
    volume=np.einsum('ij,ij->i',co[tri[:,0]],np.cross(co[tri[:,1]],co[tri[:,2]])).sum()/6
    assert volume>0,volume
    return co,np.asarray(normals,np.float32),tri


def main():
    result=json.loads((P/'work/lod_repair/work/ion_cannon/result.json').read_text())
    assert result['passed'],result
    doc,binary=read_glb(P/'work/lod_repair/export/ion_cannon.glb')
    material=next(i for i,m in enumerate(doc['materials']) if m['name']=='GC_muzzle')
    paths,tips=arc_paths();indices=[];counts=[]
    for level,keep in enumerate([list(range(8)),[0,1,3,5,7],[0,2,4,7],[0,3,7]]):
        co,normals,tri=tubes(paths,keep)
        a={name:append_accessor(doc,binary,array,{'componentType':5126,'type':'VEC3'},34962)
           for name,array in [('POSITION',co),('NORMAL',normals)]}
        index=append_accessor(doc,binary,tri.reshape(-1,1),{'componentType':5123,'type':'SCALAR'},34963)
        indices.append(len(doc['meshes']));counts.append(len(tri))
        doc['meshes'].append({'name':'GC_Arcs'+(f'_LOD{level}' if level else ''),
                              'primitives':[{'attributes':a,'indices':index,'material':material}]})
    doc['meshes'][indices[0]]['extras']={'openyamm_lods':indices[1:]}
    doc['scenes'][doc.get('scene',0)]['nodes'].append(len(doc['nodes']))
    doc['nodes'].append({'name':'GC_Arcs','mesh':indices[0]})
    # Merged shadow meshes also need POSITION bounds for glTF and the stage's decoration extent reader.
    for index in {p['attributes']['POSITION'] for mesh in doc['meshes'] for p in mesh['primitives']}:
        positions=accessor_array(doc,binary,index)
        assert len(positions)>0 and np.isfinite(positions).all(),index
        doc['accessors'][index].update(min=positions.min(axis=0).tolist(),max=positions.max(axis=0).tolist())
    ready=P/'work/ion_cannon_ready.glb';write_glb(ready,doc,binary)
    for path in export_states(ready,P/'export'):print(path.name)
    (P/'review/crown_arcs.json').write_text(json.dumps({'prong_tip_anchors_blender_metres':tips.tolist(),
        'arc_lod_triangles':counts,'radius_metres':.10,'visible_state':'c5',
        'basis':'Three static tip-to-tip arcs, as in the Crown stand-in; fitted to the retained three-prong geometry.'},indent=2)+'\n')


if __name__=='__main__':main()

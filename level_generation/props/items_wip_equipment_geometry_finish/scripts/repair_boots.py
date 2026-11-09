"""Keep the source feet, replace torn/capped shafts with continuous hollow leather shells."""
import json,math,sys
from pathlib import Path
import bmesh,bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from repair_geometry import activate,apply,closed_normals,voxel_union,finish
from repair_shapes import mesh,join


def shell(cx,cy,rx,ry,z0,zt,thickness,band=False):
    n=32;levels=2 if band else 4
    verts=[];faces=[]
    for inner in [False,True]:
        for j in range(levels):
            t=j/(levels-1)
            radius=1 if band else .77+.23*t+.025*math.sin(t*math.pi)
            for i in range(n):
                a=i*math.tau/n
                # A soft irregular flared cuff, with a continuous rim and deep lining.
                top=zt if band else zt+.035*math.cos(a)+.035*math.sin(2*a+.6)
                z=z0+(top-z0)*t
                dx=rx*radius-(thickness if inner else 0)
                dy=ry*radius-(thickness if inner else 0)
                verts.append((cx+dx*math.cos(a),cy+dy*math.sin(a),z))
    side=levels*n
    for j in range(levels-1):
        for i in range(n):
            k=j*n+i;l=j*n+(i+1)%n
            faces += [(k,l,l+n,k+n),(side+k+n,side+l+n,side+l,side+k)]
    for i in range(n):
        a=i;b=(i+1)%n;c=(levels-1)*n+i;d=(levels-1)*n+(i+1)%n
        faces += [(a,side+a,side+b,b),(c,d,side+d,side+c)]
    return mesh('leather_band' if band else 'continuous_open_shaft',verts,faces)


def bar(location,scale):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Soft buckle edge','BEVEL');bevel.width=.004;bevel.segments=1
    apply(o,bevel)
    return o


def main():
    audit=json.loads((P/'receipts/scene_audit.json').read_text())
    for icon in sys.argv[sys.argv.index('--')+1:]:
        name='equipment_'+icon
        bpy.ops.wm.open_mainfile(filepath=str(P/'references/scenes'/f'{name}.blend'))
        obj=bpy.data.objects[name]
        for other in list(bpy.context.scene.objects):
            if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
            plane_co=Vector((0,0,.335)),plane_no=Vector((0,0,1)),clear_outer=True,clear_inner=False)
        if icon=='6boots5':
            seen=set()
            for v in bm.verts:
                if v in seen:continue
                stack=[v];seen.add(v);group=[]
                while stack:
                    a=stack.pop();group.append(a)
                    for edge in a.link_edges:
                        other=edge.other_vert(a)
                        if other not in seen:seen.add(other);stack.append(other)
                shift=.045 if sum(v.co.x for v in group)>0 else -.045
                for v in group:v.co.x+=shift
        bm.to_mesh(obj.data);bm.free();voxel_union(obj,.008)
        obj.data.calc_loop_triangles()
        mod=obj.modifiers.new('Foot silhouette budget','DECIMATE');mod.ratio=min(1,1150/len(obj.data.loop_triangles));apply(obj,mod)
        parts=[obj]
        for upper in audit[icon]['upper_boots']:
            low,high=upper['bounds'];cx=(low[0]+high[0])/2;cy=(low[1]+high[1])/2
            rx=(high[0]-low[0])*.45;ry=(high[1]-low[1])*.44
            if icon=='6boots5':cx+=.045 if cx>0 else -.045
            parts.append(shell(cx,cy,rx,ry,.28,high[2]-.06,.018))
            parts.append(shell(cx,cy,rx*.85+.006,ry*.85+.006,.34,.405,.012,True))
            # A rectangular buckle really has an opening; painting only supplies its finish.
            y=cy-ry*.86-.012;z=.373;w=.105;h=.071
            for location,scale in [((cx-w/2,y,z),(.014,.021,h)),((cx+w/2,y,z),(.014,.021,h)),
                ((cx,y,z-h/2),(w,.021,.014)),((cx,y,z+h/2),(w,.021,.014)),((cx,y-.007,z),(.012,.018,h))]:
                parts.append(bar(location,scale))
            if icon=='6boots5':
                # Horn bird plaque follows the cuff rather than filling its opening.
                points=[(-.12,.025),(-.075,.08),(-.018,.055),(0,.10),(.018,.055),(.075,.08),(.12,.025),(.05,.035),(0,-.045),(-.05,.035)]
                verts=[(cx+x,y+dy,high[2]-.20+z) for dy in [0,-.014] for x,z in points]
                n=len(points);faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
                faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
                parts.append(mesh('raised_horn_bird',verts,faces))
        obj=join(parts)
        # Closed overlapping parts keep the narrow leather lining intact; union would fill the cavities again.
        finish(obj,name,3400)


if __name__=='__main__':main()

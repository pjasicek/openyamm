"""Record the inspected icon's construction; outlines constrain blades, never surface colour."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
# guard row, blade scan end, guard construction, blade/metal/grip, grip centre x/width.
SPECS = {
 '2hsword1': (.66,.60,'claymore','steel','gold','brown',.50),
 '2hsword2': (.52,.48,'double_fork','purple','darksteel','black',.50),
 '2hsword3': (.74,.57,'scroll','steel','gold','gold',.50),
 '62hsword5': (.74,.57,'scroll','steel','gold','gold',.50),
 '6brsword4': (.78,.73,'shell','steel','gold','red',.55),
 '6lsword7': (.77,.73,'skull_arch','fire','gold','gold',.50),
 '7item001': (.78,.73,'plain','steel','iron','brown',.50),
 '7item002': (.79,.74,'d_right','gold','gold','brown',.45),
 '7item003': (.76,.71,'disc','bronze','gold','black',.50),
 '7item004': (.80,.75,'skulls','darksteel','silver','black',.50),
 '7item005': (.76,.60,'angular','blue','darksteel','red',.50),
 '7item006': (.79,.64,'plain','darksteel','iron','brown',.50),
 '7item007': (.73,.67,'v_guard','purple','iron','red',.50),
 '7item008': (.73,.65,'antlers','purple','gold','red',.50),
 '7item009': (.80,.75,'d_left','steel','gold','gold',.54),
 '7item010': (.74,.69,'scroll','steel','iron','black',.50),
 '7item011': (.73,.64,'horn_bow','steel','gold','brown',.72),
 '7item012': (.71,.65,'d_left','steel','iron','black',.67),
 '7item013': (.76,.70,'d_left','fire','gold','red',.64),
 '7item014': (.73,.64,'scroll_bow','steel','gold','brown',.66),
 '7item217': (.75,.68,'crescent','steel','gold','black',.50),
 '7item218': (.75,.61,'feather','blue','gold','gold',.50),
 '7item219': (.74,.68,'scroll','steel','gold','red',.50),
 '7item220': (.74,.68,'d_left','steel','gold','brown',.67),
 '7item242': (.73,.65,'antlers','purple','gold','red',.50),
 '7item249': (.73,.67,'v_guard','purple','iron','brown',.50),
 '7item286': (.76,.70,'d_left','fire','gold','red',.64),
 '7item296': (.76,.60,'angular','blue','darksteel','red',.50),
 '7item298': (.76,.70,'d_left','fire','gold','red',.64),
 'brsword1': (.79,.74,'d_left','blue','gold','black',.53),
 'brsword2': (.78,.71,'scroll','steel','silver','black',.50),
 'brsword3': (.78,.73,'shell','steel','gold','red',.55),
 'cutlass1': (.75,.70,'d_left','steel','silver','ivory',.65),
 'cutlass2': (.74,.65,'scroll_bow','steel','gold','brown',.65),
 'cutlass3': (.74,.68,'crescent','pink','gold','red',.50),
 'item001': (.75,.70,'scroll','iron','bronze','brown',.50),
 'item002': (.77,.70,'ribbed','greensteel','bronze','brown',.50),
 'item003': (.79,.69,'twisted_horns','steel','silver','black',.50),
 'item004': (.77,.67,'crown','steel','gold','black',.50),
 'item005': (.76,.68,'angel','steel','gold','red',.50),
 'item006': (.78,.64,'plain','rust','bronze','brown',.50),
 'item007': (.73,.56,'thorns','darksteel','darksteel','black',.50),
 'item008': (.79,.62,'bat','steel','iron','red',.50),
 'item009': (.78,.62,'dragon','steel','gold','gold',.50),
 'item010': (.75,.69,'bone','steel','silver','black',.50),
 'item011': (.75,.70,'scroll','rust','bronze','brown',.50),
 'item012': (.77,.70,'horns','greensteel','gold','ivory',.50),
 'item013': (.75,.70,'plain','greensteel','gold','gold',.50),
 'item014': (.74,.69,'cup','steel','gold','gold',.50),
 'item015': (.76,.70,'scroll','steel','gold','gold',.50),
 'item016': (.76,.70,'d_left','rust','bronze','brown',.70),
 'item017': (.75,.69,'d_left','steel','gold','black',.68),
 'item018': (.77,.64,'twisted_horns','steel','gold','brown',.50),
 'item019': (.76,.68,'dragon_small','steel','gold','brown',.55),
 'item020': (.75,.68,'skull_scroll','steel','gold','brown',.52),
 'item234': (.73,.67,'serpents','gold','gold','silver',.50),
 'item235': (.73,.66,'artifact_collar','ivory','gold','brown',.51),
 'item236': (.71,.66,'candles','steel','gold','red',.50),
 'item237': (.75,.67,'ornate_bow','steel','gold','ivory',.67),
 'item296': (.73,.66,'artifact_collar','bronze','gold','brown',.51),
 'item333': (.77,.67,'crown','steel','gold','black',.50),
 'item334': (.75,.69,'bone','steel','silver','black',.50),
 'item342': (.75,.69,'bone','steel','silver','black',.50),
 'lsword1': (.815,.77,'plain','blue','gold','brown',.50),
 'lsword2': (.80,.75,'v_guard','blue','gold','brown',.50),
 'lsword3': (.80,.60,'angular','purple','darksteel','brown',.50),
 'lsword4': (.80,.74,'open_guard','steel','gold','red',.50),
 'lsword5': (.77,.73,'skull_arch','fire','gold','gold',.50),
}


def simplify(points, tolerance=1.1):
    if len(points) < 3:
        return points
    a, b = np.array(points[0]), np.array(points[-1])
    axis = b-a
    distance = np.abs(axis[0]*(np.array(points)[:,1]-a[1])-axis[1]*(np.array(points)[:,0]-a[0]))/max(np.linalg.norm(axis),1e-8)
    index = int(distance.argmax())
    if distance[index] <= tolerance:
        return [points[0],points[-1]]
    return simplify(points[:index+1],tolerance)[:-1]+simplify(points[index:],tolerance)


def main():
    ownership=json.loads((PROJECT/'ownership.json').read_text())
    assert set(SPECS)=={r['icon'] for r in ownership}
    designs={}
    for row in ownership:
        icon=row['icon'];g,scan,guard,blade,metal,grip,cx=SPECS[icon]
        image=Image.open(ROOT/row['icon_reference']).convert('RGBA')
        alpha=np.array(image)[:,:,3]>128
        height,width=alpha.shape
        upper=next(y for y in range(height) if alpha[y].any())
        fixed_ends={'2hsword2':.43,'7item008':.60,'7item242':.60,'7item005':.56,'7item296':.56,
                    'item003':.63,'item018':.60,'7item011':.61,'7item014':.61,'cutlass2':.61,
                    'item014':.64,'item020':.63,'lsword3':.57}
        scan=fixed_ends.get(icon,max(scan,g-.04) if icon not in ('item006','7item006') else scan)
        end=round(scan*height)
        sides=[[],[]]
        previous_x=float(np.where(alpha[upper])[0].mean())
        for y in range(upper+1,end+1):
            xs=np.where(alpha[y])[0]
            if len(xs):
                runs=np.split(xs,np.where(np.diff(xs)>2)[0]+1)
                # Quillon tips above the guard are independent runs, never part of the blade outline.
                run=min(runs,key=lambda r:abs(float(r.mean())-previous_x))
                if icon in ('item010','item334','item342') and y<height*.10:
                    run=xs
                previous_x=float(run.mean())
                sides[0].append((float(run[0]),float(y)))
                sides[1].append((float(run[-1]),float(y)))
        simple=[simplify(side) for side in sides]
        # Preserve curvature/notches and split long spans into approximately equilateral blade strips.
        rows=sorted(set([int(y) for side in simple for x,y in side]+list(range(upper+1,end+1,5))+[end]))
        contour=[]
        for y in rows:
            left=float(np.interp(y,*np.array(simple[0]).T[::-1]))
            right=float(np.interp(y,*np.array(simple[1]).T[::-1]))
            contour.append([y,left,max(left+.5,right)])
        # Below the clean blade outline use the independent ricasso, not the guard's alpha.
        last=contour[-1]
        base=round(g*height)
        if end < base:
            half=(last[2]-last[1])/2
            contour.append([base,cx*width-half,cx*width+half])
        if icon in ('7item008','7item242','7item005','7item296','item003'):
            assert all(right-left<width*.5 for y,left,right in contour if y>height*.55),icon
        variants={
            '62hsword5':'2hsword3','6brsword4':'brsword3','6lsword7':'lsword5',
            '7item242':'7item008','7item249':'7item007','7item286':'7item013',
            '7item296':'7item005','7item298':'7item013','item333':'item004',
            'item334':'item010','item342':'item010'}
        designs['swords_'+icon]={
            'title':row['items'][0]['name'],'icons':[icon],'master_icon':icon,
            'route':'blender_components_with_painted_pbr','design_group':variants.get(icon,icon),
            'guard':guard,'blade_material':blade,'metal_material':metal,'grip_material':grip,
            'size_px':[width,height],'guard_row':base,'scan_row':end,'grip_x':cx*width,
            'blade_outline_px':contour,'tip_row':upper,
            'length':row['binding']['length'],'source_icon':row['icon_reference'],
            'status':'pending','remaining_defects':['Awaiting mesh and visual checks'],
        }
        if icon in ('item010','item334','item342'):
            branches=[[],[]]
            for y in range(upper+1,43,2):
                xs=np.where(alpha[y])[0]
                runs=np.split(xs,np.where(np.diff(xs)>2)[0]+1)
                runs=[r for r in runs if len(r)]
                if len(runs)==1:
                    mid=(xs[0]+xs[-1])/2
                    runs=[xs[xs<=mid],xs[xs>=mid]]
                for k in range(2):
                    run=runs[k];branches[k].append([y,float(run[0]),max(float(run[0])+.5,float(run[-1]))])
            designs['swords_'+icon]['fork_branches_px']=branches
            designs['swords_'+icon]['blade_outline_px']=[r for r in contour if r[0]>=39]
    (PROJECT/'designs.json').write_text(json.dumps(designs,indent=2)+'\n')
    print('Recorded',len(designs),'individually inspected sword designs')


if __name__=='__main__':main()

"""Use the existing LOD pipeline's xatlas method without changing geometry."""
import json
from pathlib import Path
import numpy as np
import xatlas
P=Path(__file__).resolve().parents[1]
xyz=np.load(P/'work/uv_source.npy').astype(np.float32)
points,indices=np.unique(xyz.reshape(-1,3),axis=0,return_inverse=True)
indices=indices.reshape(-1,3).astype(np.uint32)
# Four triangles on overlapping housing relief fold within one projected chart; isolate their UV charts.
split_faces=[3033,3183,3319,3684]
for face in split_faces:
    indices[face]=np.arange(len(points),len(points)+3)
    points=np.concatenate([points,xyz[face]])
atlas=xatlas.Atlas();atlas.add_mesh(points,indices)
pack=xatlas.PackOptions();pack.resolution=2048;pack.padding=8;pack.bilinear=True;pack.rotate_charts=True
atlas.generate(pack_options=pack)
vertices,faces,uv=atlas[0]
assert np.array_equal(points[vertices[faces]],xyz), 'xatlas changed triangle order'
corner=uv[faces]*(1-16/2048)+8/2048
assert np.isfinite(corner).all() and corner.min()>=0 and corner.max()<=1
coverage=np.zeros((2048,2048),np.uint16)
for tri in corner.astype(np.float64)*2048:
    lo=np.maximum(np.floor(tri.min(0)).astype(int),0);hi=np.minimum(np.ceil(tri.max(0)).astype(int),2048)
    yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];pts=np.stack([xx+.5,yy+.5],axis=-1)-tri[0]
    b=tri[1]-tri[0];c=tri[2]-tri[0];den=b[0]*c[1]-b[1]*c[0]
    u=(pts[:,:,0]*c[1]-pts[:,:,1]*c[0])/den;v=(b[0]*pts[:,:,1]-b[1]*pts[:,:,0])/den
    inside=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6)
    coverage[lo[1]:hi[1],lo[0]:hi[0]]+=inside.astype(np.uint16)
overlap=int((coverage>1).sum());assert overlap==0,overlap
(P/'review/geometry/uv_overlap.json').write_text(json.dumps({'resolution':2048,'sample':'strict triangle interiors at texel centres','overlapping_texels':overlap,'covered_texels':int((coverage>0).sum()),'coverage_fraction':float((coverage>0).mean())},indent=2)+'\n')
np.savez(P/'work/packed_uv.npz',xyz=xyz,uv=corner)
report={'method':'xatlas','separate_uv_faces':split_faces,'padding_at_pack_resolution':8,'atlas_width':atlas.width,'atlas_height':atlas.height,'utilization':atlas.utilization,'charts':atlas.chart_count,'border_texels_2k':8,'minimum_chart_padding_texels_2k':8*2048/max(atlas.width,atlas.height)*(1-16/2048)}
(P/'review/geometry/uv_pack.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)

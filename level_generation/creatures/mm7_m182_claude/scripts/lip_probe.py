import bpy,numpy as np,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
o=bpy.data.objects['Body'];me=o.data;co=np.array([v.co[:] for v in me.vertices])
jaw=np.array([v.value for v in me.attributes['jaw'].data],bool);head=np.array([v.value for v in me.attributes['head'].data],bool)
cross=[(a,b) for a,b in (e.vertices[:] for e in me.edges) if jaw[a]!=jaw[b] and head[a] and head[b]]
pts=np.array([(co[a]+co[b])/2 for a,b in cross]); print('crossing edges',len(cross))
for yy in np.arange(-.40,-.33,.005):
  m=np.abs(pts[:,1]-yy)<.0025; print(round(yy,3), m.sum(), np.round(np.sort(pts[m][:,0]),3)[:12], np.round(pts[m][:,2].mean() if m.any() else 0,3))

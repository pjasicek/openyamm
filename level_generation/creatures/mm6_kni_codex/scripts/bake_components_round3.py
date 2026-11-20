def components(obj):
 parent=list(range(len(obj.data.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):parent[root(b)]=root(a)
 coords={}
 for v in obj.data.vertices:
  key=tuple(round(x,6)for x in v.co)
  if key in coords:join(v.index,coords[key])
  else:coords[key]=v.index
 for e in obj.data.edges:join(*e.vertices)
 return [root(i)for i in range(len(parent))]

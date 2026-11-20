"""Find the shoulder creases on this revision's joined stone surface."""
import sys,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_flow,breadth_first_order
p=sys.argv[1];a=np.load(p);c=a['centres'];edges=a['adj'];capacity=a['cost'];n=len(c);rows=list(edges[:,0])+list(edges[:,1]);cols=list(edges[:,1])+list(edges[:,0]);data=list(capacity)*2
for i,(x,y,z) in enumerate(c):
 shoulder=abs(x)>.11 and y<.055 and .745<z<.825
 arm=shoulder or abs(x)>.225 or (abs(x)>.185 and z<.74) or (abs(x)>.17 and .72<z<.825)
 torso=(abs(x)<.13 and not shoulder) or z>.85
 if arm and not torso:rows.append(n);cols.append(i);data.append(100000000)
 if torso:rows.append(i);cols.append(n+1);data.append(100000000)
g=coo_matrix((np.array(data,dtype=np.int64),(rows,cols)),shape=(n+2,n+2)).tocsr();result=maximum_flow(g,n,n+1);residual=g-result.flow;residual.data=(residual.data>0).astype(np.int64);residual.eliminate_zeros();reachable=breadth_first_order(residual,n,directed=True,return_predecessors=False);labels=np.zeros(n,dtype=bool);labels[reachable[reachable<n]]=True;np.save(p+'.labels.npy',labels)
print('SHOULDER_CUT',int(labels.sum()),'arm faces',int(result.flow_value),flush=True)

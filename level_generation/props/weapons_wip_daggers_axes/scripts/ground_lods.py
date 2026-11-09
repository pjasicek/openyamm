"""Ground each exported static LOD after Blender's evaluated decimation and update its accessor bounds."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from link_static_model_lods import read_glb,write_glb

def ground(path):
    doc,binary=read_glb(path)
    for mesh in doc['meshes']:
        arrays=[];seen=set()
        for prim in mesh['primitives']:
            index=prim['attributes']['POSITION']
            if index in seen:continue
            seen.add(index);acc=doc['accessors'][index];view=doc['bufferViews'][acc['bufferView']]
            assert acc['componentType']==5126 and acc['type']=='VEC3' and view.get('byteStride',12)==12
            offset=view.get('byteOffset',0)+acc.get('byteOffset',0)
            arr=np.ndarray((acc['count'],3),dtype='<f4',buffer=binary,offset=offset);arrays.append((arr,acc))
        positions=np.concatenate([a for a,_ in arrays]);lo=positions.min(0);hi=positions.max(0)
        shift=np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2],dtype='<f4')
        for arr,acc in arrays:
            arr-=shift;acc['min']=arr.min(0).tolist();acc['max']=arr.max(0).tolist()
        positions=np.concatenate([a for a,_ in arrays]);lo=positions.min(0);hi=positions.max(0)
        assert abs(lo[1])<1e-6 and abs(lo[0]+hi[0])<1e-6 and abs(lo[2]+hi[2])<1e-6
    write_glb(path,doc,binary)

if __name__=='__main__':
    for file in sys.argv[1:]:ground(Path(file))

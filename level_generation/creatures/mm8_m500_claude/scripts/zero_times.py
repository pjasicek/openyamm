"""Remove Blender's one-frame offset without resampling fractional animation keys."""
from pathlib import Path
import sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tools'))
from build_actor_lods import read_glb,write_glb

def zero_times(path):
    doc,binary=read_glb(path);binary=bytearray(binary);offsets={}
    expected={'Standing':3.,'Walk':1.125,'Running':.75,'Fidget':.75,'Attack':1.375,'Cast':1.375,'Hit':.75,'Death':.625,'Dead':1.}
    assert {a['name'] for a in doc['animations']}==set(expected)
    for animation in doc['animations']:
        indices={s['input'] for s in animation['samplers']}
        start=min(doc['accessors'][i]['min'][0] for i in indices)
        end=max(doc['accessors'][i]['max'][0] for i in indices)
        assert abs(end-start-expected[animation['name']])<1e-5,(animation['name'],start,end)
        for index in indices:
            assert index not in offsets or abs(offsets[index]-start)<1e-6
            offsets[index]=start
    for index,start in offsets.items():
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        assert a['componentType']==5126 and a['type']=='SCALAR' and v.get('byteStride',4)==4
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        times=[t[0]-start for t in struct.iter_unpack('<f',binary[offset:offset+4*a['count']])]
        assert min(times)>-1e-6
        times=[max(0.,t) for t in times];binary[offset:offset+4*a['count']]=struct.pack('<'+'f'*len(times),*times)
        a['min']=[min(times)];a['max']=[max(times)]
    write_glb(path,doc,binary)
    print('ZERO_TIME',path,len(offsets),'time accessors')

if __name__=='__main__':
    for path in sys.argv[1:]:zero_times(Path(path))

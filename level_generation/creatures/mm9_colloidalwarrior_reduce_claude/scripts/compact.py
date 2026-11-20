"""Drop unreferenced accessors and buffer views (left behind by fix_normals.py and the LOD build). Usage: compact.py <glb> (in place)"""
import sys
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), '../../claude_shared'))
import region_variants as RV
doc, b = RV.read_glb(sys.argv[1]); n0 = len(b); doc, b = RV._compact(doc, bytes(b)); RV.write_glb(sys.argv[1], doc, b)
print('COMPACT', n0, '->', len(b))

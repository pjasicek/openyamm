import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import pbr_round3 as p
orig=p.setup
def setup(*args,**kw):
 s,scale=orig(*args,**kw);body=args[0];mat=body.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');em=n.new('ShaderNodeEmission');l.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color']);l.new(em.outputs[0],n.get('Material Output').inputs['Surface']);s.cycles.samples=1;s.cycles.use_denoising=False
 return s,scale
p.setup=setup
for v in ['high','low']:p.render(v,'a','emit_'+v,views=[0])

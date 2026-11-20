"""Match the native self-lit runtime preview while retaining all authored PBR texture nodes."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_gst.blend'))
for material in bpy.data.objects['Body'].data.materials:
 nt=material.node_tree;base=next(n for n in nt.nodes if n.type=='TEX_IMAGE' and 'basecolor' in n.image.name);out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');em=nt.nodes.get('Native Lit') or nt.nodes.new('ShaderNodeEmission');em.name='Native Lit';em.inputs['Strength'].default_value=1;nt.links.new(base.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs['Emission'],out.inputs['Surface'])
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_gst.blend'))

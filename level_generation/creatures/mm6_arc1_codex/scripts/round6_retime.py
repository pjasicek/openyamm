"""Review 6: change animation clocks, preserving the accepted mesh, maps and poses."""
import sys,json,copy
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
B=P/'review/round6/baseline';d,b=read_glb(B/'export/mm6_arc1.glb');clocks={};rows={};changes=[]
for a in d['animations']:
 name=a['name'];old=max(float(accessor_array(d,b,s['input'])[-1,0])for s in a['samplers'])
 for s in a['samplers']:
  if name in ('Attack','Cast'):
   ai=s['input']
   if ai not in clocks:
    values=(accessor_array(d,b,ai)/1.5).astype(np.float32)
    ni=append_accessor(d,b,values,d['accessors'][ai],None);d['accessors'][ni]['min']=[float(values.min())];d['accessors'][ni]['max']=[float(values.max())];clocks[ai]=ni
   s['input']=clocks[ai]
  if name in ('Standing','Fidget','Walking'):
   ai=s['output'];values=accessor_array(d,b,ai).copy()
   assert s.get('interpolation','LINEAR')!='CUBICSPLINE'
   if not np.array_equal(values[0],values[-1]):
    changes.append({'clip':name,'output':ai,'max_component_delta_before':float(abs(values[0]-values[-1]).max())})
    values[-1]=values[0];s['output']=append_accessor(d,b,values,d['accessors'][ai],None)
 rows[name]={'before_s':old,'after_s':max(float(accessor_array(d,b,s['input'])[-1,0])for s in a['samplers'])}
d,b=compact(d,b);write_glb(P/'export/mm6_arc1.glb',d,b)
text=(B/'integration/actors.yml').read_text();assert text.count('impact: 1.2')==9
(P/'integration/actors.yml').write_text(text.replace('impact: 1.2','impact: 0.8'))
(P/'review/round6/retiming.json').write_text(json.dumps({'speed':1.5,'release_before_s':1.2,'release_after_s':.8,'durations':rows,'loop_endpoint_corrections':changes},indent=2));print(rows);print('Endpoint channels corrected:',len(changes))

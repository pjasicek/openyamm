from pathlib import Path
import os,runpy
p=Path(__file__).resolve().parent
os.environ['M480_MOTION_FILE']='ready_final.blend'
for n in ['measure_runtime.py','motion_quality.py','cloth_probe.py','contacts.py']:
 runpy.run_path(str(p/n),run_name='__main__')

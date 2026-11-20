from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for name,args in [("finish_hand_weights.py",[]),("finish_hands.py",[]),("hand_review.py",[]),("g5_hand_stretch.py",[str(p/"work/hands.blend"),"Standing","Walking","Running","Attack","Hit","Fidget","Death","Dead"]),("export_preview.py",[]),("export_uploads.py",[])]:
 path=p/"scripts"/name;sys.argv=[str(path),"--",*args];runpy.run_path(str(path),run_name="__main__")

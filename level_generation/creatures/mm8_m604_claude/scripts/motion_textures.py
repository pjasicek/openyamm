from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ["motion_and_sword.py","apply_textures.py"]:runpy.run_path(str(p/n),run_name="__main__")

from pathlib import Path
import runpy,subprocess
p=Path(__file__).resolve().parents[1]
subprocess.run(["python3",str(p/"scripts/compose_textures.py")],check=True)
runpy.run_path(str(p/"scripts/export_runtime.py"),run_name="__main__")
subprocess.run(["python3",str(p/"scripts/build_viewer.py")],check=True)
runpy.run_path(str(p/"scripts/build_lods.py"),run_name="__main__")

from pathlib import Path
import runpy,subprocess
p=Path(__file__).resolve().parents[1]
for name in ["export_runtime","head_look"]:runpy.run_path(str(p/"scripts"/(name+".py")),run_name="__main__")
subprocess.run(["python3",str(p/"scripts/build_viewer.py")],check=True)
runpy.run_path(str(p/"scripts/measure_export.py"),run_name="__main__")
runpy.run_path(str(p/"scripts/build_lods.py"),run_name="__main__")

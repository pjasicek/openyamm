from pathlib import Path
import runpy,subprocess
p=Path(__file__).resolve().parents[1]
for name in ["export_runtime.py","build_viewer.py","export_audit.py","build_lods.py","finish_runtime.py"]:
 s=p/"scripts"/name
 if name in ["build_viewer.py","finish_runtime.py"]:subprocess.run(["python3",str(s)],check=True)
 else:runpy.run_path(str(s),run_name="__main__")

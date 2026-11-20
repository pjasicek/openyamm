from pathlib import Path
import subprocess
subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('reduction_colours_r3.py'))],check=True)

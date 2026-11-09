from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
# The full replay recreates the six clips and their weights with the corrected death source.
sys.argv=[str(p/'scripts/g4_animate.py')]
runpy.run_path(sys.argv[0],run_name='__main__')

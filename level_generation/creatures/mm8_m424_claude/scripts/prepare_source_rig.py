"""Extract the source frames and selected civilian motion stress poses."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
lib = p.parents[2] / 'anim_library/humanoid_set'
sys.argv = ['source_rest.py', '--', str(lib / 'Relax.glb')]
runpy.run_path(str(p / 'scripts/source_rest.py'), run_name='__main__')
sys.argv = ['rom_extract.py', '--',
            'Standing=' + str(lib / 'Relax.glb') + ':RelaxIdle',
            'Walking=' + str(lib / 'Relax.glb') + ':RelaxWalkForward',
            'Hit=' + str(lib / 'Unarmed.glb') + ':UnarmedGetHitF1',
            'Death=' + str(lib / 'Unarmed.glb') + ':UnarmedDeath1']
runpy.run_path(str(p / 'scripts/rom_extract.py'), run_name='__main__')

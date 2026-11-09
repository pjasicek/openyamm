"""Sequential authoring queue under the creature lease."""
from pathlib import Path
import runpy
import sys
S = Path(__file__).resolve().parent
for script, args in [('polish_lancer.py', []), ('check_forge.py', ['Attack'])]:
    sys.argv = [script, '--', *args]
    runpy.run_path(str(S/script), run_name='__main__')

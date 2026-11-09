import importlib
import sys
from pathlib import Path
stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation')
if str(stage) not in sys.path:
    sys.path.insert(0, str(stage))
import motion
importlib.reload(motion)
motion.build()

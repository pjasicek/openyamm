from pathlib import Path
import importlib.util
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fly_motion',P/'animate.py')
motion=importlib.util.module_from_spec(spec);spec.loader.exec_module(motion)
motion.main(P/'work/final_uv_master.blend',P/'work/final_uv_master.blend',pilot=False)

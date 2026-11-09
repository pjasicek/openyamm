"""Map authored library phases onto the final, locally eased clip timeline."""
import json
from pathlib import Path
TIMES=json.loads((Path(__file__).resolve().parents[1]/'work/action_timing.json').read_text())
def phase(clip,seconds):
 result=seconds
 for center,width,delay in TIMES[clip]['bumps']:
  u=max(0,min(1,(seconds-center+width)/(2*width)));z=max(0,min(1,(-center+width)/(2*width)));result+=delay*(u*u*(3-2*u)-z*z*(3-2*z))
 return result

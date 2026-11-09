import sys, numpy as np
sys.path.insert(0,'scripts'); import rig_bones
np.savez(sys.argv[1].replace('.npz','_bones.npz'), table=np.array(rig_bones.table(), dtype=object))

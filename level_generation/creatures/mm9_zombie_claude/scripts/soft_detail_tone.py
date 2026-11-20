import numpy as np
def tone(a):
    a = np.clip(a, 0, 1) ** 1.18 * 0.86
    g = a.mean(-1, keepdims=True)
    return g + (a - g) * 0.9

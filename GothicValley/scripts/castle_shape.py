# Castle crag outline shared by the terrain and the castle greybox (signed distance to the rim, metres, < 0 = on top).
import numpy as np


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def rim_sd(X, Y):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    ang = np.arctan2(Y - 308, X - 715)
    lob = 1 + 0.035 * np.sin(3 * ang + 0.6) + 0.025 * np.sin(5 * ang + 2.1)
    q = (np.abs((X - 715) / (110 * lob)) ** 3 + np.abs((Y - 308) / (115 * lob)) ** 3) ** (1 / 3)
    sd1 = (q - 1) * 110                                                  # lobed superellipse
    # along the palace the rim is the outer face of the south facade (x 618.2): the facade continues the cliff
    w = _ss(222, 246, Y) * _ss(424, 400, Y)
    sd1 = np.maximum(sd1, (618.2 - X) - 40 * (1 - w))
    bx, by = np.abs(X - 656.1) - (37.9 - 1.0), np.abs(Y - 323.0) - (77.0 - 1.0)
    sd2 = np.hypot(np.maximum(bx, 0), np.maximum(by, 0)) + np.minimum(np.maximum(bx, by), 0) - 1.0   # palace block
    return np.minimum(sd1, sd2)

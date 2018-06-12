import numpy as np

PP_WEIGHTS = [8.67, .6, .6, 14.9, .6, 5.88, .6, 5.07, 9.85, .6, .6, 26.5]
SPOTIFY_WEIGHTS = [.6, 1.45, .6, 4.15, 1.47, 1.37, .6, 5.5, .6, .6, .6, .6, 2.65]


def get(etype, target):
    if etype == 'artist':
        return np.ones(17)
    else:
        if target == 'pp':
            return PP_WEIGHTS
        else:
            return SPOTIFY_WEIGHTS

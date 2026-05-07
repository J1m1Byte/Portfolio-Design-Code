import numpy as np


def total_return(r):
    return (1 + r).prod() - 1


def ann_return(r):
    return 100 * (np.power((1 + r).prod(), 12 / len(r)) - 1)


def ann_vol(r):
    vol_m = r.std()
    return vol_m * np.sqrt(12)


def ann_sharpe(r, rf):
    excess = r - rf
    vol_m = r.std()
    return (excess.mean() / vol_m) * np.sqrt(12)


def ann_active_return(r, bmk):
    active_m = r - bmk
    return 1200 * active_m.mean()


def ann_tracking_error(r, bmk):
    active_m = r - bmk
    te_m = active_m.std()
    return te_m * np.sqrt(12) * 100


def information_ratio(r, bmk):
    active_m = r - bmk
    active_ann = 12 * active_m.mean()
    te_ann = ann_tracking_error(r, bmk)
    return active_ann / te_ann

import math


def T(x, y):
    return 0.0


d = k = m = n = 0
smy = smY = smY2 = Y = h = 0.0


def init_bm(m0: int, mb: int):
    global d, k, m, n, smy, smY, smY2
    # Set deletion amount & batch size
    d = m0
    m = mb
    smy = smY = smY2 = 0.0
    k = n = 0


def obs(y: float) -> int:
    global d, k, n, smy, smY, smY2, Y, h
    r = 0
    if d:
        d -= 1
        return r

    smy += y
    n += 1
    if n == m:  # Batch complete: update sums & counts
        smy /= n
        smY += smy
        smY2 += smy * smy
        k += 1
        smy = 0.0
        n = 0
        if k >= 10:  # Compute grand mean & half width
            Y = smY / k
            var = (smY2 - k * Y * Y) / (k - 1)
            h = T(0.025, k - 1) * math.sqrt(var / k)
            if h / Y <= 0.1:
                r = 1
    return r


def civals(mean: list, hw: list, nb: list):
    # Return batch means analysis results
    mean[0] = Y  # NOTE: not sure if list works this way _ these args should be references
    hw[0] = h
    nb[0] = k

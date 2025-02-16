import math


def z(p: float) -> float:
    """-------------------- COMPUTE pth QUANTILE OF THE NORMAL DISTRIBUTION --------------------"""
    q = p - 0.5 if p > 0.5 else 1 - p
    z1 = math.sqrt(-2.0 * math.log(q))
    n = (0.010328 * z1 + 0.802853) * z1 + 2.515517
    d = ((0.001308 * z1 + 0.189269) * z1 + 1.43278) * z1 + 1
    z1 = n / d
    return z1 if p > 0.5 else -z1


def t(p: float, ndf: int) -> float:
    """-------------------- COMPUTE pth QUANTILE OF THE t DISTRIBUTION --------------------"""
    z1 = Z(p)
    z2 = z1 * z1
    h = [
        0.25 * z2 * (z2 + 1.0),
        0.010416667 * z1 * ((5.0 * z2 + 16.0) * z2 + 3.0),
        0.002604167 * z1 * (((3.0 * z2 + 19.0) * z2 + 17.0) * z2 - 15.0),
        z1 * (((179.0 * z2 + 776.0) * z2 + 1482.0) * z2 - 1920.0) * z2 - 945.0,
    ]
    x = 0.0
    for i in range(3, -1, -1):
        x = (x + h[i]) / float(ndf)
    z1 += x
    return z1 if p > 0.5 else -z1

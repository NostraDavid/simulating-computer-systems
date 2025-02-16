import math


def delay(t: float, r: float, Tf: float, dis: int) -> float:
    """Compute Lam's Mean Frame Delay"""
    Tf2 = 0.0
    B = 0.0
    e = math.exp(1.0)

    if dis == 1:
        Tf2 = Tf * Tf
        B = math.exp(-r * Tf)
    else:
        Tf2 = 2.0 * Tf * Tf
        B = 1.0 / (1.0 + r * Tf)

    f1 = Tf + t * (4.0 * e + 1.0) / 2.0
    f2 = Tf2 + t * Tf * (4.0 * e + 2.0) + t * t * (5.0 + 4.0 * e * (2.0 * e - 1.0))
    f2 *= r
    f3 = 2.0 * (1.0 - r * (Tf + t * (2.0 * e + 1.0)))
    f4 = (1.0 - math.exp(-2.0 * r * t)) * (e + r * t - 3.0 * r * t * e)
    f5 = r * e * (B * math.exp(-(1.0 + r * t)) + math.exp(-2.0 * r * t) - 1.0)

    return f1 + f2 / f3 - f4 / f5

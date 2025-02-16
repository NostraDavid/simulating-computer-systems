import math


def BW(p: float, B: int, M: int, N: int) -> float:
    bw0 = bw1 = p * N
    r = p
    x = 1.0 / p - 1.0

    while True:
        bw0 = bw1
        r = 1.0 / (1.0 + x * bw0 / (N * r))
        bw1 = BWi(r, B, M, N)
        if abs(bw1 - bw0) <= 0.005:
            break
    return bw1


def BWi(r: float, B: int, M: int, N: int) -> float:
    """Compute bandwidth for request rate r"""
    bw = 0.0
    q = 1.0 - math.pow(1.0 - r / M, float(N))

    for i in range(1, B):
        bw += i * f(i, M, q)
    for i in range(B, M + 1):
        bw += B * f(i, M, q)
    return bw


def Fact(n: int) -> float:
    """Compute n factorial"""
    z = 1.0
    while n:
        z *= n
        n -= 1
    return z


def C(n: int, k: int) -> float:
    """Compute binomial coefficient"""
    return Fact(n) / (Fact(k) * Fact(n - k))


def f(i: int, M: int, q: float) -> float:
    """Compute binomial probability"""
    return C(M, i) * math.pow(q, float(i)) * math.pow(1.0 - q, float(M - i))

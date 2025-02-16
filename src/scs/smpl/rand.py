import math

# Constants
A = 16807  # Multiplier for 'ranf'
M = 2147483647  # Modulus for 'ranf'

ln = [
    0,
    1973272912,
    747177549,
    20464843,
    640830765,
    1098742207,
    78126602,
    84743774,
    831312807,
    124667236,
    1172177002,
    1124933064,
    1223960546,
    1878982404,
    1449793615,
    553303732,
]  # Seeds for streams 1-15

strm = 1  # Index of current stream


def ranf() -> float:  # FIXME: weird implementation??
    """-------------------- UNIFORM [0, 1] RANDOM NUMBER GENERATOR --------------------"""
    global strm, ln
    ln[strm] = (A * ln[strm]) % M
    return ln[strm] * 4.656612875e-10  # Lo x 1/(2**31 - 1)


def stream(n: int) -> int:
    """-------------------- SELECT GENERATOR STREAM --------------------"""
    global strm
    if n < 0 or n > 15:
        raise ValueError("Stream Argument Error")
    if n:
        strm = n
    return strm


def seed(Ik: int, n: int) -> int:
    """-------------------- SET/GET SEED --------------------"""
    global ln
    if n < 1 or n > 15:
        raise ValueError("Seed Argument Error")
    if Ik > 0:
        ln[n] = Ik
    return ln[n]


def uniform(a: float, b: float) -> float:
    """-------------------- UNIFORM [a, b] RANDOM VARIATE GENERATOR --------------------"""
    if a > b:
        raise ValueError("Uniform Argument Error: a > b")
    return a + (b - a) * ranf()


def random(i: int, n: int) -> int:
    """-------------------- RANDOM INTEGER GENERATOR --------------------"""
    if i > n:
        raise ValueError("Random Argument Error: i > n")
    n -= i
    return i + int((n + 1.0) * ranf())


def expntl(x: float) -> float:
    """-------------------- EXPONENTIAL RANDOM VARIATE GENERATOR --------------------"""
    return -x * math.log(ranf())


def erlang(x: float, s: float) -> float:
    """-------------------- ERLANG RANDOM VARIATE GENERATOR --------------------"""
    if s > x:
        raise ValueError("Erlang Argument Error: s > x")
    k = int(x / s)
    z = 1.0
    for _ in range(k):
        z *= ranf()
    return -(x / k) * math.log(z)


def hyperx(x: float, s: float) -> float:
    """-------------------- HYPEREXPONENTIAL RANDOM VARIATE GENERATION --------------------"""
    if s <= x:
        raise ValueError("Hyperx Argument Error: s not > x")
    c = s / x
    z = math.sqrt((c * c - 1.0) / (c * c + 1.0))
    p = 0.5 * (1.0 - z)
    r = ranf()
    z = x * (1.0 - p) if r > p else x * (p / (1.0 - p))
    return -0.5 * z * math.log(ranf())


def normal(x: float, s: float) -> float:
    """-------------------- NORMAL RANDOM VARIATE GENERATOR --------------------"""
    global z2
    if z2 != 0.0:
        z1 = z2
        z2 = 0.0
    else:
        while True:
            v1 = 2.0 * ranf() - 1.0
            v2 = 2.0 * ranf() - 1.0
            w = v1 * v1 + v2 * v2
            if w < 1.0:
                break
        w = math.sqrt(-2.0 * math.log(w) / w)
        z1 = v1 * w
        z2 = v2 * w
    return x + z1 * s

import numpy as np
from structlog.stdlib import get_logger

logger = get_logger(__name__)


mxK: int = 9  # max. no. of service centers + 1
K: int = 3  # no. of centers (excl. terminals)
N: int = 16  # no. terminals (mpl for batch)
Z: float = 5000.0  # think time (0 for batch system)

D = np.zeros(mxK)  # D[k] = service demand at center k
R = np.zeros(mxK)  # R[k] = residence time at center k
Q = np.zeros(mxK)  # Q[k] = no. customers at center k


# Exact MVA for Single Class, FIFO Center Networks
def mva():
    # Exact mean value analysis for closed queueing
    # networks with a single customer class and only
    # first-in, first-out service centers.
    Q.fill(0.0)  # for (k=1; k<=K; k++) Q[k] = 0.0;

    for n in range(1, N + 1):
        for k in range(1, K + 1):
            R[k] = D[k] * (1.0 + Q[k])

        s: float = Z + sum(R[1 : K + 1])  # s=Z; for (k=1; k<=K; k++) s+=R[k];
        X: float = n / s

        for k in range(1, K + 1):
            Q[k] = X * R[k]

    print(" k       Rk     Qk     Uk")
    for k in range(1, K + 1):
        print(f"{k:2d}{R[k]:9.3f}{Q[k]:7.3f}{X * D[k]:7.3f}")

    print(f"\nX = {X:7.4f}, R = {(N / X) - Z:9.3f}\n")


def main():
    D[1] = 12 * 40.0
    D[2] = D[3] = 6 * (22.0 + 8.33 + 0.52)
    mva()


if __name__ == "__main__":
    main()

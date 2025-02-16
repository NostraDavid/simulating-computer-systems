from structlog.stdlib import get_logger
from scs.smpl import expntl

logger = get_logger(__name__)


def main() -> None:
    """Simulates a single-server queueing system with exponential interarrival and service times.
    This simulation models a M/M/1 queue where:
    - Customers arrive according to a Poisson process with mean interarrival time ta
    - Service times are exponentially distributed with mean ts
    - System is observed until time te
    Parameters
    ----------
    ta : float
        Mean interarrival time
    ts : float
        Mean service time
    te : float
        End time of simulation
    Variables
    ---------
    n : int
        Current number of customers in system
    t1 : float
        Time of next arrival
    t2 : float
        Time of next completion
    time : float
        Current simulation time
    Returns
    -------
    None
        Logs final number of customers in system at end of simulation
    """
    Ta: float = 200.0  # mean interarrival time
    Ts: float = 100.0  # mean service time
    te: float = 200000.0  # end time of simulation

    n: int = 0  # current number of customers in system
    t1: float = 0.0  # time of next arrival
    t2: float = te  # time of next completion
    time: float = 0.0  # current simulation time

    while time < te:
        if t1 < t2:  # event 1: arrival
            time = t1
            n += 1
            t1 = time + expntl(Ta)
            if n == 1:
                t2 = time + expntl(Ts)
        else:  # event 2: completion
            time = t2
            n -= 1
            if n > 0:
                t2 = time + expntl(Ts)
            else:
                t2 = te

    logger.info("final", n=n)


if __name__ == "__main__":
    main()

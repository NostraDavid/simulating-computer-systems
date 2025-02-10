import numpy as np

def expntl(mean: float) -> float:
    """Generate an exponentially distributed random variable."""
    return -mean * np.log(np.random.rand())

def simulate_queue(te: float = 200000.0, ta: float = 200.0, tz: float = 100.0) -> None:
    """Simulate a simple queuing system."""
    n = 0  # Number of customers in the system
    t1 = 1.0 + expntl(ta)  # First arrival time
    t2 = te  # Initially, no departures
    time = 0.0

    while time < te:
        if t1 < t2:
            # Event 1: Arrival
            time = t1
            n += 1
            t1 = time + expntl(ta)
        else:
            # Event 2: Completion
            time = t2
            n -= 1
            t2 = time + expntl(tz) if n > 0 else te

if __name__ == "__main__":
    simulate_queue()

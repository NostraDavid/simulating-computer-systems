import pyglet
from pyglet import shapes
from scs.smpl import expntl
from structlog.stdlib import get_logger

logger = get_logger(__name__)


class Customer:
    def __init__(self, x: float, y: float) -> None:
        self.shape: shapes.Circle = shapes.Circle(x, y, 20, color=(0, 0, 255))
        self.state: str = "arriving"  # arriving, waiting, or departing
        self.animating: bool = False
        self.start_x: float = x
        self.start_y: float = y
        self.target_x: float = x
        self.target_y: float = y
        self.animation_time: float = 0.0
        self.animation_duration: float = 0.5  # seconds

    def animate_to(self, target_x: float, target_y: float) -> None:
        self.start_x = self.shape.x
        self.start_y = self.shape.y
        self.target_x = target_x
        self.target_y = target_y
        self.animation_time = 0.0
        self.animating = True

    def update(self, dt: float) -> None:
        if self.animating:
            self.animation_time += dt
            progress = min(self.animation_time / self.animation_duration, 1.0)
            new_x = self.start_x + (self.target_x - self.start_x) * progress
            new_y = self.start_y + (self.target_y - self.start_y) * progress
            self.shape.x = new_x
            self.shape.y = new_y
            if progress >= 1.0:
                self.animating = False


class Simulation:
    def __init__(self, ta: float, ts: float, te: float, window_width: float) -> None:
        self.ta: float = ta
        self.ts: float = ts
        self.te: float = te
        self.n: int = 0              # number of customers in the system
        self.t1: float = 0.0         # next arrival time
        self.t2: float = te          # next departure time
        self.time: float = 0.0       # simulation time
        self.s: float = 0.0          # cumulative number-in-system time
        self.tn: float = 0.0         # last update time
        self.C: float = 0.0          # number of departures (completed customers)
        self.B: float = 0.0          # total busy time of server
        self.tb: float = 0.0         # time when server became busy
        # customers waiting or in service
        self.customers: list[Customer] = []
        # customers that have departed but are still animating off-screen
        self.departing_customers: list[Customer] = []
        self.window_width: float = window_width

    def update_targets(self) -> None:
        # The first customer goes to the server (centered at (75,300)),
        # waiting customers line up to its right.
        for i, customer in enumerate(self.customers):
            if i == 0:
                target = (75, 300)
            else:
                target = (120 + (i - 1) * 40, 300)
            customer.animate_to(target[0], target[1])

    def update_animations(self, dt: float) -> None:
        for customer in self.customers:
            customer.update(dt)
        for customer in self.departing_customers:
            customer.update(dt)
        # Remove departing customers that have finished their animation.
        self.departing_customers = [c for c in self.departing_customers if c.animating]

    def ready_for_event(self) -> bool:
        # Proceed only if all customers in the queue are stationary.
        return all(not c.animating for c in self.customers)

    def step(self) -> None:
        if self.time >= self.te:
            return
        if self.t1 < self.t2:
            # arrival event
            self.time = self.t1
            self.s += self.n * (self.time - self.tn)
            self.n += 1
            self.tn = self.time
            self.t1 = self.time + expntl(self.ta)
            # Create a new customer starting off-screen left.
            new_customer = Customer(x=-40, y=300)
            self.customers.append(new_customer)
            if self.n == 1:
                self.tb = self.time
                self.t2 = self.time + expntl(self.ts)
            self.update_targets()
        else:
            # departure event
            self.time = self.t2
            self.s += self.n * (self.time - self.tn)
            self.n -= 1
            self.tn = self.time
            self.C += 1
            if self.customers:
                # Remove the first customer from the queue and animate it off-screen right.
                departing = self.customers.pop(0)
                departing.state = "departing"
                departing.animate_to(self.window_width + 40, 300)
                self.departing_customers.append(departing)
            if self.n > 0:
                self.t2 = self.time + expntl(self.ts)
            else:
                self.t2 = self.te
                self.B += self.time - self.tb
            self.update_targets()

    def is_done(self) -> bool:
        # End the simulation if simulation time is reached and no customers remain.
        return (
            self.time >= self.te and not self.customers and not self.departing_customers
        )

    def results(self) -> dict[str, float]:
        x: float = self.C / self.time if self.time > 0 else 0.0
        u: float = self.B / self.time if self.time > 0 else 0.0
        l: float = self.s / self.time if self.time > 0 else 0.0
        w: float = l / x if x > 0 else 0.0
        return {"throughput": x, "utilization": u, "mean_in_system": l, "residence_time": w}


def main() -> None:
    window: pyglet.window.Window = pyglet.window.Window(
        width=800, height=600, caption="Simulation Visualization"
    )
    # Draw a red rectangle to represent the server.
    server_rect: shapes.Rectangle = shapes.Rectangle(
        x=50, y=275, width=50, height=50, color=(255, 0, 0)
    )
    sim: Simulation = Simulation(
        ta=200.0, ts=100.0, te=200000.0, window_width=window.width
    )

    @window.event
    def on_draw() -> None:
        window.clear()
        server_rect.draw()
        # Draw customers in the queue (and in service).
        for customer in sim.customers:
            customer.shape.draw()
        # Draw customers that are departing.
        for customer in sim.departing_customers:
            customer.shape.draw()

    def update(dt: float) -> None:
        sim.update_animations(dt)
        # Process the next simulation event only if the queue is stationary.
        if sim.ready_for_event() and sim.time < sim.te:
            sim.step()
        # Exit the app once the simulation is done.
        if sim.is_done():
            pyglet.app.exit()

    pyglet.clock.schedule_interval(update, 1 / 60)  # 60 fps update
    pyglet.app.run()

    results = sim.results()
    logger.info("throughput", x=results["throughput"])
    logger.info("utilization", u=results["utilization"])
    logger.info("mean_in_system", l=results["mean_in_system"])
    logger.info("residence_time", w=results["residence_time"])


if __name__ == "__main__":
    main()

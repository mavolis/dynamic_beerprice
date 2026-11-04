"""
================================================================
  PRICE ENGINE  —  edit this file to change how prices move
================================================================

  The only method you need to touch is `next_price()` below.
  Everything else (chart, display, button) lives in app.py and
  will automatically pick up whatever this method returns.
================================================================
"""
import random


class PriceEngine:
    def __init__(self, initial_price: float = 9.00):
        self.price          = initial_price
        self.mu_0           = initial_price  # mean is anchored to the starting price
        self.t              = 0
        self.history:       list[float] = [initial_price]
        self.event_occurred = False   # set True on the tick an event fires; app.py reads this
        self.event_sign     = 0      # +1 or -1, readable by app.py for coloring

    # ── ALGORITHM PARAMETERS ─────────────────────────────────────────────────
    DELTA = 0.007   # mean drift per tick — positive = downward (mean falls over time)
    RHO   = 0.85    # AR(1) coefficient: 0 = snaps back instantly, 1 = random walk
    SIGMA = 0.03    # noise std dev — controls how jagged the spikes are

    # Special event parameters
    # At 2 ticks/sec, avg interval = 1/EVENT_PROB ticks = 3 min → EVENT_PROB ≈ 1/360
    EVENT_PROB        = 1 / 360          # probability of an event firing each tick
    EVENT_SHOCK_MIN   = 0.50             # minimum shock magnitude (±)
    EVENT_SHOCK_MAX   = 2.00             # maximum shock magnitude (±)
    # ─────────────────────────────────────────────────────────────────────────

    # ── ALGORITHM ────────────────────────────────────────────────────────────
    def next_price(self) -> float:
        """
        AR(1) around a linearly drifting mean:

            price_t = μ_t + ρ · (price_{t-1} − μ_{t-1}) + ε_t

        where  μ_t = μ_0 − DELTA · t   (mean drifts downward each tick)
               ε_t ~ Normal(0, SIGMA²)  (Gaussian noise)

        Effect of RHO:
          → 0  : price snaps back to the trend line after each shock
          → 1  : price wanders freely (random walk with drift)
          ~0.85: shocks decay over ~6–7 ticks — realistic bar price memory

        BUY shocks push price above the trend; they decay at rate RHO per tick.
        """
        self.t += 1
        self.event_occurred = False
        self.event_sign     = 0

        mu_prev = self.mu_0 - self.DELTA * (self.t - 1)
        mu_curr = self.mu_0 - self.DELTA * self.t

        deviation = self.price - mu_prev
        noise     = random.gauss(0, self.SIGMA)
        new_price = mu_curr + self.RHO * deviation + noise

        # ── SPECIAL EVENT ────────────────────────────────────────────────────
        if random.random() < self.EVENT_PROB:
            magnitude           = random.uniform(self.EVENT_SHOCK_MIN, self.EVENT_SHOCK_MAX)
            sign                = random.choice([-1, 1])
            new_price          += sign * magnitude
            self.event_occurred = True
            self.event_sign     = sign
            # Reset mean to new level so price drifts from here
            self.mu_0 = max(0.50, new_price)
            self.t    = 0
        # ── END SPECIAL EVENT ────────────────────────────────────────────────

        self.price = max(0.50, round(new_price, 2))
        self.history.append(self.price)
        return self.price
    # ── END ALGORITHM ────────────────────────────────────────────────────────

    # ── BUY SHOCK ────────────────────────────────────────────────────────────
    def buy_shock(self) -> float:
        """
        Applied on every BUY press.
        Resets the AR(1) mean to the post-shock price, so the price drifts
        downward slowly from the new level rather than snapping back to the
        old trend.
        """
        shock      = random.uniform(0.05, 0.2)              # ← tune buy-shock range
        self.price = round(self.price + shock, 2)
        self.mu_0  = self.price   # anchor mean to new elevated price
        self.t     = 0            # restart drift from here
        self.history.append(self.price)
        return self.price
    # ── END BUY SHOCK ────────────────────────────────────────────────────────

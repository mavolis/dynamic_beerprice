"""
Beer Price Exchange — main application.
Run with:  .venv/bin/python3 app.py
"""
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import time

from price_engine import PriceEngine

# ── CONFIG ───────────────────────────────────────────────────────────────────
INITIAL_PRICE  = 9.00   # starting beer price in $
PRICE_TICK_MS  = 500    # how often the underlying price changes (ms)
RENDER_MS      = 33     # rendering frame rate (~30 fps)
WINDOW_SIZE    = 2000    # render frames kept in the chart window (~30 s at 30 fps)
WINDOW_W, WINDOW_H = 1000, 620
# ─────────────────────────────────────────────────────────────────────────────

BG       = "#0d0d0d"
CHART_BG = "#111111"
GREEN    = "#00e676"
RED      = "#ff1744"
GREY     = "#555555"
BTN_BG   = "#00c853"
BTN_FG   = "#0d0d0d"


class BeerPriceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🍺  Beer Price Exchange")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.engine        = PriceEngine(initial_price=INITIAL_PRICE)
        self.start_price   = INITIAL_PRICE   # where the line began this segment
        self.end_price     = INITIAL_PRICE   # where the line is heading
        self.display_price = INITIAL_PRICE   # current interpolated position
        self.tick_time     = time.time()     # wall-clock time of last price tick
        self.prices        = deque([INITIAL_PRICE], maxlen=WINDOW_SIZE)
        self.frames        = deque([0],              maxlen=WINDOW_SIZE)
        self.frame         = 0
        self.buy_frames    = []   # frame numbers of every BUY press
        self.event_frames  = []   # (frame, sign) for every special event

        self._build_header()
        self._build_chart()
        self._build_footer()
        self._start_loops()

    # ── UI CONSTRUCTION ───────────────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(12, 0))

        self.price_var = tk.StringVar(value=f"${INITIAL_PRICE:.2f}")
        self.price_label = tk.Label(
            header,
            textvariable=self.price_var,
            font=("Courier New", 36, "bold"),
            fg=GREEN,
            bg=BG,
            anchor="w",
        )
        self.price_label.pack(side="left")

        self.change_var = tk.StringVar(value="")
        tk.Label(
            header,
            textvariable=self.change_var,
            font=("Courier New", 16),
            fg=GREEN,
            bg=BG,
            anchor="w",
            width=12,
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        tk.Label(header, text="", font=("Courier New", 11), fg=GREY, bg=BG
                 ).pack(side="right", pady=(14, 0))

    def _build_chart(self):
        self.fig = plt.Figure(figsize=(10, 4.4), dpi=100, facecolor=CHART_BG)
        self.ax  = self.fig.add_subplot(111)
        self._style_axes()

        # Pre-create artists once — update their data every frame instead of ax.clear()
        self.line, = self.ax.plot([], [], color=GREEN, linewidth=2.0, zorder=2)
        self.dot,  = self.ax.plot([], [], "o", color=GREEN, markersize=5, zorder=3)
        self._fill   = None
        self._vlines = []

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().configure(bg=BG, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", pady=(4, 14))

        self.buy_btn = tk.Button(
            footer,
            text="BUY",
            font=("Courier New", 16, "bold"),
            fg=BTN_FG,
            bg=BTN_BG,
            activebackground="#31ab70",
            activeforeground=BTN_FG,
            relief="flat",
            padx=48,
            pady=10,
            cursor="hand2",
            command=self._on_buy,
        )
        self.buy_btn.pack()

    # ── CHART STYLING ─────────────────────────────────────────────────────────

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(CHART_BG)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color("#2a2a2a")
        ax.tick_params(colors=GREY, labelsize=9)
        ax.set_ylabel("Price  ($)", color=GREY, fontsize=10)
        ax.yaxis.label.set_color(GREY)
        ax.grid(axis="y", color="#1e1e1e", linewidth=0.8)
        self.fig.tight_layout(pad=1.4)

    # ── DUAL LOOP ─────────────────────────────────────────────────────────────

    def _start_loops(self):
        self._price_tick()   # slow loop: computes new target prices
        self._render()       # fast loop: lerps display and redraws

    def _price_tick(self):
        """Runs every PRICE_TICK_MS — sets the next target; line travels there linearly."""
        self.start_price = self.display_price          # start from wherever we are now
        self.end_price   = self.engine.next_price()    # ← calls price_engine.py
        self.tick_time   = time.time()

        diff  = self.end_price - self.start_price
        color = GREEN if diff >= 0 else RED
        sign  = "▲" if diff >= 0 else "▼"
        self.change_var.set(f"{sign} {abs(diff):.2f}")
        self.price_label.configure(fg=color)

        if self.engine.event_occurred:
            self.event_frames.append((self.frame, self.engine.event_sign))

        self.root.after(PRICE_TICK_MS, self._price_tick)

    def _render(self):
        """Runs every RENDER_MS — linearly interpolates toward end_price over PRICE_TICK_MS."""
        self.frame += 1

        t = min((time.time() - self.tick_time) / (PRICE_TICK_MS / 1000.0), 1.0)
        self.display_price = self.start_price + t * (self.end_price - self.start_price)

        self.prices.append(self.display_price)
        self.frames.append(self.frame)
        self.price_var.set(f"${self.display_price:.2f}")
        self._redraw()
        self.root.after(RENDER_MS, self._render)

    # ── CHART DRAW ────────────────────────────────────────────────────────────

    def _redraw(self):
        prices = list(self.prices)
        frames = list(self.frames)

        line_color = GREEN if prices[-1] >= prices[0] else RED

        # Update existing artists — no ax.clear(), keeps the event loop free
        self.line.set_data(frames, prices)
        self.line.set_color(line_color)
        self.dot.set_data([frames[-1]], [prices[-1]])
        self.dot.set_color(line_color)

        if self._fill is not None:
            self._fill.remove()
        self._fill = self.ax.fill_between(
            frames, prices, min(prices) * 0.97,
            alpha=0.12, color=line_color, zorder=1,
        )

        # Axes limits
        self.ax.set_xlim(frames[0], frames[-1] + 1)
        p_min, p_max = min(prices), max(prices)
        pad = max((p_max - p_min) * 0.08, 0.20)
        self.ax.set_ylim(p_min - pad, p_max + pad)

        # Vertical lines: buy (white), special event (green=positive, red=negative)
        for vl in self._vlines:
            vl.remove()
        self._vlines = []
        f_min, f_max = frames[0], frames[-1]
        for bf in self.buy_frames:
            if f_min <= bf <= f_max:
                self._vlines.append(self.ax.axvline(
                    x=bf, color="#ffffff", linewidth=1.2,
                    linestyle="--", alpha=0.45, zorder=4,
                ))
        for bf, sign in self.event_frames:
            if f_min <= bf <= f_max:
                color = GREEN if sign > 0 else RED
                self._vlines.append(self.ax.axvline(
                    x=bf, color=color, linewidth=1.5,
                    linestyle="--", alpha=0.7, zorder=4,
                ))

        self.canvas.draw_idle()

    # ── BUTTON HANDLER ────────────────────────────────────────────────────────

    def _on_buy(self):
        old_price      = self.engine.price
        new_price      = self.engine.buy_shock()
        shock          = new_price - old_price
        self.end_price += shock   # shift destination up; don't reset tick_time
        self.buy_frames.append(self.frame)

        self.change_var.set(f"▲ {shock:.2f}")
        self.price_label.configure(fg=GREEN)

        print(f"BUY  @ ${new_price:.2f}  (frame {self.frame})")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = BeerPriceApp(root)
    root.mainloop()

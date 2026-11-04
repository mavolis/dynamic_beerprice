# Beer Price Exchange

A small Tkinter + Matplotlib desktop app that shows a live, stock-ticker-style beer price. I vibe coded this on the following weekend after the Super Bowl, after being inspired by how the bar I watched the Super Bowl at designed their beer prices.

## Files
- `app.py` — the GUI: price display, live chart, and a **BUY** button. It runs two loops: a price tick every 500 ms and a ~30 fps render loop that moves the line smoothly between ticks.
- `price_engine.py` — the price model (`PriceEngine`). Edit this file to change how prices move.

## Price model
- **Base process:** AR(1) around a mean that drifts slowly downward: `p_t = μ_t + ρ(p_{t-1} − μ_{t-1}) + ε_t`, with `μ_t = μ_0 − δt` and `ε_t ~ N(0, σ²)`.
- **BUY:** each press adds a shock of +$0.05–0.20 and re-anchors the mean at the new price.
- **Random events:** on average once every ~3 minutes, a ±$0.50–2.00 jump that also re-anchors the mean. These show as green or red dashed lines on the chart; BUY presses show as white dashed lines.
- The price never drops below $0.50.

You can tune the parameters (`DELTA`, `RHO`, `SIGMA`, `EVENT_*`) at the top of `PriceEngine`, and the timing and window settings in the `CONFIG` block of `app.py`.

## Run
```bash
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
.venv/bin/python3 app.py
```
Tkinter must be available in your Python install.

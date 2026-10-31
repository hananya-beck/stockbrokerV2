# Exercise 1 — Three EARS requirements

> Slide 32. v2 epic (section B): **backtest simulator** — simulate what
> following the dashboard's suggested monthly allocation would have returned
> historically, compared to an equal-weight baseline. Branch: `feat/backtest-simulator`.

One requirement per EARS pattern, as the exercise asks: event-driven, state-driven, unwanted-behavior.

1. **Event-driven.** When the user enters a start date and a monthly deposit
   amount and clicks "Run backtest," the system shall compute, for each month
   in that range, the simulated portfolio value by applying that month's
   suggested allocation weights to the historical NAV data, and shall render
   the resulting cumulative value as a line chart.

2. **State-driven.** While the backtest chart is displayed, the system shall
   also plot an equal-weight baseline (the same monthly deposit split evenly
   across all seven funds) on the same chart, so the recommended-allocation
   line is always shown next to that comparison.

3. **Unwanted-behavior.** If a fund has no NAV data for one or more months
   inside the selected backtest range, then the system shall exclude that
   fund's weight from the affected months (redistributing it proportionally
   among the funds that do have data) and visibly mark those months in the
   chart, rather than silently treating the missing NAV as zero or crashing
   the simulation.

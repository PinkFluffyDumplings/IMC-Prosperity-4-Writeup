# IMC Prosperity 4

Our team, `Pink Fluffy Dumplings` finished **#13** globally in IMC Prosperity 4 with a cumulative Phase-2 PnL of 1,096,164 XIRECs (Algo 1,062,502 + Manual 33,662). On the algorithmic challenge alone, we finished **#9 globally**. This placed us **#4 in Australia** overall, and **#2** in the algorithmic component.

This writeup includes the strategies and ideas we implemented, and takeaways from Prosperity - our first algorithmic trading competition :) 

> *Note: Our final round submission was unfortunately copied by another team, so although we were still scored, our final rank wasn't initially published onto the public leaderboard. We emailed the Prosperity team and they kindly confirmed we *"still appeared as 13th globally"* on their final recruiter leaderboard.*

## Round 3 — Mean Reversion & Inverse Momentum

**Algo PnL: +103,038** • **Algo rank: #262** • **Manual PnL: +71,118** • **Manual rank: #420** • **Round 3 total: +174,156**

Round 3 gave us two underlying products — `HYDROGEL_PACK` and `VELVETFRUIT_EXTRACT` (VEE) — plus a full chain of vouchers (european options) on VEE across strikes from 4000 to 6500. Plotting the mid prices for both stocks immediately suggested mean reversion: noisy, range-bound walks with no persistent drift.

<p align="center">
  <img src="images/hydrogel_vee_mids.png" width="80%" alt="HYDROGEL_PACK and VELVETFRUIT_EXTRACT mid prices over the three training days"/>
</p>

Our first attempt on the options was IV scalping, an idea borrowed from previous years' writeups. However, we eventually realised that the volatility smile wasn't stable enough — the IV wobble wasn't profitable enough to scalp relative to the noise in the parabola fit. We later realised it was more profitable to trade the vouchers directionally as part of mean reversion.

For `HYDROGEL_PACK` we also did mean reversion. We calculated the mean/fair value at **9990**, and ran a sweep of backtests to find entry levels: buy down to max long when the mid fell ~45 below fair (around **9945**), neutralise back to flat at fair (**9990**), and sell to max short when the mid rose ~30 above fair (around **10020**). We implemented this using three resting limit orders sized to fill when something crossed each level.

We also tried to build a regime logic off the opening prints. If VEE opened high we'd lean harder long on `HYDROGEL_PACK` with a lower buy grid and treat the vouchers differently; if `HYDROGEL_PACK` itself opened cheap, a separate set of voucher logic kicked in. We later realised this part was overfit.

We also noticed VEE tended to overshoot the mean and then bounce on each move, so instead of the standard "buy low, sell high, flatten in the middle" band, we tried a more aggressive version: whenever VEE retraced 35 points from a local extreme, we would take our max position in the direction of the eventual reversion. Based on previous data, we predicted that VEE and the vouchers would bounce at the extremes more reliably than they would drift through the mean.

For the vouchers, we implemented a more involved idea for this round. We computed the rough deltas of each voucher to estimate where they should be priced, then bought or sold them relative to the VEE signal. Rather than fitting Black-Scholes, we extracted each voucher's delta directly from the chain by taking the slope of voucher mid price against strike — a model-free shortcut that sidesteps having to know TTE or volatility.

<p align="center">
  <img src="images/voucher_delta_explainer.png" width="90%" alt="Empirical delta extraction — slope of voucher mid price vs strike gives delta directly from the chain"/>
</p>

***Strategy:*** `HYDROGEL_PACK` — symmetric mean-reversion band (buy ≈ 9945, neutral 9990, sell ≈ 10020) via three resting orders, with opening-regime adjustments. VEE — inverse-momentum reversal trading: track the running anchor, and on a reversal of ≥35 from the extreme, take max long/short into the next bounce. Vouchers — directional long/short tied to the VEE signal, with empirical deltas pulled from the chain slope used to translate VEE-side triggers into voucher-side entry/exit prices.

**What went wrong:** Unfortunately, we got quite unlucky. VEE opened high and fell *straight to the bottom* during the first half of the day without bouncing in the way we predicted, so we were positioned for a reversal that never came and made far less than a plain mean-reversion approach would have. We had spotted the right structure but traded it the wrong way. The simpler, more robust version of a signal usually generalises better than the clever one that maxes out the backtest.

<p align="center">
  <img src="images/vee_live_round3.png" width="80%" alt="VELVETFRUIT_EXTRACT mid price during the live Round 3 submission — opens high, falls without bouncing"/>
</p>

## Round 2 — [Strategy name]

**Algo PnL: +[X]** • **Algo rank: #[X]**

[What changed from round 1? What new information or products did you get?]

***Strategy:*** [What you implemented.]

## Round 3 — [Strategy name]

**Algo PnL: +[X]** • **Algo rank: #[X]**

[Context and observations.]

***Strategy:*** [What you implemented.]

## Round 4 — [Strategy name]

**Algo PnL: +[X]** • **Algo rank: #[X]**

[Context and observations.]

***Strategy:*** [What you implemented.]

## Round 5 — [Strategy name]

**Algo PnL: +[X]** • **Algo rank: #[X]**

[Context and observations.]

***Strategy:*** [What you implemented.]

## Manual

### Round 1 — [X]
[What you did.]

### Round 2 — [X]
[What you did.]

### Round 3 — [X]
[What you did.]

### Round 4 — [X]
[What you did.]

### Round 5 — [X]
[What you did.]

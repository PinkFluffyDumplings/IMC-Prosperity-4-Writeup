# IMC Prosperity 4

Our team, `Pink Fluffy Dumplings` finished **#13** globally in IMC Prosperity 4 with a cumulative Phase-2 PnL of 1,096,164 XIRECs (Algo 1,062,502 + Manual 33,662). On the algorithmic challenge alone, we finished **#9 globally**. This placed us **#4 in Australia** overall, and **#2** in the algorithmic component.

This writeup includes the strategies and ideas we implemented, and takeaways from Prosperity - our first algorithmic trading competition :) 

> *Note: Our final round submission was unfortunately copied by another team, so although we were still scored, our final rank wasn't initially published onto the public leaderboard. We emailed the Prosperity team and they kindly confirmed we *"appear as 13th globally"* on their final recruiter leaderboard.*

## Round 3 — Mean Reversion & Inverse Momentum

**Algo PnL: +[X]** • **Algo rank: #[X]**

Round 3 gave us two underlying products — `HYDROGEL_PACK` and `VELVETFRUIT_EXTRACT` (VEE) — plus a full chain of vouchers (european options) on VEE across strikes from 4000 to 6500. Plotting the mid prices for both stocks immediately suggested mean reversion: noisy, range-bound walks with no persistent drift.

<p align="center">
  <img src="images/hydrogel_vee_mids.png" width="80%" alt="HYDROGEL_PACK and VELVETFRUIT_EXTRACT mid prices over the three training days"/>
</p>

**Day 1.** Our first instinct on the options was IV scalping — fit a surface, trade deviations. But after some digging we realised the vouchers were rarely mispriced relative to their implied vol; the IV wobble just wasn't large enough to scalp profitably. Simply going long or short the options directionally made far more money than trying to scalp the surface, so we dropped IV scalping entirely and treated the vouchers as a lever on VEE itself.

For `HYDROGEL_PACK` we settled on a clean mean-reversion band. We estimated fair value at **9990**, and ran a sweep of backtests to find entry levels: buy down to max long when the mid fell ~45 below fair (around **9945**), neutralise back to flat at fair (**9990**), and sell to max short when the mid rose ~30 above fair (around **10020**). We implemented this as three resting limit orders sized so that our aggregated bid/ask volume never breaches the position limit at any intermediate position — a simple, capacity-respecting three-state band.

We also built regime logic off the opening prints. If VEE opened high we'd lean harder long on `HYDROGEL_PACK` with a lower buy grid and treat the vouchers differently; if `HYDROGEL_PACK` itself opened cheap, a separate set of voucher logic kicked in. The intuition was that the opening level told us something about which side of the range we were starting from.

**Day 2.** Here's where we made our key (and ultimately costly) call on VEE. We noticed that when VEE reverted to its mean, it tended to *keep going* in that same direction rather than settling — i.e. it overshot. So instead of the standard "buy low, sell high, flatten in the middle" two-step mean reversion, we chose to ride the move: whenever VEE swung from a local high or low back through the mid by more than our reversal threshold (35), we'd aggressively flip to max position in the *opposite* direction, betting on the bounce continuing. Since we were chasing a high finish, taking this more aggressive trend bet seemed worth it.

***Strategy:*** `HYDROGEL_PACK` — symmetric mean-reversion band (buy ≈ 9945, neutral 9990, sell ≈ 10020) via three capacity-aware resting orders, with opening-regime adjustments. VEE — inverse-momentum reversal trading: track the running anchor, and on a reversal of ≥35 from the extreme, take max long/short into the bounce. Vouchers — directional long/short tied to the VEE signal and opening regime rather than IV scalping, with deep out-of-the-money wings (6000, 6500) left as free zero-bid options.

**What went wrong:** The VEE reversal strategy backtested beautifully — but it was more overfit than just plainly buying low and selling high. The unseen evaluation data opened high and then fell *straight to the bottom* without bouncing. So even though we'd correctly identified that VEE mean-reverts, our algorithm was positioned for a continuation that never came, and made far less than it could have. We spotted the right structure but traded it the wrong way, which cost us a much better placement this round. Lesson learned: the simpler, more robust version of a signal usually generalises better than the clever one that maxes out the backtest.

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

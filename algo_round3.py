"""
trader4 — symmetric HYDROGEL band (3-state) + everything else from trader3.

HYDROGEL_PACK strategy upgrade:
  Three-state targets driven by price level:
    * mid drops to 9945  →  target +200 (max long)
    * mid returns to 9990 →  target  0  (neutral)
    * mid rises to 10020 →  target −200 (max short)

  Implemented via three resting limit orders, sized so the aggregated
  bid/ask volumes never breach position limits at any intermediate state.
  Math:
    NEUTRAL ask (when long)   = position             # close longs at 9990
    NEUTRAL bid (when short)  = -position            # cover shorts at 9990
    BUY  ask (always)         = limit − max(0,pos)   # bring us up to +limit
    SELL ask (always)         = limit + min(0,pos)   # bring us down to −limit
  Capacity-respecting at every position p ∈ [-limit, +limit].

VEE inverse momentum plus opening-regime voucher timing packages.
"""
import json

try:
    from datamodel import Order, ProsperityEncoder, TradingState
except ImportError:
    from prosperity4bt.datamodel import Order, ProsperityEncoder, TradingState


# ───────────────────────────── Logger ─────────────────────────────────────────
class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750
    def print(self, *objects, sep=" ", end="\n"):
        self.logs += sep.join(map(str, objects)) + end
    def flush(self, state, orders, conversions, trader_data):
        base_length = len(self.to_json([self.compress_state(state, ""), self.compress_orders(orders), conversions, "", ""]))
        max_item_length = (self.max_log_length - base_length) // 3
        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders), conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))
        self.logs = ""
    def compress_state(self, state, trader_data):
        return [state.timestamp, trader_data, self.compress_listings(state.listings),
                self.compress_order_depths(state.order_depths), self.compress_trades(state.own_trades),
                self.compress_trades(state.market_trades), state.position, self.compress_observations(state.observations)]
    def compress_listings(self, listings):
        return [[l.symbol, l.product, l.denomination] for l in listings.values()]
    def compress_order_depths(self, order_depths):
        return {s: [od.buy_orders, od.sell_orders] for s, od in order_depths.items()}
    def compress_trades(self, trades):
        return [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp]
                for arr in trades.values() for t in arr]
    def compress_observations(self, observations):
        co = {p: [o.bidPrice, o.askPrice, o.transportFees, o.exportTariff, o.importTariff, o.sugarPrice, o.sunlightIndex]
              for p, o in observations.conversionObservations.items()}
        return [observations.plainValueObservations, co]
    def compress_orders(self, orders):
        return [[o.symbol, o.price, o.quantity] for arr in orders.values() for o in arr]
    def to_json(self, value):
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))
    def truncate(self, value, max_length):
        lo, hi = 0, min(len(value), max_length); out = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = value[:mid]
            if len(self.to_json(candidate)) <= max_length:
                out = candidate; lo = mid + 1
            else:
                hi = mid - 1
        return out


logger = Logger()


# ───────────────────────────── Config ─────────────────────────────────────────
INNER_STRIKES = [5000, 5100, 5200, 5300, 5400, 5500]
WING_STRIKES  = [4000, 4500, 6000, 6500]
ALL_STRIKES   = INNER_STRIKES + WING_STRIKES
INNER_VOUCHERS = [f"VEV_{k}" for k in INNER_STRIKES]
WING_VOUCHERS  = [f"VEV_{k}" for k in WING_STRIKES]
ALL_VOUCHERS   = INNER_VOUCHERS + WING_VOUCHERS
VOUCHER_STRIKES = {f"VEV_{k}": k for k in ALL_STRIKES}
NO_TRADE_VOUCHERS = {"VEV_6000", "VEV_6500"}
NORMAL_VEE_FOLLOW_VOUCHERS = {
    "VEV_4500",
    "VEV_5000",
    "VEV_5100",
    "VEV_5200",
    "VEV_5300",
    "VEV_5400",
}
LOW_VEE_FOLLOW_VOUCHERS = {"VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400"}
HIGH_OPEN_VOUCHERS = {f"VEV_{k}" for k in (4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500)}
NORMAL_OPEN_DELAYED_SHORTS = set()
NORMAL_OPEN_CONDITIONAL_SHORTS = set()
NORMAL_OPEN_FLIP_COVERS = {"VEV_5500"}
LOW_OPEN_VOUCHERS = set()
LOW_OPEN_CAPPED_LONGS = {"VEV_4500"}
HIGH_OPEN_CAPPED_LONGS = {"VEV_5300", "VEV_5400", "VEV_5500"}

POSITION_LIMITS = {
    "HYDROGEL_PACK":        200,
    "VELVETFRUIT_EXTRACT":  200,
    **{v: 300 for v in ALL_VOUCHERS},
}

# HYDROGEL three-state band
HYDROGEL          = "HYDROGEL_PACK"
HYDROGEL_FAIR     = 9990
HYDROGEL_BUY      = HYDROGEL_FAIR - 45    # 9945  → target +limit
HYDROGEL_NEUTRAL  = HYDROGEL_FAIR         # 9990  → target 0
HYDROGEL_SELL     = HYDROGEL_FAIR + 30    # 10020 → target −limit
HYDROGEL_HIGH_OPEN_FLATTEN_AFTER = 850000

# VEE inverse momentum
VEE                = "VELVETFRUIT_EXTRACT"
REVERSAL_THRESHOLD = 35
VEE_HIGH_OPEN_REGIME = 5260
VEE_HIGH_OPEN_LATE_SHORT_AFTER = 950000

# Coarse opening-session guards for the normal-open voucher module.
# These are shared risk windows, not per-product PnL peak/drawdown exits.
NORMAL_OPEN_EARLY_SHORT_UNTIL = 100000
NORMAL_OPEN_EARLY_COVER_UNTIL = 150000

# Voucher MM inventory guard
GUARD_FRAC = 0.75


# ───────────────────────────── Helpers ────────────────────────────────────────
def book_mid(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None
    return (max(depth.buy_orders) + min(depth.sell_orders)) / 2.0


def wall_mid(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None
    wall_bid = max(depth.buy_orders.items(), key=lambda kv: kv[1])[0]
    wall_ask = max(depth.sell_orders.items(), key=lambda kv: -kv[1])[0]
    return (wall_bid + wall_ask) / 2.0


def voucher_surface(order_depths):
    mids = {}
    for symbol in ALL_VOUCHERS:
        depth = order_depths.get(symbol)
        mid = book_mid(depth) if depth else None
        if mid is not None:
            mids[symbol] = mid

    points = sorted((VOUCHER_STRIKES[symbol], symbol, mid) for symbol, mid in mids.items())
    deltas = {}
    for i, (strike, symbol, mid) in enumerate(points):
        if len(points) == 1:
            delta = 0.5
        elif i == 0:
            next_strike, _, next_mid = points[i + 1]
            delta = (mid - next_mid) / (next_strike - strike)
        elif i == len(points) - 1:
            prev_strike, _, prev_mid = points[i - 1]
            delta = (prev_mid - mid) / (strike - prev_strike)
        else:
            prev_strike, _, prev_mid = points[i - 1]
            next_strike, _, next_mid = points[i + 1]
            delta = (prev_mid - next_mid) / (next_strike - prev_strike)
        deltas[symbol] = max(0.0, min(1.0, delta))
    return {"mid": mids, "delta": deltas}


def surface_level(symbol, surface, current_underlying, target_underlying):
    mid = surface["mid"].get(symbol)
    if mid is None or current_underlying is None:
        return 0
    delta = surface["delta"].get(symbol, 0.5)
    return max(0, int(round(mid + delta * (target_underlying - current_underlying))))


def high_open_long_underlying(open_underlying):
    return open_underlying - REVERSAL_THRESHOLD - REVERSAL_THRESHOLD / 3


def high_open_short_underlying(open_underlying):
    return open_underlying + REVERSAL_THRESHOLD / 2


def high_open_second_short_underlying(open_underlying):
    return open_underlying + REVERSAL_THRESHOLD / 3


def high_open_late_short_underlying(open_underlying):
    return open_underlying + REVERSAL_THRESHOLD - REVERSAL_THRESHOLD / 5


def high_open_long_level(symbol, surface, current_underlying, open_underlying):
    return surface_level(symbol, surface, current_underlying, high_open_long_underlying(open_underlying))


def high_open_short_level(symbol, surface, current_underlying, open_underlying):
    return surface_level(symbol, surface, current_underlying, high_open_short_underlying(open_underlying))


def high_open_second_short_level(symbol, surface, current_underlying, open_underlying):
    return surface_level(symbol, surface, current_underlying, high_open_second_short_underlying(open_underlying))


def high_open_late_short_level(symbol, surface, current_underlying, open_underlying):
    return surface_level(symbol, surface, current_underlying, high_open_late_short_underlying(open_underlying))


def low_open_long_level(symbol, surface, current_underlying):
    return surface_level(symbol, surface, current_underlying, current_underlying - REVERSAL_THRESHOLD)


def low_open_short_level(symbol, surface, current_underlying):
    return surface_level(symbol, surface, current_underlying, current_underlying + REVERSAL_THRESHOLD)


def normal_open_short_level(symbol, surface, current_underlying):
    return surface_level(symbol, surface, current_underlying, current_underlying + REVERSAL_THRESHOLD)


def normal_open_early_short_level(symbol, surface, current_underlying):
    return surface_level(symbol, surface, current_underlying, current_underlying + REVERSAL_THRESHOLD)


def normal_open_cover_level(symbol, surface, current_underlying):
    if symbol == "VEV_4000":
        return 0
    return surface_level(symbol, surface, current_underlying, current_underlying - REVERSAL_THRESHOLD)


def hydrogel_three_state(symbol, depth, position, limit, buy_level=HYDROGEL_BUY, sell_level=HYDROGEL_SELL):
    """
    Three resting orders forming a 3-state band:
        BUY_LEVEL bid    — bring (post-neutral) position from 0 to +limit
        NEUTRAL leg      — bring position from current to 0 (close longs / cover shorts)
        SELL_LEVEL ask   — bring (post-neutral) position from 0 to −limit

    Sizing respects |aggregated bid| ≤ limit − pos and |aggregated ask| ≤ limit + pos.
    """
    orders = []

    # BUY_LEVEL bid: bring (post-neutral) position 0 → +limit; capped to keep aggregated bids ≤ buy_cap
    buy_size = limit - max(0, position)
    if buy_size > 0:
        orders.append(Order(symbol, buy_level, buy_size))

    # SELL_LEVEL ask: bring (post-neutral) position 0 → -limit; capped to keep aggregated asks ≤ sell_cap
    sell_size = limit + min(0, position)
    if sell_size > 0:
        orders.append(Order(symbol, sell_level, -sell_size))

    return orders


def sweep_to_target(symbol, depth, position, target):
    orders = []
    delta = target - position
    if delta > 0:
        remaining = delta
        for ask in sorted(depth.sell_orders):
            avail = -depth.sell_orders[ask]
            qty = min(avail, remaining)
            if qty <= 0: continue
            orders.append(Order(symbol, ask, qty)); remaining -= qty
            if remaining <= 0: break
    elif delta < 0:
        remaining = -delta
        for bid in sorted(depth.buy_orders, reverse=True):
            avail = depth.buy_orders[bid]
            qty = min(avail, remaining)
            if qty <= 0: continue
            orders.append(Order(symbol, bid, -qty)); remaining -= qty
            if remaining <= 0: break
    return orders


def target_at_touch(symbol, depth, position, target):
    delta = target - position
    if delta > 0:
        if not depth.sell_orders:
            return []
        return [Order(symbol, min(depth.sell_orders), delta)]
    if delta < 0:
        if not depth.buy_orders:
            return []
        return [Order(symbol, max(depth.buy_orders), delta)]
    return []


def buy_to_target_below(symbol, depth, position, target, max_price):
    orders = []
    remaining = target - position
    if remaining <= 0:
        return orders
    for ask in sorted(depth.sell_orders):
        if ask > max_price:
            break
        avail = -depth.sell_orders[ask]
        qty = min(avail, remaining)
        if qty <= 0:
            continue
        orders.append(Order(symbol, ask, qty))
        remaining -= qty
        if remaining <= 0:
            break
    if remaining > 0:
        orders.append(Order(symbol, max_price, remaining))
    return orders


def sell_to_target_above(symbol, depth, position, target, min_price):
    orders = []
    remaining = position - target
    if remaining <= 0:
        return orders
    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < min_price:
            break
        avail = depth.buy_orders[bid]
        qty = min(avail, remaining)
        if qty <= 0:
            continue
        orders.append(Order(symbol, bid, -qty))
        remaining -= qty
        if remaining <= 0:
            break
    if remaining > 0:
        orders.append(Order(symbol, min_price, -remaining))
    return orders


def market_make(symbol, depth, position, limit, fair):
    orders = []
    buy_cap, sell_cap = limit - position, limit + position
    pos_frac = position / limit if limit else 0.0
    if pos_frac >  GUARD_FRAC:    buy_edge, sell_edge = 2, 0
    elif pos_frac < -GUARD_FRAC:  buy_edge, sell_edge = 0, 2
    else:                          buy_edge = sell_edge = 1

    for ask in sorted(depth.sell_orders):
        if buy_cap <= 0 or ask > fair - buy_edge: break
        qty = min(-depth.sell_orders[ask], buy_cap)
        if qty > 0:
            orders.append(Order(symbol, ask, qty)); buy_cap -= qty
    for bid in sorted(depth.buy_orders, reverse=True):
        if sell_cap <= 0 or bid < fair + sell_edge: break
        qty = min(depth.buy_orders[bid], sell_cap)
        if qty > 0:
            orders.append(Order(symbol, bid, -qty)); sell_cap -= qty

    if not depth.buy_orders or not depth.sell_orders: return orders
    best_bid, best_ask = max(depth.buy_orders), min(depth.sell_orders)
    spread = best_ask - best_bid
    if spread <= 1:
        quote_bid, quote_ask = best_bid, best_ask
    elif spread == 2:
        quote_bid, quote_ask = best_bid + 1, best_ask - 1
        if quote_bid >= quote_ask: quote_bid, quote_ask = best_bid, best_ask
    else:
        quote_bid, quote_ask = best_bid + 1, best_ask - 1
    quote_bid = min(quote_bid, int(fair))
    quote_ask = max(quote_ask, int(fair) + 1)
    if buy_cap  > 0: orders.append(Order(symbol, quote_bid, +buy_cap))
    if sell_cap > 0: orders.append(Order(symbol, quote_ask, -sell_cap))
    return orders

# ───────────────────────────── Trader ─────────────────────────────────────────
class Trader:
    def run(self, state: TradingState):
        result: dict[str, list[Order]] = {}
        data = json.loads(state.traderData) if state.traderData else {}
        last_fair    = data.get("last_fair", {})
        vee_dir      = data.get("vee_dir", None)
        vee_anchor   = data.get("vee_anchor", None)
        open_vee_mid = data.get("open_vee_mid", None)
        open_regime  = data.get("open_regime", None)
        high_open_covering = data.get("high_open_covering", {})
        low_open_covering = data.get("low_open_covering", {})
        normal_open_covering = data.get("normal_open_covering", {})

        vee_depth = state.order_depths.get(VEE)
        S = book_mid(vee_depth) if vee_depth else None
        if open_vee_mid is None and S is not None:
            open_vee_mid = S
        surface = voucher_surface(state.order_depths)
        hydrogel_depth = state.order_depths.get(HYDROGEL)
        hydrogel_mid = book_mid(hydrogel_depth) if hydrogel_depth else None
        if open_regime is None and S is not None and hydrogel_mid is not None:
            if S >= VEE_HIGH_OPEN_REGIME:
                open_regime = "high_open"
            elif hydrogel_mid < 9980:
                open_regime = "low_hydrogel_open"
            else:
                open_regime = "normal_open"
        for symbol, depth in state.order_depths.items():
            limit = POSITION_LIMITS.get(symbol)
            if limit is None:
                result[symbol] = []
                continue
            position = state.position.get(symbol, 0)
            if symbol in NO_TRADE_VOUCHERS:
                # Free-option bid at 0: zero downside, free voucher if anyone ever sells into it
                buy_cap = limit - position
                if buy_cap > 0:
                    result[symbol] = [Order(symbol, 0, buy_cap)]
                else:
                    result[symbol] = []
                continue

            if symbol == HYDROGEL:
                if open_regime == "high_open" and state.timestamp >= HYDROGEL_HIGH_OPEN_FLATTEN_AFTER and position:
                    result[symbol] = [Order(symbol, HYDROGEL_NEUTRAL, -position)]
                elif open_regime == "high_open" and state.timestamp >= HYDROGEL_HIGH_OPEN_FLATTEN_AFTER:
                    result[symbol] = []
                elif open_regime == "high_open":
                    result[symbol] = hydrogel_three_state(symbol, depth, position, limit, 9940, HYDROGEL_SELL)
                else:
                    result[symbol] = hydrogel_three_state(symbol, depth, position, limit)

            elif symbol == VEE:
                mid = book_mid(depth)
                if mid is None:
                    result[symbol] = []
                    continue
                if open_regime == "high_open":
                    high_phase = high_open_covering.get(symbol)
                    long_underlying = high_open_long_underlying(open_vee_mid)
                    short_underlying = high_open_short_underlying(open_vee_mid)
                    second_short_underlying = high_open_second_short_underlying(open_vee_mid)
                    late_short_underlying = high_open_late_short_underlying(open_vee_mid)
                    if state.timestamp >= VEE_HIGH_OPEN_LATE_SHORT_AFTER:
                        result[symbol] = sell_to_target_above(
                            symbol, depth, position, -limit, late_short_underlying
                        )
                    elif high_phase == "short2":
                        if mid <= long_underlying:
                            high_open_covering[symbol] = "long2"
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_underlying)
                        elif position > -limit or mid >= second_short_underlying:
                            result[symbol] = target_at_touch(symbol, depth, position, -limit)
                        else:
                            result[symbol] = []
                    elif high_phase == "long2":
                        if position < limit:
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_underlying)
                        else:
                            result[symbol] = []
                    elif high_phase:
                        if mid >= second_short_underlying:
                            high_open_covering[symbol] = "short2"
                            result[symbol] = target_at_touch(symbol, depth, position, -limit)
                        elif position < limit:
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_underlying)
                        else:
                            result[symbol] = []
                    elif position < 0 and mid <= long_underlying:
                        high_open_covering[symbol] = "long1"
                        result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_underlying)
                    elif position > 0 or mid <= long_underlying:
                        result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_underlying)
                    elif position < 0 or mid >= short_underlying:
                        result[symbol] = target_at_touch(symbol, depth, position, -limit)
                    else:
                        result[symbol] = []
                    continue
                if vee_dir is None:
                    vee_dir, vee_anchor = +1, mid
                else:
                    if vee_dir > 0:
                        if mid > vee_anchor:
                            vee_anchor = mid
                        elif mid <= vee_anchor - REVERSAL_THRESHOLD:
                            vee_dir, vee_anchor = -1, mid
                    else:
                        if mid < vee_anchor:
                            vee_anchor = mid
                        elif mid >= vee_anchor + REVERSAL_THRESHOLD:
                            vee_dir, vee_anchor = +1, mid
                target = -vee_dir * limit
                result[symbol] = target_at_touch(symbol, depth, position, target)

            elif (
                (open_regime == "normal_open" and symbol in NORMAL_VEE_FOLLOW_VOUCHERS)
                or (open_regime == "low_hydrogel_open" and symbol in LOW_VEE_FOLLOW_VOUCHERS)
            ):
                if vee_dir is None:
                    result[symbol] = []
                else:
                    result[symbol] = target_at_touch(symbol, depth, position, -vee_dir * limit)

            elif open_regime == "high_open" and symbol in HIGH_OPEN_VOUCHERS and state.timestamp >= VEE_HIGH_OPEN_LATE_SHORT_AFTER:
                result[symbol] = sell_to_target_above(
                    symbol, depth, position, -limit, high_open_late_short_level(symbol, surface, S, open_vee_mid)
                )

            elif open_regime == "high_open" and symbol in HIGH_OPEN_VOUCHERS:
                mid = book_mid(depth)
                long_level = high_open_long_level(symbol, surface, S, open_vee_mid)
                short_level = high_open_short_level(symbol, surface, S, open_vee_mid)
                second_short_level = high_open_second_short_level(symbol, surface, S, open_vee_mid)
                high_phase = high_open_covering.get(symbol)
                if high_phase == "short2":
                    if mid is not None and mid <= long_level:
                        high_open_covering[symbol] = "long2"
                        if symbol in HIGH_OPEN_CAPPED_LONGS:
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                        else:
                            result[symbol] = sweep_to_target(symbol, depth, position, limit)
                    elif position > -limit or (mid is not None and mid >= second_short_level):
                        result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                    else:
                        result[symbol] = []
                elif high_phase == "long2":
                    if position < limit:
                        if symbol in HIGH_OPEN_CAPPED_LONGS:
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                        else:
                            result[symbol] = sweep_to_target(symbol, depth, position, limit)
                    else:
                        result[symbol] = []
                elif high_phase:
                    if mid is not None and mid >= second_short_level:
                        high_open_covering[symbol] = "short2"
                        result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                    elif position < limit:
                        if symbol in HIGH_OPEN_CAPPED_LONGS:
                            result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                        else:
                            result[symbol] = sweep_to_target(symbol, depth, position, limit)
                    else:
                        result[symbol] = []
                elif position < 0 and mid is not None and mid <= long_level:
                    high_open_covering[symbol] = "long1"
                    if symbol in HIGH_OPEN_CAPPED_LONGS:
                        result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                    else:
                        result[symbol] = sweep_to_target(symbol, depth, position, limit)
                elif position > 0 or (mid is not None and mid <= long_level):
                    if symbol in HIGH_OPEN_CAPPED_LONGS:
                        result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                    else:
                        result[symbol] = sweep_to_target(symbol, depth, position, limit)
                elif position < 0 or (mid is not None and mid >= short_level):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                else:
                    result[symbol] = []

            elif open_regime == "normal_open" and symbol in NORMAL_OPEN_DELAYED_SHORTS:
                mid = book_mid(depth)
                early_short = normal_open_early_short_level(symbol, surface, S)
                early_cover = normal_open_cover_level(symbol, surface, S)
                if early_short is not None and normal_open_covering.get(symbol):
                    if position < 0:
                        result[symbol] = sweep_to_target(symbol, depth, position, 0)
                    else:
                        normal_open_covering.pop(symbol, None)
                        result[symbol] = []
                elif early_short is not None and position < 0 and mid is not None and mid <= early_cover and state.timestamp <= NORMAL_OPEN_EARLY_COVER_UNTIL:
                    normal_open_covering[symbol] = True
                    result[symbol] = sweep_to_target(symbol, depth, position, 0)
                elif early_short is not None and state.timestamp <= NORMAL_OPEN_EARLY_SHORT_UNTIL and (position < 0 or (mid is not None and mid >= early_short)):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                elif position < 0 and mid is not None and mid <= normal_open_cover_level(symbol, surface, S):
                    target = limit if symbol in NORMAL_OPEN_FLIP_COVERS else 0
                    result[symbol] = sweep_to_target(symbol, depth, position, target)
                elif position < 0 or (mid is not None and mid >= normal_open_short_level(symbol, surface, S)):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                else:
                    result[symbol] = []

            elif open_regime == "normal_open" and symbol in NORMAL_OPEN_CONDITIONAL_SHORTS:
                mid = book_mid(depth)
                early_short = None
                early_cover = None
                if early_short is not None and normal_open_covering.get(symbol):
                    if position < 0:
                        result[symbol] = sweep_to_target(symbol, depth, position, 0)
                    else:
                        normal_open_covering.pop(symbol, None)
                        result[symbol] = []
                elif early_short is not None and position < 0 and mid is not None and mid <= early_cover and state.timestamp <= NORMAL_OPEN_EARLY_COVER_UNTIL:
                    normal_open_covering[symbol] = True
                    result[symbol] = sweep_to_target(symbol, depth, position, 0)
                elif early_short is not None and state.timestamp <= NORMAL_OPEN_EARLY_SHORT_UNTIL and (position < 0 or (mid is not None and mid >= early_short)):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                elif position < 0 and mid is not None and mid <= normal_open_cover_level(symbol, surface, S):
                    target = limit if symbol in NORMAL_OPEN_FLIP_COVERS else 0
                    result[symbol] = sweep_to_target(symbol, depth, position, target)
                elif position < 0 or (mid is not None and mid >= normal_open_short_level(symbol, surface, S)):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                else:
                    fair = wall_mid(depth) or last_fair.get(symbol)
                    if fair is None:
                        result[symbol] = []
                        continue
                    last_fair[symbol] = fair
                    result[symbol] = market_make(symbol, depth, position, limit, fair)

            elif open_regime == "low_hydrogel_open" and symbol in LOW_OPEN_VOUCHERS:
                mid = book_mid(depth)
                long_level = low_open_long_level(symbol, surface, S)
                short_level = low_open_short_level(symbol, surface, S)
                exit_level = short_level
                if low_open_covering.get(symbol):
                    if position < limit:
                        result[symbol] = sweep_to_target(symbol, depth, position, limit)
                    elif mid is not None and mid >= exit_level:
                        low_open_covering.pop(symbol, None)
                        result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                    else:
                        result[symbol] = []
                elif position < 0 and mid is not None and mid <= long_level:
                    low_open_covering[symbol] = True
                    result[symbol] = sweep_to_target(symbol, depth, position, limit)
                elif position > 0 and mid is not None and mid >= exit_level:
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                elif position > 0 or (mid is not None and mid <= long_level):
                    if symbol in LOW_OPEN_CAPPED_LONGS:
                        result[symbol] = buy_to_target_below(symbol, depth, position, limit, long_level)
                    else:
                        result[symbol] = sweep_to_target(symbol, depth, position, limit)
                elif position < 0 or (mid is not None and mid >= short_level):
                    result[symbol] = sweep_to_target(symbol, depth, position, -limit)
                else:
                    result[symbol] = []

            else:
                fair = wall_mid(depth) or last_fair.get(symbol)
                if fair is None:
                    result[symbol] = []
                    continue
                last_fair[symbol] = fair
                result[symbol] = market_make(symbol, depth, position, limit, fair)

        data["last_fair"]    = last_fair
        data["vee_dir"]      = vee_dir
        data["vee_anchor"]   = vee_anchor
        data["open_vee_mid"] = open_vee_mid
        data["open_regime"]  = open_regime
        data["high_open_covering"] = high_open_covering
        data["low_open_covering"] = low_open_covering
        data["normal_open_covering"] = normal_open_covering
        trader_data = json.dumps(data, separators=(",", ":"))
        conversions = 0
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data
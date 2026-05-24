import json
import math

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
DELTA_ONE_LIMIT = 200
VOUCHER_LIMIT = 300
HYDROGEL = "HYDROGEL_PACK"
VELVETFRUIT = "VELVETFRUIT_EXTRACT"
VOUCHER_PREFIX = "VEV_"


def parse_strike(symbol):
    if not symbol.startswith(VOUCHER_PREFIX):
        return None
    try:
        return int(symbol[len(VOUCHER_PREFIX):])
    except ValueError:
        return None


def position_limit(symbol):
    if symbol == HYDROGEL or symbol == VELVETFRUIT:
        return DELTA_ONE_LIMIT
    if parse_strike(symbol) is not None:
        return VOUCHER_LIMIT
    return None


def best_bid_ask(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None, None
    return max(depth.buy_orders), min(depth.sell_orders)


def book_tick(depth):
    prices = sorted(set(depth.buy_orders) | set(depth.sell_orders))
    gaps = [right - left for left, right in zip(prices, prices[1:]) if right > left]
    return min(gaps) if gaps else 1


def wall_mid(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None
    wall_bid = max(depth.buy_orders.items(), key=lambda item: item[1])[0]
    wall_ask = max(depth.sell_orders.items(), key=lambda item: -item[1])[0]
    return (wall_bid + wall_ask) / 2


def book_mid(depth):
    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2


def book_microprice(depth):
    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return None
    bid_volume = depth.buy_orders[bid]
    ask_volume = -depth.sell_orders[ask]
    total_volume = bid_volume + ask_volume
    if total_volume <= 0:
        return (bid + ask) / 2
    return (ask * bid_volume + bid * ask_volume) / total_volume


def update_stats(stats, value):
    count = stats.get("n", 0) + 1
    mean = stats.get("mean", value)
    delta = value - mean
    mean += delta / count
    m2 = stats.get("m2", 0) + delta * (value - mean)
    return {"n": count, "mean": mean, "m2": m2}


def rolling_std(stats):
    count = stats.get("n", 0)
    if count <= 1:
        return 0
    return math.sqrt(max(0, stats.get("m2", 0) / count))


def sign(value):
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def fair_market_make(symbol, depth, position, limit):
    bid, ask = best_bid_ask(depth)
    fair = wall_mid(depth)
    if bid is None or ask is None or fair is None:
        return []

    tick = book_tick(depth)
    if symbol == HYDROGEL:
        fair -= (position / limit) * (ask - bid)
    buy_cap = max(0, limit - position)
    sell_cap = max(0, limit + position)
    orders = []

    for ask_price in sorted(depth.sell_orders):
        if buy_cap <= 0 or ask_price > fair - tick:
            break
        quantity = min(-depth.sell_orders[ask_price], buy_cap)
        if quantity > 0:
            orders.append(Order(symbol, ask_price, quantity))
            buy_cap -= quantity

    for bid_price in sorted(depth.buy_orders, reverse=True):
        if sell_cap <= 0 or bid_price < fair + tick:
            break
        quantity = min(depth.buy_orders[bid_price], sell_cap)
        if quantity > 0:
            orders.append(Order(symbol, bid_price, -quantity))
            sell_cap -= quantity

    quote_bid = min(bid + tick, int(fair))
    quote_ask = max(ask - tick, int(fair) + tick)
    if quote_bid >= quote_ask:
        quote_bid, quote_ask = bid, ask

    if buy_cap > 0:
        orders.append(Order(symbol, quote_bid, buy_cap))
    if sell_cap > 0:
        orders.append(Order(symbol, quote_ask, -sell_cap))
    return orders


def target_at_touch(symbol, depth, position, target):
    delta = target - position
    if delta > 0 and depth.sell_orders:
        return [Order(symbol, min(depth.sell_orders), delta)]
    if delta < 0 and depth.buy_orders:
        return [Order(symbol, max(depth.buy_orders), delta)]
    return []


def mean_revert_velvetfruit(symbol, depth, position, limit, data):
    bid, ask = best_bid_ask(depth)
    mid = book_microprice(depth)
    if bid is None or ask is None or mid is None:
        return [], data

    product_state = data.get(symbol, {})
    if "veto_anchor" not in product_state:
        if mid > 5280:
            product_state["veto_anchor"] = 5228
        elif mid > 5255:
            product_state["veto_anchor"] = 5245
        else:
            product_state["veto_anchor"] = 5242
    previous_mid = product_state.get("last_mid")
    if previous_mid is not None:
        product_state["return"] = update_stats(
            product_state.get("return", {}), mid - previous_mid
        )
    product_state["last_mid"] = mid
    mid_stats = update_stats(product_state.get("mid", {}), mid)
    spread_stats = update_stats(product_state.get("spread", {}), ask - bid)
    product_state["mid"] = mid_stats
    product_state["spread"] = spread_stats
    data[symbol] = product_state

    tick = book_tick(depth)
    band = rolling_std(mid_stats) + spread_stats["mean"] + tick
    fast_band = rolling_std(product_state.get("return", {})) + spread_stats["mean"] + tick
    target = 0
    fast_target = 0
    if mid > mid_stats["mean"] + band:
        target = -limit
    elif mid < mid_stats["mean"] - band:
        target = limit
    if mid > mid_stats["mean"] + fast_band:
        fast_target = -limit
    elif mid < mid_stats["mean"] - fast_band:
        fast_target = limit

    fast_sign = sign(fast_target)
    fast_counts = product_state.get("fast_counts", {"pos": 0, "neg": 0, "flat": 0})
    if fast_sign > 0:
        fast_counts["pos"] = fast_counts.get("pos", 0) + 1
    elif fast_sign < 0:
        fast_counts["neg"] = fast_counts.get("neg", 0) + 1
    else:
        fast_counts["flat"] = fast_counts.get("flat", 0) + 1
    product_state["fast_counts"] = fast_counts

    fast_regime = 0
    if fast_sign > 0 and fast_counts["pos"] > fast_counts["flat"] and fast_counts["pos"] > fast_counts["neg"]:
        fast_regime = 1
    elif fast_sign < 0 and fast_counts["neg"] > fast_counts["flat"] and fast_counts["neg"] > fast_counts["pos"]:
        fast_regime = -1

    product_state["target"] = target
    product_state["fast_target"] = fast_target
    product_state["fast_regime"] = fast_regime
    data[symbol] = product_state
    execution_target = target
    if not execution_target and fast_regime and sign(fast_target) == fast_regime:
        execution_target = fast_target
    if execution_target:
        anchor = product_state.get("veto_anchor", 5244)
        veto_band = product_state.get("anchor_veto_band", 0)
        if execution_target > 0 and mid > anchor + veto_band:
            execution_target = 0
        elif execution_target < 0 and mid < anchor - veto_band:
            execution_target = 0
    if execution_target:
        return target_at_touch(symbol, depth, position, execution_target), data
    return fair_market_make(symbol, depth, position, limit), data


def mean_revert_hydrogel(depth, position, limit, data):
    bid, ask = best_bid_ask(depth)
    mid = book_mid(depth)
    if bid is None or ask is None or mid is None:
        return [], data

    product_state = data.get(HYDROGEL, {})
    anchor = product_state.get("anchor", 9993)
    entry_band = product_state.get("entry_band", 36)
    exit_band = product_state.get("exit_band", 0)

    target = product_state.get("target", 0)
    if mid < anchor - entry_band:
        target = limit
    elif mid > anchor + entry_band:
        target = -limit
    elif abs(mid - anchor) <= exit_band:
        target = 0

    product_state["target"] = target
    data[HYDROGEL] = product_state
    if target:
        return target_at_touch(HYDROGEL, depth, position, target), data
    return fair_market_make(HYDROGEL, depth, position, limit), data


def voucher_surface_deltas(order_depths):
    points = []
    for symbol, depth in order_depths.items():
        strike = parse_strike(symbol)
        mid = book_mid(depth)
        if strike is not None and mid is not None:
            points.append((strike, symbol, mid))
    points.sort()

    deltas = {}
    for index, (strike, symbol, mid) in enumerate(points):
        if len(points) <= 1 or index == len(points) - 1:
            delta = 0
        elif index == 0:
            next_strike, _, next_mid = points[index + 1]
            delta = (mid - next_mid) / (next_strike - strike)
        else:
            prev_strike, _, prev_mid = points[index - 1]
            next_strike, _, next_mid = points[index + 1]
            delta = (prev_mid - next_mid) / (next_strike - prev_strike)
        deltas[symbol] = max(0, min(1, delta))
    return deltas


def voucher_follow_vee(symbol, depth, position, limit, data, deltas, underlying_mid):
    if underlying_mid is None:
        return []

    vee_state = data.get(VELVETFRUIT, {})
    vee_target = vee_state.get("target", 0)
    fast_target = vee_state.get("fast_target", 0)
    if (
        not vee_target
        and sign(fast_target) == vee_state.get("fast_regime", 0)
    ):
        vee_target = fast_target
    veto_anchor = vee_state.get("veto_anchor", 5244)
    if not vee_target and veto_anchor <= 5230:
        if underlying_mid > veto_anchor + 36:
            vee_target = -VOUCHER_LIMIT
        elif underlying_mid < veto_anchor - 36:
            vee_target = VOUCHER_LIMIT
    if underlying_mid > veto_anchor and vee_target > 0:
        vee_target = 0
    elif underlying_mid < veto_anchor and vee_target < 0:
        vee_target = 0
    delta = deltas.get(symbol, 0)
    if not vee_target or delta <= 0:
        positive_deltas = [value for value in deltas.values() if value > 0]
        max_delta = max(positive_deltas) if positive_deltas else 0
        if delta > 0 and delta >= max_delta:
            return fair_market_make(symbol, depth, position, limit)
        return []

    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return []
    top_clip = min(depth.buy_orders[bid], -depth.sell_orders[ask])
    if limit * delta * 5 < top_clip:
        return []

    target_size = limit
    direction = 1 if vee_target > 0 else -1
    return target_at_touch(symbol, depth, position, direction * target_size)


# ───────────────────────────── Trader ─────────────────────────────────────────
class Trader:
    def run(self, state: TradingState):
        data = json.loads(state.traderData) if state.traderData else {}
        voucher_deltas = voucher_surface_deltas(state.order_depths)
        underlying_mid = (
            book_mid(state.order_depths[VELVETFRUIT])
            if VELVETFRUIT in state.order_depths
            else None
        )
        result: dict[str, list[Order]] = {}
        handled = set()

        if VELVETFRUIT in state.order_depths:
            depth = state.order_depths[VELVETFRUIT]
            limit = position_limit(VELVETFRUIT)
            position = state.position.get(VELVETFRUIT, 0)
            result[VELVETFRUIT], data = mean_revert_velvetfruit(
                VELVETFRUIT, depth, position, limit, data
            )
            handled.add(VELVETFRUIT)

        for symbol, depth in state.order_depths.items():
            if symbol in handled:
                continue
            limit = position_limit(symbol)
            if limit is None:
                result[symbol] = []
                continue
            position = state.position.get(symbol, 0)
            if parse_strike(symbol) is not None:
                result[symbol] = voucher_follow_vee(
                    symbol,
                    depth,
                    position,
                    limit,
                    data,
                    voucher_deltas,
                    underlying_mid,
                )
            elif symbol == HYDROGEL:
                result[symbol], data = mean_revert_hydrogel(
                    depth, position, limit, data
                )
            else:
                result[symbol] = fair_market_make(symbol, depth, position, limit)

        conversions = 0
        trader_data = json.dumps(data, separators=(",", ":"))
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data
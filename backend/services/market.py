import math

def get_deal_score(
    buy_price: float,
    sell_price: float,
    observation_count: int
):
    if buy_price <= 0:
        return 0

    margin_pct = (sell_price - buy_price) / buy_price * 100

    if margin_pct < 5:
        return 0

    confidence = min(observation_count / 50, 1.0)

    #prevents outliers from dominating
    #basically makes score start to grow slower as margin increases
    #A 10% deal feels way better than a 5% deal but a 200% deal is NOT 20x better than a 10% deal
    score = score = math.log1p(max(margin_pct, 0)) * confidence * 10
    return round(score, 2)
def get_deal_score(
    buy_price: float,
    sell_price: float,
    observation_count: int
):
    if buy_price <= 0:
        return 0

    margin_pct = (sell_price - buy_price) / buy_price * 100

    confidence = min(observation_count / 50, 1.0)

    score = margin_pct * confidence

    return round(score, 2)
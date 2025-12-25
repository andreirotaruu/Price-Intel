


#define logic for getting the opportunity index

CATEGORY_FEES = {
    "gpu": 0.14,
    "console": 0.13,
}

WEIGHTS = {
    "roi": 50,
    "velocity": 0.1,
    "profit": 0.05
}


def classify_velocity(sold_count):
    if sold_count >= 50:
        return "FAST"
    elif sold_count >= 15:
        return "MEDIUM"
    else:
        return "SLOW"

def get_opportunity_index(buy_price, sell_price, sold_count, category):
    
    #get and calculate necessary stats
    fee_rate = CATEGORY_FEES.get(category, .15)
    fees = sell_price * fee_rate

    profit = sell_price - buy_price - fee_rate
    roi = profit / buy_price if buy_price else 0

    velocity = classify_velocity(sold_count)


    #calculate opportunity score while adding proper weights for values
    opportunity_score = (
        roi * WEIGHTS["roi"] +
        sold_count * WEIGHTS["velocity"] +
        profit * WEIGHTS["profit"]
    )

    #rule-outs
    if profit < 25:
        recommendation = "PASS"
    elif roi < 0.08:
        recommendation = "PASS"
    elif velocity == "SLOW":
        recommendation = "WAIT"
    else:
        recommendation = "BUY"

    return {
        "buy_price": round(buy_price, 2),
        "sell_price": round(sell_price, 2),
        "fees": round(fees, 2),
        "estimated_profit": round(profit, 2),
        "roi_percent": round(roi * 100, 2),
        "velocity": velocity,
        "recommendation": recommendation,
        "opportunity": opportunity_score
    }

    
    

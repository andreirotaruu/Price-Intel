


#define logic for getting the opportunity index

#to-do add score
def get_opportunity_index(buy_price, sell_price, sold_count, fee_rate = .14):
    
    fees = sell_price * fee_rate
    profit = sell_price - buy_price - fee_rate
    roi = profit / buy_price if buy_price else 0

    if profit <= 0:
        return "SKIP"
    

    if sold_count >= 15:
        velocity = "FAST"
    elif sold_count >= 5:
        velocity = "MEDIUM"
    else:
        velocity = "SLOW"

    
    if roi >= .15:
        return "BUY"
    elif roi >= .10 and velocity != 'slow':
        return "BUY"
    elif roi >= 0.05 and velocity == "FAST":
        return "CONSIDER"
    else:
        return "WAIT"
    
    

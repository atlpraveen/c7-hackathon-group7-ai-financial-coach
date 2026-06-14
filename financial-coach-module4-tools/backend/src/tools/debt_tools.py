from math import ceil

def calculate_simple_interest(balance, rate, years):
    return balance * (rate/100) * years

def avalanche_sort(debts):
    return sorted(debts, key=lambda x: x['rate'], reverse=True)

def snowball_sort(debts):
    return sorted(debts, key=lambda x: x['balance'])

def payoff_months(balance, monthly_payment):
    return ceil(balance / monthly_payment)

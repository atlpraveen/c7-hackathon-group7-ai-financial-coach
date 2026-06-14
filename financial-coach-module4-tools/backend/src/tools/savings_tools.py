def emergency_fund_target(monthly_expenses, months=6):
    return monthly_expenses * months

def monthly_savings_required(target_amount, months):
    return target_amount / months

def savings_rate(monthly_income, monthly_savings):
    return round((monthly_savings/monthly_income)*100,2)

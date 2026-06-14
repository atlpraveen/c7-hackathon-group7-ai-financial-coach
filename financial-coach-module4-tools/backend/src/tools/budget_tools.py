def categorize_expense(amount, category):
    return {'category': category, 'amount': amount}

def total_expenses(expenses):
    return sum(expenses)

def budget_surplus(income, expenses):
    return income - expenses

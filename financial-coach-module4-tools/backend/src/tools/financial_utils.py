def percentage(part,total):
    if total == 0:
        return 0
    return round((part/total)*100,2)

def currency(value):
    return f"${value:,.2f}"

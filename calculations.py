import pandas as pd
import numpy as np

def calculate_projection(
    start_capital,
    years,
    income_return,
    growth_return,
    tax_rate,
    fee_rate,
    drawdown_schedule,
    subtract_fees=True,
    p1_age=None,
    p2_age=None
):
    """
    Core function to project portfolio balance over time.
    
    Parameters:
    - start_capital: Initial amount of money.
    - years: List or array of years.
    - income_return: Annual income return rate (e.g., 0.045).
    - growth_return: Annual growth return rate (e.g., 0.005).
    - tax_rate: Tax rate on income return.
    - fee_rate: Annual fee rate.
    - drawdown_schedule: List/Array of amount to withdraw each year.
    - subtract_fees: Boolean, if True fees are deducted from balance.
    
    Returns:
    - DataFrame containing the projection year by year.
    """
    records = []
    balance = start_capital
    
    # Support per-year tax schedules: tax_rate can be a float or a list
    if isinstance(tax_rate, (list, tuple)):
        tax_schedule = tax_rate
    else:
        tax_schedule = None  # Use uniform rate
    
    for i, year in enumerate(years):
        # 1. Calculate Fees (based on opening balance)
        fees = balance * fee_rate
        
        # 2. Calculate Returns
        year_tax_rate = tax_schedule[i] if tax_schedule and i < len(tax_schedule) else (tax_rate if not tax_schedule else 0)
        inc_amt = balance * income_return
        tax_amt = inc_amt * year_tax_rate
        inc_net = inc_amt - tax_amt
        growth_amt = balance * growth_return
        
        # 3. Calculate Pre-Drawdown Closing
        # Balance + Growth + Net Income
        pre_drawdown_balance = balance + growth_amt + inc_net
        
        # 4. Drawdown
        drawdown = drawdown_schedule[i] if i < len(drawdown_schedule) else 0
        
        # 5. Final Closing
        if subtract_fees:
            closing_balance = pre_drawdown_balance - drawdown - fees
        else:
            closing_balance = pre_drawdown_balance - drawdown
            
        record = {
            "Year": year,
            "Opening Balance": balance,
            "Income Return": inc_amt,
            "Tax": tax_amt,
            "Income Net": inc_net,
            "Growth": growth_amt,
            "Fees": fees,
            "Drawdown": drawdown,
            "Closing Balance": closing_balance,
            "P1 Age": (p1_age + i) if p1_age is not None else None,
            "P2 Age": (p2_age + i) if p2_age is not None else None
        }
        records.append(record)
        
        # Update balance for next year
        balance = closing_balance
        
    return pd.DataFrame(records)

def solve_required_capital(
    years,
    income_return,
    growth_return,
    tax_rate,
    fee_rate,
    drawdown_schedule,
    subtract_fees=True
):
    """
    Calculates the starting capital required to survive the given drawdown schedule.
    """
    low = 0.0
    # Upper bound guess: Sum of drawdowns * 2 (safe buffer)
    # If drawdowns are 0 (e.g., funded by growth?), default to something small
    total_drawdown = sum(drawdown_schedule)
    high = total_drawdown * 20 if total_drawdown > 0 else 1000000.0
    
    required_capital = high
    
    # Binary search
    for _ in range(100):
        mid = (low + high) / 2
        
        # Run projection logic inline for speed or call function
        # Calling function is cleaner
        df = calculate_projection(mid, years, income_return, growth_return, tax_rate, fee_rate, drawdown_schedule, subtract_fees)
        final_balance = df.iloc[-1]["Closing Balance"]
        
        if final_balance >= -0.01: # allow slightly negative due to float precision, essentially 0
            required_capital = mid
            high = mid
        else:
            low = mid
            
    return required_capital

def calculate_income_portfolio(
    start_year: int,
    duration_years: int,
    initial_drawdown: float,
    inflation: float,
    income_return: float,
    growth_return: float,
    tax_rate: float,
    fee_rate: float,
    p1_age: int,
    p2_age: int,
    defer_years: int = 0,
    start_capital: float = None
):
    """
    Calculates the Income Portfolio (fees subtracted, inflating drawdown).
    Supports 'Deferral Phase' where capital grows but no drawdown occurs.
    """
    total_years = defer_years + duration_years
    years = [start_year + i for i in range(total_years)]
    
    # 1. Build Drawdown List
    drawdowns = []
    
    # Phase A: Deferral (Zero Drawdown)
    for i in range(defer_years):
        drawdowns.append(0.0)
        
    # Phase B: Active Drawdown (Inflated)
    # Inflation starts from the FIRST YEAR OF DRAWDOWN (Face Value Calculation).
    # If user asks for $60k in Stage 3, they mean $60k in the first year of Stage 3.
    for i in range(duration_years):
        inflated_amount = initial_drawdown * ((1 + inflation) ** i)
        drawdowns.append(inflated_amount)
    
    if start_capital is None:
        start_capital = solve_required_capital(years, income_return, growth_return, tax_rate, fee_rate, drawdowns, subtract_fees=True)
        
    df = calculate_projection(start_capital, years, income_return, growth_return, tax_rate, fee_rate, drawdowns, subtract_fees=True, p1_age=p1_age, p2_age=p2_age)
    
    # Format or ensure columns exist for the detailed table (they are already created in calculate_projection)
    
    # Format or ensure columns exist for the detailed table (they are already created in calculate_projection)
    # columns: Year, Opening Balance, Income Return, Tax, Income Net, Growth, Fees, Drawdown, Closing Balance
    
    return start_capital, df.to_dict(orient="records")


def calculate_asset_portfolio(
    start_year: int,
    duration_years: int,
    purchase_value: float,
    replacement_cycle: int, # Years between replacements
    annual_holding_cost: float,
    trade_in_value: float, # Value of old asset when sold
    inflation: float, # Inflation for purchase price and holding cost
    income_return: float,
    growth_return: float,
    tax_rate: float,
    fee_rate: float,
    p1_age: int,
    p2_age: int,
    defer_years: int = 0,
    sell_at_end: bool = False,
    start_capital: float = None
):
    """
    Calculates Asset Portfolio (Car, Boat, etc) with replacement cycles.
    Fees NOT subtracted from balance.
    returns: start_capital, list of dicts with detailed columns.
    """
    years = [start_year + i for i in range(duration_years + defer_years)]
    drawdowns = []
    
    # Detailed tracking lists
    purchase_costs = []
    trade_in_values = []
    holding_costs = []
    
    # 1. Deferral Phase
    for i in range(defer_years):
        drawdowns.append(0.0)
        purchase_costs.append(0.0)
        trade_in_values.append(0.0)
        holding_costs.append(0.0)
    
    # 2. Active Phase
    for i in range(duration_years):
        # Current costs adjusted for inflation
        inflated_holding = annual_holding_cost * ((1 + inflation) ** i)
        inflated_purchase = purchase_value * ((1 + inflation) ** i)
        inflated_trade_in = trade_in_value * ((1 + inflation) ** i)
        
        current_purchase = 0.0
        current_trade_in = 0.0
        current_holding = inflated_holding
        
        cash_flow = current_holding
        
        # Purchase Logic
        # 1. Initial Purchase at Year 0
        if i == 0:
            current_purchase = inflated_purchase
            cash_flow += current_purchase
        
        # 2. Replacement Cycles (e.g. Year 10, 20...)
        elif replacement_cycle > 0 and i % replacement_cycle == 0:
            # Sell Old (Credit)
            current_trade_in = inflated_trade_in
            cash_flow -= current_trade_in
            # Buy New (Debit)
            current_purchase = inflated_purchase
            cash_flow += current_purchase

        # 3. Sell at End Logic
        # If this is the LAST year and sell_at_end is True, we trigger a sale (Trade-in value)
        # We only do this if a replacement didn't ALREADY happen this year (to avoid double counting)
        if sell_at_end and i == (duration_years - 1):
             # Check if we didn't just sell it in step 2
             just_sold = (replacement_cycle > 0 and i % replacement_cycle == 0)
             if not just_sold:
                 current_trade_in += inflated_trade_in
                 cash_flow -= inflated_trade_in

        drawdowns.append(cash_flow)
        
        # Store for record
        purchase_costs.append(current_purchase)
        trade_in_values.append(current_trade_in)
        holding_costs.append(current_holding)
        
    if start_capital is None:
        # For required capital validation, we ignore the INFLOWS from trade-ins/sales
        # because we cannot use future sale proceeds to fund current holding costs.
        # We solve for the capital needed to cover Purchase + Holding Costs only.
        
        # Create a "cost only" drawdown list
        cost_only_drawdowns = []
        for d in drawdowns:
            if d > 0:
                cost_only_drawdowns.append(d)
            else:
                cost_only_drawdowns.append(0) # Ignore inflow for funding requirement
                
        start_capital = solve_required_capital(years, income_return, growth_return, tax_rate, fee_rate, cost_only_drawdowns, subtract_fees=False)
        
    df = calculate_projection(start_capital, years, income_return, growth_return, tax_rate, fee_rate, drawdowns, subtract_fees=False, p1_age=p1_age, p2_age=p2_age)
    
    # Add Detailed Columns
    # Age columns now added by calculate_projection
    df["Purchase Cost"] = purchase_costs
    df["Trade-In Value"] = trade_in_values
    df["Holding Cost"] = holding_costs
    
    return start_capital, df.to_dict(orient="records")




def calculate_holiday_portfolio(
    start_year: int,
    duration_years: int,
    daily_cost_total: float,
    days_per_trip: int,
    trip_frequency_years: int,
    inflation: float,
    income_return: float,
    growth_return: float,
    tax_rate: float,
    
    fee_rate: float,
    defer_years: int = 0,
    start_capital: float = None,
    p1_age: int = None,
    p2_age: int = None
):
    """
    Calculates Holiday Portfolio.
    Fees NOT subtracted.
    Drawdown = (DailyCost * Days) every X years, inflated.
    """
    years = [start_year + i for i in range(duration_years + defer_years)]
    drawdowns = []
    
    # Deferral
    for i in range(defer_years):
        drawdowns.append(0.0)

    base_cost_per_trip = daily_cost_total * days_per_trip
    
    for i in range(duration_years):
        # Inflate the cost
        current_year_cost = base_cost_per_trip * ((1 + inflation) ** i)
        
        # Trip Logic
        if trip_frequency_years > 0 and i % trip_frequency_years == 0:
            drawdowns.append(current_year_cost)
        else:
            drawdowns.append(0)

    if start_capital is None:
        start_capital = solve_required_capital(years, income_return, growth_return, tax_rate, fee_rate, drawdowns, subtract_fees=False)
        
    df = calculate_projection(start_capital, years, income_return, growth_return, tax_rate, fee_rate, drawdowns, subtract_fees=False, p1_age=p1_age, p2_age=p2_age)
    return start_capital, df.to_dict(orient="records")


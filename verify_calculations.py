from calculations import calculate_income_portfolio, calculate_asset_portfolio, calculate_holiday_portfolio

def verify():
    print("--- Verifying Income Portfolio ---")
    capital, df = calculate_income_portfolio(
        start_year=2026,
        duration_years=6, 
        initial_drawdown=80000,
        inflation=0.03,
        income_return=0.045, # Conservative
        growth_return=0.005,
        tax_rate=0.15,
        fee_rate=0.011,
        p1_age=65,
        p2_age=62
    )
    print(f"Calculated Capital: {capital:,.2f}")
    
    print("--- Verifying Deferred Income Portfolio (Stage 2) ---")
    # Defer 10 years, then draw $80k for 10 years.
    # Start Capital should be LESS than immediate start because of 10y growth.
    cap_def, df_def = calculate_income_portfolio(
        start_year=2026,
        duration_years=10, 
        initial_drawdown=80000,
        inflation=0.03,
        income_return=0.045, # Conservative
        growth_return=0.005,
        tax_rate=0.15,
        fee_rate=0.011,
        p1_age=65,
        p2_age=62,
        defer_years=10
    )
    print(f"Calculated Deferred Capital (10y Defer, 10y Draw): {cap_def:,.2f}")
    
    # Check first year (should be 0 drawdown)
    print(f"Year 0 Drawdown: {df_def[0]['Drawdown']}")
    
    # Check 11th year (index 10) (Should be EXACTLY initial_drawdown because we reset inflation clock)
    first_paid = df_def[10]['Drawdown']
    print(f"Year 11 Drawdown (First Payout): {first_paid:,.2f} (Target: 80,000.00)")
    
    if abs(first_paid - 80000) < 1.0:
        print("SUCCESS: Inflation correctly reset for deferred stage.")
    else:
        print("FAILURE: Inflation logic incorrectly applied to deferred years.")

    
    print("\n--- Verifying Car Portfolio ---")
    cap_car, _ = calculate_asset_portfolio(
        start_year=2026,
        duration_years=27, 
        purchase_value=50000,
        replacement_cycle=17, 
        annual_holding_cost=3300,
        trade_in_value=10000,
        inflation=0.03,
        income_return=0.035,
        growth_return=0.045,
        tax_rate=0.15,
        fee_rate=0.011,
        p1_age=65,
        p2_age=62
    )

    print(f"Calculated Car Capital (Cycle 17, 3% Inf): {cap_car:,.2f}")
    
    print("\n--- Verifying Car Portfolio (Sell at End) ---")
    # Using the prompt values: 30y, $50k buy, 10y cycle, $10k trade, $3300 holding, 3% inf
    cap_car_end, df_car_end = calculate_asset_portfolio(
        start_year=2026,
        duration_years=30, # 30 years
        purchase_value=50000,
        replacement_cycle=10, 
        annual_holding_cost=3300,
        trade_in_value=10000,
        inflation=0.03,
        income_return=0.035, # Balanced
        growth_return=0.045,
        tax_rate=0.15,
        fee_rate=0.011,
        p1_age=65,
        p2_age=62,
        sell_at_end=True
    )
    print(f"Calculated Car Capital (30y, Sell at End): {cap_car_end:,.2f}")
    # Check last year for trade-in value
    last_year = df_car_end[-1]
    print(f"Last Year Trade-In Value: {last_year['Trade-In Value']:,.2f}")
    print(f"Last Year Drawdown: {last_year['Drawdown']:,.2f}")


    print("\n--- Verifying Holiday Portfolio ---")
    # Target: ~115,568
    # Cost 10,500/yr (750 * 14)
    # 10 Years? 
    # CSV "Domestic Holidays Rows 50-70"
    # Row 64: "if by 2026 I need 115568...".
    # Row 49: Finish Year 2042 ? (Stage length 10 years? Wait, Stage 2?)
    # Row 48: "Stage length 10". Start 6.
    # Ah, the sheet has "Income Stage 1" and "Stage 2".
    # But for "Holiday", it probably has a duration.
    # User's CSV dump "Domestic Holidays Row 30..."
    # Does not explicitly show Duration.
    # But usually these are 10-20 years.
    # Let's try to solve for 10 years duration (2026-2035) and see if we get ~115k.
    # Or 15 years?
    
    cap_hol, df_hol = calculate_holiday_portfolio(
        start_year=2026,
        duration_years=10, 
        daily_cost_total=750,
        days_per_trip=14,
        trip_frequency_years=1, # Annual
        inflation=0.03, # Added Inflation
        income_return=0.035,
        growth_return=0.045,
        tax_rate=0.15,
        fee_rate=0.011 
    )
    print(f"Calculated Holiday Capital (10 Years, 3% Inf): {cap_hol:,.2f}")
    
    cap_hol_15, _ = calculate_holiday_portfolio(
        start_year=2026,
        duration_years=15, 
        daily_cost_total=750,
        days_per_trip=14,
        trip_frequency_years=1, 
        inflation=0.03,
        income_return=0.035,
        growth_return=0.045,
        tax_rate=0.15,
        fee_rate=0.011
    )
    print(f"Calculated Holiday Capital (15 Years, 3% Inf): {cap_hol_15:,.2f}")


    
if __name__ == "__main__":
    verify()

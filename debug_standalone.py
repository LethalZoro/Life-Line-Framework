import json
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from calculations import calculate_income_portfolio, calculate_asset_portfolio, calculate_holiday_portfolio

# --- Models ---
class CompProfile(BaseModel):
    p1_name: str
    p1_dob: str
    p2_name: str
    p2_dob: str

class CompAssumptions(BaseModel):
    income_return: float
    growth_return: float
    tax_rate: float
    inflation: float
    fee_load: float

class CompItem(BaseModel):
    name: str
    income: Optional[float] = 0
    start: Optional[int] = 0
    end: Optional[int] = 0
    cost: Optional[float] = 0
    cycle: Optional[int] = 0
    holding: Optional[float] = 0
    resale: Optional[float] = 0
    type: Optional[str] = None
    funding_start: Optional[int] = None
    apply_inflation: Optional[bool] = True

class CompInput(BaseModel):
    profile: CompProfile
    assumptions: CompAssumptions
    incomes: List[CompItem]
    cars: List[CompItem]
    assets: List[CompItem]
    travel: List[CompItem]
    medical: dict

# --- Logic (Copied from main.py) ---
def process_scenario(data: CompInput):
    p1_birth_year = int(data.profile.p1_dob.split("-")[0]) 
    current_year = 2026
    p1_current_age = current_year - p1_birth_year
    
    results = [] 
    asm = data.assumptions
    
    def make_chart_data(df):
        return {
            "labels": [str(d['Year']) for d in df],
            "balance": [d['Closing Balance'] for d in df],
            "drawdown": [d['Drawdown'] for d in df],
            "table_data": df 
        }

    for item in data.incomes:
        duration = item.end - item.start
        fund_age = item.funding_start if item.funding_start is not None else p1_current_age
        deferral = item.start - fund_age
        if deferral < 0: deferral = 0
        funding_year = current_year + (fund_age - p1_current_age)
        
        cap, df_list = calculate_income_portfolio(
            start_year=funding_year,
            duration_years=duration,
            initial_drawdown=item.income,
            inflation=asm.inflation / 100,
            income_return=asm.income_return / 100,
            growth_return=asm.growth_return / 100,
            tax_rate=asm.tax_rate / 100,
            fee_rate=asm.fee_load / 100,
            p1_age=fund_age, 
            p2_age=fund_age, 
            defer_years=deferral
        )
        pv = cap
        delay_from_now = fund_age - p1_current_age
        if delay_from_now > 0:
            pv = cap * ((1.0 + (asm.growth_return/100)) ** -delay_from_now)

        results.append({
            "title": f"Income Stream: {item.name}",
            "capital_required": pv,
            "chart_data": make_chart_data(df_list),
            "details": f"..."
        })

    for item in data.cars:
        duration = 30 
        fund_age = item.funding_start if item.funding_start is not None else p1_current_age
        funding_year = current_year + (fund_age - p1_current_age)
        eff_inflation = (asm.inflation / 100) if item.apply_inflation else 0.0
        
        asset_start_year = current_year + (item.start - p1_current_age)
        
        cap, df_list = calculate_asset_portfolio(
            start_year=asset_start_year,
            duration_years=duration,
            purchase_value=item.cost,
            replacement_cycle=item.cycle,
            annual_holding_cost=item.holding,
            trade_in_value=item.cost * 0.3, 
            inflation=eff_inflation, 
            income_return=asm.income_return / 100,
            growth_return=asm.growth_return / 100,
            tax_rate=asm.tax_rate / 100,
            fee_rate=asm.fee_load / 100,
            p1_age=item.start,
            p2_age=0
        )
        
        years_to_grow = item.start - fund_age
        if years_to_grow > 0:
             cap_at_fund_time = cap * ((1.0 + (asm.growth_return/100)) ** -years_to_grow)
        else:
             cap_at_fund_time = cap
             
        delay_to_fund = fund_age - p1_current_age
        pv = cap_at_fund_time
        if delay_to_fund > 0:
            pv = cap_at_fund_time * ((1.0 + (asm.growth_return/100)) ** -delay_to_fund)

        results.append({
            "title": f"Vehicle: {item.name}",
            "capital_required": pv,
            "chart_data": make_chart_data(df_list),
            "details": f"..."
        })

    total_capital = sum(r['capital_required'] for r in results)
    return results, total_capital

# --- Test Data ---
raw_data = {
    "profile": { "p1_name": "Test", "p1_dob": "1980-01-01", "p2_name": "Test2", "p2_dob": "1982-01-01" },
    "assumptions": { "income_return": 3.5, "growth_return": 4.5, "tax_rate": 15, "inflation": 3, "fee_load": 1.1 },
    "incomes": [ {"name": "Stage 1", "income": 80000, "start": 60, "end": 70} ],
    "cars": [ {"name": "Car 1", "cost": 60000, "start": 60, "cycle": 5, "holding": 2500, "apply_inflation": True} ],
    "assets": [], "travel": [], "medical": {}
}

if __name__ == "__main__":
    try:
        obj = CompInput(**raw_data)
        res, total = process_scenario(obj)
        print(f"Success! Total Capital: {total}")
    except Exception as e:
        import traceback
        traceback.print_exc()

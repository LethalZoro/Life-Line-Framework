import requests
import json
from datetime import date

url = "http://localhost:8000/api/analyze"

payload = {
    "profile": {
        "partner1_name": "Alex",
        "partner1_dob": "1965-05-15",
        "partner2_name": "Sam",
        "partner2_dob": "1968-08-20",
        "partner1_retirement_age": 65,
        "partner2_retirement_age": 60,
        "wants": ["Travel Europe", "New Boat"],
        "dont_wants": ["Run out of money", "Be a burden"],
        "barriers": [
            {"description": "Fear of market crash", "impact_percentage": 80},
            {"description": "Health concerns", "impact_percentage": 50}
        ],
        "eulogy_partner": "He was kind.",
        "eulogy_child": "He was present.",
        "eulogy_friend": "He was generous."
    },
    "context": {
        "total_investable": 1250000,
        "super_balance": 800000,
        "cash_savings": 150000,
        "shares_investments": 300000,
        "investment_properties": 0,
        "other_assets": 0
    },
    "lifestyle": {
        "life_stages": [
            {"name": "Early Active", "start_age": 60, "end_age": 70, "annual_income": 100000},
            {"name": "Late Passive", "start_age": 70, "end_age": 90, "annual_income": 80000}
        ],
        "cars": [
             {"name": "Toyota Prado", "purchase_value": 70000, "start_age": 60, "replacement_cycle": 10, "holding_cost": 2000, "end_age": 80}
        ],
        "travel_domestic": {
            "name": "Local Trips", "duration_days": 10, "cost_accom_daily": 300, 
            "cost_transport_daily": 0, "cost_food_daily": 100, "cost_fun_daily": 100,
            "start_age": 60, "end_age": 80, "flight_cost_per_person": 0, "seasonality": "Peak"
        },
        "travel_international": {
            "name": "Europe", "duration_days": 20, "cost_accom_daily": 500,
            "cost_transport_daily": 0, "cost_food_daily": 200, "cost_fun_daily": 200,
             "start_age": 65, "end_age": 75, "flight_cost_per_person": 3000, "seasonality": "Peak"
        },
        "boat": {
            "name": "Fishing Boat", "purchase_value": 40000, "purchase_timing": 62,
            "holding_cost": 3000, "disposal_timing": 70, "disposal_value": 10000
        },
        "medical_expenses": {
             "name": "Health Ins", "purchase_value": 5000, "purchase_timing": 60,
             "holding_cost": 0, "disposal_timing": 95, "disposal_value": 0
        },
        "health_buffer": {
             "name": "Health Buffer", "purchase_value": 5000, "purchase_timing": 60,
             "holding_cost": 0, "disposal_timing": 100, "disposal_value": 0
        },
        "emergency_reserve": 50000
    },
    "big_rocks": {
        "primary_residence": {
            "current_value": 1500000, "outstanding_mortgage": 0, "holding_cost": 8000,
            "strategy": "Keep", "dwelling_type": "House", "location_type": "Metro", "growth_assumption": "Average"
        },
        "aged_care": {"entry_age": 85, "rad_deposit": 550000, "daily_fees": 0}
    },
    "family": {},
    "assumptions": {
        "general_inflation": 3.0,
        "education_inflation": 5.0,
        "car_depreciation": 15.0,
        "fee_load": 1.1,
        "risk_profile": "Balanced"
    }
}

try:
    print("Sending Request to /api/analyze...")
    resp = requests.post(url, json=payload, timeout=120)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("Success!")
        print(json.dumps(data, indent=2))
    else:
        print("Error:", resp.text)
except Exception as e:
    print(f"Exception: {e}")

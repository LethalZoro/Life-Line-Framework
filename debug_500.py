from main import process_scenario, CompInput, CompProfile, CompAssumptions, CompItem

data = {
    "profile": {
        "p1_name": "Test",
        "p1_dob": "1980-01-01",
        "p2_name": "Test2",
        "p2_dob": "1982-01-01"
    },
    "assumptions": {
        "income_return": 3.5,
        "growth_return": 4.5,
        "tax_rate": 15,
        "inflation": 3,
        "fee_load": 1.1
    },
    "incomes": [
        {"name": "Stage 1", "income": 80000, "start": 60, "end": 70}
    ],
    "cars": [
        {"name": "Car 1", "cost": 60000, "start": 60, "cycle": 5, "holding": 2500, "apply_inflation": True}
    ],
    "assets": [],
    "travel": [],
    "medical": {}
}

try:
    obj = CompInput(**data)
    process_scenario(obj)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

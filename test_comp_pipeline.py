import requests
import json

url = "http://localhost:8000/api/generate_comprehensive_report"

payload = {
    "profile": {
        "p1_name": "Test User",
        "p1_dob": "1980-01-01",
        "p2_name": "Test Partner",
        "p2_dob": "1982-01-01"
    },
    "assumptions": {
        "income_return": 3.5,
        "growth_return": 4.5,
        "tax_rate": 15.0,
        "inflation": 3.0,
        "fee_load": 1.1
    },
    "incomes": [
        {"name": "Stage 1", "income": 80000, "start": 60, "end": 70},
        {"name": "Stage 2", "income": 60000, "start": 70, "end": 85}
    ],
    "cars": [
        {"name": "Primary Car", "cost": 50000, "start": 60, "cycle": 5, "holding": 2000}
    ],
    "assets": [
        {"name": "Boat", "cost": 100000, "start": 65, "end": 75, "holding": 5000, "resale": 30000}
    ],
    "travel": [
         {"name": "Europe Trip", "cost": 20000, "start": 60, "end": 70, "type": "annual"}
    ],
    "medical": {
        "cost": 5000, "start": 75, "end": 95
    }
}

try:
    print("Sending POST request...")
    r = requests.post(url, json=payload)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        print("Success! Response length:", len(r.text))
        if "Life Plan Strategy" in r.text:
            print("Found 'Life Plan Strategy' in response.")
        else:
            print("WARNING: Expected title not found in response.")
    else:
        print("Error:", r.text)
except Exception as e:
    print("Exception:", e)

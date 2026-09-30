import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

CASES = [
    {
        "diagnosis": "Community-acquired pneumonia",
        "symptoms": ["Fever, cough, and shortness of breath",
                     "Fever, productive cough, and chest discomfort"],
        "procedure": "Chest X-ray",
        "treatment": "Received treatment for pneumonia and improved during admission",
        "medication": "Discharge medications as prescribed for pneumonia",
        "follow_up": "Follow up with a healthcare professional in 7 days",
    },
    {
        "diagnosis": "Acute gastroenteritis",
        "symptoms": ["Diarrhea, nausea, and abdominal cramps",
                     "Vomiting and loose stools"],
        "procedure": "Clinical assessment",
        "treatment": "Received supportive care and improved during admission",
        "medication": "Discharge medications as prescribed",
        "follow_up": "Follow up with a healthcare professional if symptoms continue",
    },
    {
        "diagnosis": "Urinary tract infection",
        "symptoms": ["Painful urination and frequent urination",
                     "Frequent urination and lower abdominal discomfort"],
        "procedure": "Urine test",
        "treatment": "Received treatment for urinary tract infection and improved",
        "medication": "Discharge medications as prescribed for the infection",
        "follow_up": "Follow up with a healthcare professional in 7 days",
    },
]

def make_record(number):
    case = random.choice(CASES)
    age = random.randint(18, 90)
    gender = random.choice(["Female", "Male"])
    admission = date(2026, 1, 1) + timedelta(days=random.randint(0, 250))
    stay = random.randint(1, 7)
    discharge = admission + timedelta(days=stay)

    summary = (
        f"A {age}-year-old {gender.lower()} was admitted with "
        f"{case['symptoms'][0].lower()}. The recorded diagnosis was "
        f"{case['diagnosis']}. The patient received care and improved "
        f"during the stay, then was discharged in stable condition. "
        f"{case['follow_up']}."
    )

    return {
        "patient_id": f"SYN{number:06d}",
        "age": age,
        "gender": gender,
        "admission_date": admission.isoformat(),
        "discharge_date": discharge.isoformat(),
        "length_of_stay": stay,
        "diagnosis": case["diagnosis"],
        "symptoms": case["symptoms"][0],
        "comorbidities": "None recorded",
        "procedures": case["procedure"],
        "treatment_summary": case["treatment"],
        "discharge_condition": "Stable",
        "discharge_medications": case["medication"],
        "follow_up": case["follow_up"],
        "discharge_summary": summary,
    }

FIELDS = [
    "patient_id", "age", "gender", "admission_date", "discharge_date",
    "length_of_stay", "diagnosis", "symptoms", "comorbidities",
    "procedures", "treatment_summary", "discharge_condition",
    "discharge_medications", "follow_up", "discharge_summary",
]

# Generate 20 valid records.
records = [make_record(i) for i in range(1, 21)]
with (OUTPUT_DIR / "synthetic_discharge_data.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(records)

# Keep deliberately faulty examples separate from the valid dataset.
invalid_records = [
    {
        **records[0],
        "patient_id": "TEST000001",
        "age": -8,
        "discharge_date": "2025-01-01",
        "length_of_stay": 9,
        "symptoms": "Ankle pain only",
        "discharge_summary": "TEST ONLY: deliberately invalid record.",
    },
    {
        **records[1],
        "patient_id": "TEST000002",
        "age": 999,
        "length_of_stay": 0,
        "discharge_summary": "TEST ONLY: deliberately invalid record.",
    },
]
with (OUTPUT_DIR / "invalid_test_cases.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(invalid_records)

print(f"Created {len(records)} valid records in data/synthetic_discharge_data.csv")
print(f"Created {len(invalid_records)} test records in data/invalid_test_cases.csv")
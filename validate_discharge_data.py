import csv
from datetime import date

csv_path = "data/synthetic_discharge_data.csv"

with open(csv_path, newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        errors = []

        age = int(row["age"])
        admission = date.fromisoformat(row["admission_date"])
        discharge = date.fromisoformat(row["discharge_date"])
        stay = int(row["length_of_stay"])

        if not 0 <= age <= 120:
            errors.append("age is outside 0–120")

        if discharge < admission:
            errors.append("discharge is before admission")
        elif (discharge - admission).days != stay:
            errors.append("length of stay does not match dates")

        if (
            row["diagnosis"] == "Community-acquired pneumonia"
            and "cough" not in row["symptoms"].lower()
        ):
            errors.append("pneumonia symptoms do not include cough")

        if errors:
            print(f'{row["patient_id"]} INVALID: {"; ".join(errors)}')
        else:
            print(f'{row["patient_id"]} VALID')
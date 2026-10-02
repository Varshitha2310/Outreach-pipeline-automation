"""Creates a SAMPLE (fictional) outreach tracker, like one used for sponsor/partner outreach.
Run: python generate_sample_data.py
Output: data/outreach_tracker.csv
All company names are fictional.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(7)
today = date.today()

sectors = ["FinTech", "EdTech", "FMCG", "Telecom", "Fashion", "Food & Beverage", "Gaming", "Travel"]
stages = ["Lead Identified", "Contacted", "Pitch Sent", "Negotiation", "Closed Won", "Closed Lost"]
stage_p = [0.12, 0.22, 0.22, 0.14, 0.18, 0.12]
owners = ["Aarav", "Diya", "Kabir", "Meera"]
prefixes = ["Nova", "Apex", "Bright", "Zenith", "Orbit", "Pulse", "Vertex", "Lumen", "Cobalt", "Ember"]
suffixes = ["Pay", "Learn", "Foods", "Mobile", "Wear", "Drinks", "Play", "Trips", "Labs", "Works"]

rows = []
used = set()
while len(rows) < 40:
    name = f"{rng.choice(prefixes)}{rng.choice(suffixes)}"
    if name in used:
        continue
    used.add(name)
    stage = rng.choice(stages, p=stage_p)
    last_contact = today - timedelta(days=int(rng.integers(0, 25)))
    followup = last_contact + timedelta(days=int(rng.integers(3, 10)))
    value = int(rng.choice([25000, 50000, 75000, 100000, 150000, 250000]))
    rows.append([name, rng.choice(sectors), stage, rng.choice(owners),
                 last_contact.isoformat(), followup.isoformat(), value])

df = pd.DataFrame(rows, columns=["company", "sector", "stage", "owner",
                                 "last_contact_date", "next_followup_date", "expected_value_inr"])
df.to_csv("data/outreach_tracker.csv", index=False)
print(f"Saved {len(df)} leads to data/outreach_tracker.csv")

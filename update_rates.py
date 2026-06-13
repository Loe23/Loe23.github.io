import json
from datetime import datetime

# Données actuelles – à remplacer plus tard par un scraping réel
services = [
    {"name": "Sendwave", "fee": 3.00, "rate": 655.96, "affiliate": "#"},
    {"name": "Orange Money", "fee": 2.50, "rate": 650.00, "affiliate": "#"},
    {
        "name": "Remitly",
        "fee_special": {
            "function": True,
            "thresholds": [100, 200, 300, 500, 700],
            "values": [2.99, 5.99, 8.99, 12.99, 15.99, 18.99]
        },
        "rate": 655.96,
        "affiliate": "#"
    },
    {"name": "Taptap Send", "fee": 2.00, "rate": 655.957, "affiliate": "#"},
    {"name": "WorldRemit", "fee": 2.00, "rate": 655.957, "affiliate": "#"}
]

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "services": services
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("✅ data.json généré avec succès.")

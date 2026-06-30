import requests
import json
import os
from datetime import datetime, timezone
from google.cloud import bigquery

# =============================================
# CONFIGURATION
# =============================================
PROJECT_ID = "crafty-coral-420410"
DATASET_ID = "transfert_data"
TABLE_ID = "taux_historiques"

# FRAIS RÉELS (les mêmes que sur ton PC)
SERVICES = [
    {"name": "Sendwave", "fee": 3.00, "promo": "20€ offerts (code 4ZJWI)"},
    {"name": "Orange Money", "fee": 2.50, "promo": ""},
    {"name": "Remitly", "fee": 5.99, "promo": ""},
    {"name": "Taptap Send", "fee": 2.00, "promo": "10€ offerts (code JOELL823)"},
    {"name": "WorldRemit", "fee": 2.00, "promo": ""},
]

# =============================================
# 1. AUTHENTIFICATION (via le secret GitHub)
# =============================================
credential_str = os.environ.get("GCP_CREDENTIALS")

if credential_str:
    creds = json.loads(credential_str)
    client = bigquery.Client.from_service_account_info(creds, project=PROJECT_ID)
    print("✅ Authentification via GCP_CREDENTIALS secret")
else:
    # Fallback local (si jamais tu testes chez toi)
    try:
        client = bigquery.Client.from_service_account_json("key.json")
        print("✅ Authentification via key.json (local)")
    except FileNotFoundError:
        raise Exception("❌ Aucune clé trouvée.")

# =============================================
# 2. RÉCUPÉRATION DU TAUX DE CHANGE EN TEMPS RÉEL
# =============================================
def get_exchange_rate():
    """Récupère le vrai taux EUR/XOF du jour"""
    # 1er essai : Frankfurter (très fiable)
    try:
        url = "https://api.frankfurter.app/latest?from=EUR&to=XOF"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "rates" in data and "XOF" in data["rates"]:
            taux = data["rates"]["XOF"]
            print(f"✅ Taux réel du jour (Frankfurter) : {taux}")
            return taux
    except Exception as e:
        print(f"⚠️ Erreur Frankfurter : {e}")

    # 2ème essai : exchangerate.host
    try:
        url = "https://api.exchangerate.host/latest?base=EUR&symbols=XOF"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("success") and "rates" in data:
            taux = data["rates"]["XOF"]
            print(f"✅ Taux réel du jour (ExchangeRate) : {taux}")
            return taux
    except Exception as e:
        print(f"⚠️ Erreur ExchangeRate : {e}")

    # Fallback ultime (si les 2 API sont mortes, ce qui est rarissime)
    print("🚨 Fallback : utilisation de 655.96")
    return 655.96

# =============================================
# 3. GÉNÉRATION DU data.json
# =============================================
def generate_data_json(taux, timestamp):
    rows = []
    montant_base = 200
    for service in SERVICES:
        frais = service["fee"]
        montant_recu = (montant_base - frais) * taux
        rows.append({
            "name": service["name"],
            "fee": round(frais, 2),
            "rate": round(taux, 3),
            "affiliate": "#"
        })
    
    # Envoi vers BigQuery (pour l'API)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    bq_rows = []
    for service in SERVICES:
        frais = service["fee"]
        montant_recu = (montant_base - frais) * taux
        bq_rows.append({
            "id": f"{service['name'].lower()}_{timestamp.strftime('%Y%m%d%H%M%S')}",
            "operateur": service["name"],
            "devise_source": "EUR",
            "devise_cible": "XOF",
            "frais_application": round(frais, 2),
            "taux_de_change": round(taux, 3),
            "montant_recu": round(montant_recu, 2),
            "promo": service["promo"],
            "timestamp_collecte": timestamp.isoformat()
        })
    
    try:
        errors = client.insert_rows_json(table_ref, bq_rows)
        if errors:
            print(f"⚠️ Erreurs BigQuery : {errors}")
        else:
            print(f"✅ {len(bq_rows)} lignes envoyées à BigQuery")
    except Exception as e:
        print(f"⚠️ Erreur BigQuery : {e}")

    # Génération du JSON final
    return {
        "last_updated": timestamp.isoformat(),
        "services": rows
    }

# =============================================
# 4. LANCEMENT
# =============================================
if __name__ == "__main__":
    print("🚀 Pipeline Cloud : Mise à jour des taux...")
    taux = get_exchange_rate()
    now = datetime.now(timezone.utc)
    data = generate_data_json(taux, now)
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ data.json mis à jour avec taux = {taux}")
    print("🎯 Terminé !")

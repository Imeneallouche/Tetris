import os
import json
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, parent_dir)

# Now you can import your module as expected
from Web_Application.Server.app.models import init_db, Command, Palette, Product, Camion


app = Flask(__name__)
engine = init_db()  # Initialisation de la base SQLite et création des tables
Session = sessionmaker(bind=engine)

# Chargement du fichier JSON contenant les types de produits et leurs contraintes
PRODUCTS_JSON_PATH = os.path.join(parent_dir, "Web_Application/Server/products.json")
with open(PRODUCTS_JSON_PATH, "r") as f:
    products_data = json.load(f)
# On crée un dictionnaire pour accéder rapidement aux infos de chaque type
product_types_info = {pt["type"]: pt for pt in products_data.get("product_types", [])}

# Seuil de distance pour regrouper des commandes (en kilomètres)
THRESHOLD_DISTANCE = 10


def parse_coordinates(destination):
    """
    Extrait les coordonnées d'une destination au format "lat,lon".
    Retourne un tuple (lat, lon) ou None si le format est incorrect.
    """
    try:
        lat, lon = map(float, destination.split(","))
        return lat, lon
    except Exception:
        return None


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points géographiques.
    """
    R = 6371  # Rayon de la Terre en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return R * c


def are_product_types_compatible(order1, order2):
    """
    Vérifie la compatibilité entre deux commandes sur la base de leur type de produit.
    """
    pt1 = order1["product_type"]
    pt2 = order2["product_type"]
    incompat1 = order1.get("incompatible_types", [])
    incompat2 = order2.get("incompatible_types", [])
    if pt2 in incompat1 or pt1 in incompat2:
        return False
    return True


@app.route("/api/load_plan", methods=["POST"])
def load_plan():
    """
    Endpoint pour la planification du chargement.
    Expects un JSON de la forme:
    {
        "order_ids": [1, 2, 3, ...]
    }
    Retourne des groupes de commandes pouvant être envoyées ensemble avec le camion sélectionné et l'ID du contrat associé.
    """
    data = request.get_json()
    if "order_ids" not in data:
        return jsonify({"error": "Le champ 'order_ids' est obligatoire."}), 400
    order_ids = data["order_ids"]

    session = Session()
    orders = session.query(Command).filter(Command.id.in_(order_ids)).all()
    if not orders:
        session.close()
        return jsonify({"error": "Aucune commande trouvée pour les IDs fournis."}), 404

    # Construction d'une liste d'informations pertinentes pour chaque commande
    orders_info = []
    for order in orders:
        # On considère ici qu'une commande possède au moins une palette
        if not order.palettes:
            continue
        palette = order.palettes[0]
        product = session.query(Product).filter_by(id=palette.product_id).first()
        if not product:
            continue
        coords = parse_coordinates(order.destination)
        if not coords:
            continue
        # Le type de produit est une chaîne qui doit correspondre aux clés du fichier JSON
        ptype = product.type
        pt_info = product_types_info.get(ptype, {})
        orders_info.append(
            {
                "order_id": order.id,
                "coords": coords,
                "product_type": ptype,
                "incompatible_types": pt_info.get("incompatible_types", []),
                "weight": palette.weight,
                "volume": palette.height * palette.width * palette.length,
                "min_temp": pt_info.get("min_temperature"),
                "max_temp": pt_info.get("max_temperature"),
            }
        )

    # Regroupement glouton des commandes compatibles et géographiquement proches
    groups = []
    used = set()
    for i, order in enumerate(orders_info):
        if order["order_id"] in used:
            continue
        group = [order]
        used.add(order["order_id"])
        for j, other in enumerate(orders_info):
            if other["order_id"] in used:
                continue
            # Vérification de la proximité géographique
            dist = haversine(
                order["coords"][0],
                order["coords"][1],
                other["coords"][0],
                other["coords"][1],
            )
            if dist > THRESHOLD_DISTANCE:
                continue
            # Vérification de la compatibilité des types de produits
            compatible = True
            for existing in group:
                if not are_product_types_compatible(existing, other):
                    compatible = False
                    break
            if compatible:
                group.append(other)
                used.add(other["order_id"])
        groups.append(group)

    result_groups = []
    for group in groups:
        total_weight = sum(item["weight"] for item in group)
        total_volume = sum(item["volume"] for item in group)
        # Calcul des contraintes de température communes, si définies
        temps_min = [item["min_temp"] for item in group if item["min_temp"] is not None]
        temps_max = [item["max_temp"] for item in group if item["max_temp"] is not None]
        overall_min_temp = max(temps_min) if temps_min else None
        overall_max_temp = min(temps_max) if temps_max else None

        # Recherche des camions disponibles répondant aux contraintes de capacité
        available_trucks = session.query(Camion).filter(Camion.state == True).all()
        candidate_trucks = []
        for truck in available_trucks:
            if truck.poids_max < total_weight or truck.volume_max < total_volume:
                continue
            # Vérification des contraintes de température, le cas échéant
            if overall_min_temp is not None and overall_max_temp is not None:
                if not (overall_min_temp <= truck.temperature <= overall_max_temp):
                    continue
            candidate_trucks.append(truck)
        if not candidate_trucks:
            # Si aucun camion ne convient pour ce groupe, on passe au suivant
            continue
        # Sélection du camion avec le coût de transport minimal
        candidate_trucks.sort(key=lambda t: t.transport_cost)
        selected_truck = candidate_trucks[0]
        # Marquer le camion comme occupé
        selected_truck.state = False
        session.commit()
        # Récupérer l'ID du contrat associé (premier trouvé)
        contract_id = (
            selected_truck.contracts[0].id if selected_truck.contracts else None
        )

        result_groups.append(
            {
                "order_ids": [item["order_id"] for item in group],
                "truck_id": selected_truck.id,
                "contract_id": contract_id,
                "total_weight": total_weight,
                "total_volume": total_volume,
            }
        )

    session.commit()
    session.close()
    return jsonify({"groups": result_groups}), 200


if __name__ == "__main__":
    app.run(debug=True)

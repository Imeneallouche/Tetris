# /*//////////////////////////////////////////////////////////////
#                    MADE WITH <3 BY T34M IMP3RM34BLE
#                                IMPORTS
# /////////////////////////////////////////////////////////////*/

from flask import Flask, request, jsonify
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import os
import json
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, parent_dir)

from app.models import init_db, User, Command, Palette, Product, Camion, Stock, UserRole


# /*//////////////////////////////////////////////////////////////
#                  STATIC VARIABLES AND INITIALIZATIONS
# //////////////////////////////////////////////////////////////*/

app = Flask(__name__)
engine = init_db()  # Initialize the SQLite database and create tables
Session = sessionmaker(bind=engine)


# Valeurs par défaut pour les palettes
DEFAULT_PALETTE_EMPTY_WEIGHT = 10.0  # poids de la palette vide
DEFAULT_PALETTE_DIMENSION = 1.0  # dimensions par défaut (height, width, length)
THRESHOLD_DISTANCE = 10  # Threshold distance (in kilometers) to group orders and to check supplier proximity
WAREHOUSE_COORD = "48.8566,2.3522"  # example coordinate (Paris center)

# Load the JSON file with product types and their constraints
PRODUCTS_JSON_PATH = os.path.join(parent_dir, "Web_Application/Server/products.json")
with open(PRODUCTS_JSON_PATH, "r") as f:
    products_data = json.load(f)
# Build a lookup dictionary for product type info
product_types_info = {pt["type"]: pt for pt in products_data.get("product_types", [])}


# /*//////////////////////////////////////////////////////////////
#                GEOGRAPHICAL COORDINATES PARSER FUNCTION
# //////////////////////////////////////////////////////////////*/
def parse_coordinates(destination):
    """
    Extract coordinates from a destination formatted as "lat,lon".
    Returns a tuple (lat, lon) or None if the format is incorrect.
    """
    try:
        lat, lon = map(float, destination.split(","))
        return lat, lon
    except Exception:
        return None


# /*//////////////////////////////////////////////////////////////
#                           DISTANCE COMPUTER
# //////////////////////////////////////////////////////////////*/
def haversine(lat1, lon1, lat2, lon2):
    """
    Compute the distance (in kilometers) between two geographic points.
    """
    R = 6371  # Radius of the Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return R * c


# /*//////////////////////////////////////////////////////////////
#                        COMPATIBLE PRODUCT TYPES
# //////////////////////////////////////////////////////////////*/
def are_product_types_compatible(order1, order2):
    """
    Check whether two orders are compatible based on their product type.
    """
    pt1 = order1["product_type"]
    pt2 = order2["product_type"]
    incompat1 = order1.get("incompatible_types", [])
    incompat2 = order2.get("incompatible_types", [])
    if pt2 in incompat1 or pt1 in incompat2:
        return False
    return True


# /*//////////////////////////////////////////////////////////////
#               COMPUTE MIDPOINT BETWEEN TWO DESTINATIONS
# //////////////////////////////////////////////////////////////*/
def compute_midpoint(coord1, coord2):
    """
    Given two destination strings "lat,lon", compute the midpoint (lat, lon).
    """
    lat1, lon1 = parse_coordinates(coord1)
    lat2, lon2 = parse_coordinates(coord2)
    if lat1 is None or lat2 is None:
        return None, None
    return (lat1 + lat2) / 2, (lon1 + lon2) / 2


# /*//////////////////////////////////////////////////////////////
#               SUPPLIERS NEARBY THE COMING BACK ITINERARY
# //////////////////////////////////////////////////////////////*/
def detect_supplier(mid_lat, mid_lon):
    """
    Query the database for suppliers (users with role 'fournisseur')
    and return the ID and address of the supplier that is closest to the midpoint,
    if within the THRESHOLD_DISTANCE.
    """
    session = Session()
    suppliers = session.query(User).filter(User.role == UserRole.fournisseur).all()
    best_supplier = None
    best_distance = float("inf")
    for supplier in suppliers:
        supp_coord = parse_coordinates(getattr(supplier, "address", ""))
        if supp_coord:
            dist = haversine(mid_lat, mid_lon, supp_coord[0], supp_coord[1])
            if dist < THRESHOLD_DISTANCE and dist < best_distance:
                best_supplier = supplier
                best_distance = dist
    session.close()
    if best_supplier:
        return best_supplier.id, getattr(best_supplier, "address", None)
    return None, None


def get_route(waypoints):
    """
    Simulate a call to an external routing API (OpenStreetMap) to obtain
    the optimal route for the given list of waypoints.
    """
    # In a real implementation, use the requests library to call the external API.
    return {"route": "Simulated optimal route", "waypoints": waypoints}


# /*//////////////////////////////////////////////////////////////
#                           ROUTES START HERE
# //////////////////////////////////////////////////////////////*/
# Route pour vérifier que l'application fonctionne
@app.route("/")
def home():
    return "L'application fonctionne ! 🚀"


# /*//////////////////////////////////////////////////////////////
#                          COMMAND SUBMISSION
# //////////////////////////////////////////////////////////////*/
@app.route("/api/command", methods=["POST"])
def add_command():
    """
    Endpoint pour ajouter une commande.
    Le formulaire doit contenir les champs suivants (en JSON):
      - destination : point ou adresse (issue de Google Maps)
      - full_name : nom complet du client
      - email : adresse email du client
      - phone : numéro de téléphone
      - city : ville
      - type_of_product : type de produit
      - name_of_product : nom du produit
      - quantity : quantité commandée (entier)
      - deadline : date limite (format 'YYYY-MM-DD')
      - message (optionnel) : message complémentaire
    """
    data = request.get_json()

    # Vérification des champs obligatoires
    required_fields = [
        "destination",
        "full_name",
        "email",
        "phone",
        "city",
        "type_of_product",
        "name_of_product",
        "quantity",
        "deadline",
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Champs manquants: {', '.join(missing_fields)}"}), 400

    session = Session()

    # Recherche de l'utilisateur par email
    user = session.query(User).filter_by(email=data["email"]).first()
    if not user:
        session.close()
        return jsonify({"error": "Utilisateur non trouvé."}), 404

    # Recherche du produit par son nom (et éventuellement type si besoin)
    product = session.query(Product).filter_by(name=data["name_of_product"]).first()
    if not product:
        session.close()
        return jsonify({"error": "Produit non trouvé."}), 404

    # Conversion et vérification des données
    try:
        quantity = int(data["quantity"])
    except ValueError:
        session.close()
        return jsonify({"error": "La quantité doit être un entier."}), 400

    try:
        # On suppose un format de date 'YYYY-MM-DD'
        max_date = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
    except Exception:
        session.close()
        return (
            jsonify({"error": "Format de deadline invalide, attendu YYYY-MM-DD."}),
            400,
        )

    # Calcul du gain : quantité * prix du produit.
    # On suppose que l'attribut 'price' existe dans le modèle Product.
    product_price = getattr(product, "price", None)
    if product_price is None:
        session.close()
        return jsonify({"error": "Le prix du produit n'est pas défini."}), 400
    gain = quantity * product_price

    # Création de la nouvelle commande
    new_command = Command(
        client_id=user.id,
        destination=f"{data['destination']}, {data['city']}",
        min_date=datetime.today().date(),
        max_date=max_date,
        gain=gain,
    )
    # Si le modèle Command est enrichi d'un champ 'message', on le renseigne
    if "message" in data:
        # On ajoute ici le message si le modèle le supporte
        new_command.message = data["message"]

    session.add(new_command)
    session.commit()  # Permet d'obtenir l'ID de la commande

    # Création d'une palette associée à la commande
    new_palette = Palette(
        command_id=new_command.id,
        product_id=product.id,
        quantity=quantity,
        height=DEFAULT_PALETTE_DIMENSION,
        width=DEFAULT_PALETTE_DIMENSION,
        length=DEFAULT_PALETTE_DIMENSION,
        weight=product.weight * quantity + DEFAULT_PALETTE_EMPTY_WEIGHT,
        reverseable=False,
        extra_details=data.get("message", ""),
    )
    session.add(new_palette)
    session.commit()

    session.close()
    return jsonify({"success": True, "command_id": new_command.id}), 201


# Stub for the external function – implement later
def estimate_warehouse_needs(fournisseur_id, group):
    # This function will estimate the materiel premiere quantities required from the supplier.
    pass


# /*//////////////////////////////////////////////////////////////
#                       PLANNIFICATION DES CAMIONS
# //////////////////////////////////////////////////////////////*/
@app.route("/api/plan_delivery", methods=["POST"])
def plan_delivery():
    """
    Endpoint to plan the delivery scheduling.

    Expected JSON input:
    {
        "order_ids": [1, 2, 3, ...]
    }

    The endpoint groups orders (using the knapsack-inspired logic from load_plan),
    then assigns a warehouse arrival time for each truck (ensuring that no more than the yard_space trucks
    are charging concurrently, with a 40-minute charging time per truck) and identifies a nearby supplier
    if one exists along the return itinerary.

    The JSON response for each group contains:
      - order_ids: list of order IDs in the group
      - truck_id: the ID of the selected truck
      - contract_id: the ID of the associated contract (from the truck’s contracts)
      - total_weight: total weight of the grouped orders
      - total_volume: total volume of the grouped orders
      - warehouse_arrival_time: ISO-formatted datetime when the truck will arrive to charge
      - fournisseur_id: supplier ID if a nearby supplier was detected, otherwise null
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

    # Build a list of order info (each order must have at least one palette)
    orders_info = []
    for order in orders:
        if not order.palettes:
            continue
        palette = order.palettes[0]
        product = session.query(Product).filter_by(id=palette.product_id).first()
        if not product:
            continue
        coords = parse_coordinates(order.destination)
        if not coords:
            continue
        ptype = product.type  # must correspond to a key in the JSON
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
                "deadline": order.max_date,  # deadline for delivery (a date object)
            }
        )

    # Group orders that are geographically close and have compatible product types
    groups_temp = []
    used = set()
    for order in orders_info:
        if order["order_id"] in used:
            continue
        group = [order]
        used.add(order["order_id"])
        for other in orders_info:
            if other["order_id"] in used:
                continue
            dist = haversine(
                order["coords"][0],
                order["coords"][1],
                other["coords"][0],
                other["coords"][1],
            )
            if dist > THRESHOLD_DISTANCE:
                continue
            compatible = True
            for existing in group:
                if not are_product_types_compatible(existing, other):
                    compatible = False
                    break
            if compatible:
                group.append(other)
                used.add(other["order_id"])
        groups_temp.append(group)

    # For each group, calculate the earliest deadline among its orders.
    planned_groups = []
    for group in groups_temp:
        deadlines = [order["deadline"] for order in group]
        min_deadline = min(deadlines)
        planned_groups.append({"orders": group, "min_deadline": min_deadline})

    # Sort groups by the earliest deadline (ascending)
    planned_groups.sort(key=lambda g: g["min_deadline"])

    # Get the available yard space from the stock table (assume a single warehouse)
    stock = session.query(Stock).first()
    yard_space = stock.yard_space if stock else 1

    # Scheduling: assign arrival times in batches (each truck charges for 40 minutes)
    base_time = datetime.now()
    charging_time = 40  # in minutes
    for idx, group in enumerate(planned_groups):
        # Simple batch scheduling: up to yard_space trucks can start at the same time.
        batch_index = idx // yard_space
        arrival_time = base_time + timedelta(minutes=batch_index * charging_time)
        planned_departure = arrival_time + timedelta(minutes=charging_time)
        # Ensure that the planned departure is before the group’s earliest deadline.
        if planned_departure > group["min_deadline"]:
            group["arrival_time"] = (
                None  # Not schedulable; you might flag or filter these groups
            )
        else:
            group["arrival_time"] = arrival_time

    # For each group, determine if a nearby supplier is available.
    # Suppliers are users with the "fournisseur" role and are assumed to have an "address" field (a "lat,lon" string)
    suppliers = session.query(User).filter(User.role == "fournisseur").all()
    for group in planned_groups:
        # Compute the average coordinates for the group.
        lat_sum = sum(order["coords"][0] for order in group["orders"])
        lon_sum = sum(order["coords"][1] for order in group["orders"])
        count = len(group["orders"])
        avg_lat = lat_sum / count
        avg_lon = lon_sum / count
        supplier_found = None
        for supplier in suppliers:
            supp_coords = parse_coordinates(getattr(supplier, "address", ""))
            if supp_coords:
                if (
                    haversine(avg_lat, avg_lon, supp_coords[0], supp_coords[1])
                    <= THRESHOLD_DISTANCE
                ):
                    supplier_found = supplier
                    break
        if supplier_found:
            group["fournisseur_id"] = supplier_found.id
            # Call the external function (to be implemented later) to estimate needed materiel
            estimate_warehouse_needs(supplier_found.id, group)
        else:
            group["fournisseur_id"] = None

    # For each planned group, run the truck selection logic (similar to load_plan)
    result_groups = []
    for group in planned_groups:
        orders = group["orders"]
        total_weight = sum(item["weight"] for item in orders)
        total_volume = sum(item["volume"] for item in orders)
        temps_min = [
            item["min_temp"] for item in orders if item["min_temp"] is not None
        ]
        temps_max = [
            item["max_temp"] for item in orders if item["max_temp"] is not None
        ]
        overall_min_temp = max(temps_min) if temps_min else None
        overall_max_temp = min(temps_max) if temps_max else None

        available_trucks = session.query(Camion).filter(Camion.state == True).all()
        candidate_trucks = []
        for truck in available_trucks:
            if truck.poids_max < total_weight or truck.volume_max < total_volume:
                continue
            if overall_min_temp is not None and overall_max_temp is not None:
                if not (overall_min_temp <= truck.temperature <= overall_max_temp):
                    continue
            candidate_trucks.append(truck)
        if not candidate_trucks:
            # No truck available for this group: skip or handle as needed.
            continue
        candidate_trucks.sort(key=lambda t: t.transport_cost)
        selected_truck = candidate_trucks[0]
        selected_truck.state = False  # Mark truck as occupied
        session.commit()
        contract_id = (
            selected_truck.contracts[0].id if selected_truck.contracts else None
        )

        result_groups.append(
            {
                "order_ids": [item["order_id"] for item in orders],
                "truck_id": selected_truck.id,
                "contract_id": contract_id,
                "total_weight": total_weight,
                "total_volume": total_volume,
                "warehouse_arrival_time": (
                    group["arrival_time"].isoformat() if group["arrival_time"] else None
                ),
                "fournisseur_id": group["fournisseur_id"],
            }
        )

    session.commit()
    session.close()
    return jsonify({"groups": result_groups}), 200


from datetime import datetime, timedelta
from Web_Application.Server.app.models import (
    Session,
    Command,
    Palette,
    Product,
    Stock,
    User,
    product_matiere,
    stock_matiere,
)


# /*//////////////////////////////////////////////////////////////
#                 TRANSPORT COORDINATION WITH PRODUCTION
# //////////////////////////////////////////////////////////////*/


def estimate_warehouse_needs(supplier_id, group):
    """
    Estimate the additional quantities of raw materials (matières premières) needed for the upcoming week.

    The estimation is based on:
      - Historical orders over the past 4 weeks to calculate an average weekly demand per product.
      - The raw material consumption per product (stored in the 'product_matiere' association table).
      - The current stock levels of raw materials (from the Stock table via the 'stock_matiere' association).

    If a supplier is specified (supplier_id), only the raw materials supplied by that supplier are returned.

    Returns:
      A dictionary mapping raw material IDs to the additional quantity needed.
    """
    session = Session()

    # Define the historical window (last 4 weeks)
    four_weeks_ago = datetime.now().date() - timedelta(weeks=4)

    # Query historical orders from the past 4 weeks
    orders = (
        session.query(Command).filter(Command.delivery_date >= four_weeks_ago).all()
    )

    # Calculate total quantity ordered for each product over the period
    product_totals = {}  # {product_id: total_quantity}
    for order in orders:
        for palette in order.palettes:
            pid = palette.product_id
            product_totals[pid] = product_totals.get(pid, 0) + palette.quantity

    # Compute the average weekly demand for each product (divide total by 4 weeks)
    product_weekly_demand = {pid: total / 4.0 for pid, total in product_totals.items()}

    # Now calculate the raw material requirements based on product consumption.
    # The association table 'product_matiere' stores the quantity of raw material consumed per unit of product.
    raw_material_requirements = {}  # {matiere_id: total_required per week}
    for pid, weekly_demand in product_weekly_demand.items():
        # Query the consumption details for this product from the association table.
        query = product_matiere.select().where(product_matiere.c.product_id == pid)
        result = session.execute(query)
        for row in result:
            matiere_id = row.matiere_id
            consumption_per_unit = (
                row.quantity
            )  # Raw material needed per unit of product
            # Accumulate the total weekly requirement for this raw material.
            raw_material_requirements[matiere_id] = raw_material_requirements.get(
                matiere_id, 0
            ) + (weekly_demand * consumption_per_unit)

    # Get current stock of raw materials from the Stock table.
    # Here we assume a single warehouse stock record.
    stock = session.query(Stock).first()
    current_stock = {}  # {matiere_id: quantity_in_stock}
    if stock:
        query = stock_matiere.select().where(stock_matiere.c.stock_id == stock.id)
        result = session.execute(query)
        for row in result:
            matiere_id = row.matiere_id
            quantity_in_stock = row.quantity
            current_stock[matiere_id] = quantity_in_stock

    # Compute the additional raw material needed for each matiere:
    additional_needs = {}
    for matiere_id, required in raw_material_requirements.items():
        in_stock = current_stock.get(matiere_id, 0)
        additional = required - in_stock
        # If we already have enough, no need to order extra.
        if additional < 0:
            additional = 0
        additional_needs[matiere_id] = additional

    # If a supplier is specified, filter the needs to only those raw materials supplied by this supplier.
    if supplier_id:
        supplier = session.query(User).filter(User.id == supplier_id).first()
        if supplier and hasattr(supplier, "materiels"):
            supplied_matiere_ids = {m.id for m in supplier.materiels}
            additional_needs = {
                mat_id: qty
                for mat_id, qty in additional_needs.items()
                if mat_id in supplied_matiere_ids
            }

    session.close()
    return additional_needs


# /*//////////////////////////////////////////////////////////////
#                         ITENERARY OPTIMISATION
# //////////////////////////////////////////////////////////////*/


@app.route("/api/optimize_route", methods=["POST"])
def optimize_route():
    """
    Endpoint to optimize a truck's route.

    Expected JSON input:
    {
        "truck_id": <integer>,
        "direction": "outbound" or "return",
        "palettes": [
            {"order_id": 1, "position": 3, "destination": "48.8600,2.3500"},
            {"order_id": 2, "position": 1, "destination": "48.8570,2.3530"},
            {"order_id": 3, "position": 2, "destination": "48.8585,2.3525"}
        ]
    }

    For the outbound route, the order is determined by LIFO (sorted by position descending).
    For the return route, the starting point is the last delivery destination,
    and if a supplier is detected on the return path, its address is added as a waypoint.
    """
    data = request.get_json()
    required_fields = ["truck_id", "direction", "palettes"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    truck_id = data["truck_id"]
    direction = data["direction"]
    palettes = data["palettes"]

    if not isinstance(palettes, list) or not palettes:
        return jsonify({"error": "Palettes must be a non-empty list."}), 400

    # Validate each palette entry contains 'order_id', 'position', and 'destination'
    for p in palettes:
        if not all(k in p for k in ("order_id", "position", "destination")):
            return (
                jsonify(
                    {
                        "error": "Each palette must include 'order_id', 'position', and 'destination'."
                    }
                ),
                400,
            )

    if direction == "outbound":
        # Outbound: determine delivery order based on LIFO (highest position first)
        sorted_palettes = sorted(palettes, key=lambda x: x["position"], reverse=True)
        # Build the list of waypoints (delivery destinations) in order
        waypoints = [p["destination"] for p in sorted_palettes]
        route_info = get_route(waypoints)
        route_info["delivery_order"] = [p["order_id"] for p in sorted_palettes]
        return jsonify(route_info), 200

    elif direction == "return":
        # Return: start from the last delivered destination
        sorted_palettes = sorted(palettes, key=lambda x: x["position"], reverse=True)
        last_destination = sorted_palettes[-1]["destination"]
        # Compute the midpoint between the last destination and the warehouse
        mid_lat, mid_lon = compute_midpoint(last_destination, WAREHOUSE_COORD)
        supplier_id, supplier_address = (None, None)
        if mid_lat is not None:
            supplier_id, supplier_address = detect_supplier(mid_lat, mid_lon)
        # Build the waypoints for the return route:
        # Start at last destination, then (if supplier found) supplier, then warehouse.
        waypoints = [last_destination]
        if supplier_address:
            waypoints.append(supplier_address)
        waypoints.append(WAREHOUSE_COORD)
        route_info = get_route(waypoints)
        route_info["fournisseur_id"] = supplier_id
        return jsonify(route_info), 200

    else:
        return (
            jsonify({"error": "Invalid 'direction'. Must be 'outbound' or 'return'."}),
            400,
        )


if __name__ == "__main__":
    app.run(debug=True)

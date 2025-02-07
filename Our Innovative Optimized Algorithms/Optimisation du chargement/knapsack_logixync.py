import math
from collections import defaultdict
from typing import List, Dict, Tuple

# Définition d'une commande (order) sous forme de dictionnaire
# Chaque commande a :
#   - 'id' : identifiant unique
#   - 'product_type' : type de produit (ex. "laitiers", "nettoyage", "alimentation", …)
#   - 'destination' : (x, y) coordonnées (ou tout autre système géographique simplifié)
#   - 'weight' : poids de la commande
#   - 'dimensions' : (length, width, height) en unités cohérentes (pour calculer le volume)
#
# On calcule alors 'volume' = length * width * height.


def compute_volume(dimensions: Tuple[float, float, float]) -> float:
    length, width, height = dimensions
    return length * width * height


# Fonction pour calculer la distance Euclidienne entre deux destinations
def distance(dest1: Tuple[float, float], dest2: Tuple[float, float]) -> float:
    return math.sqrt((dest1[0] - dest2[0]) ** 2 + (dest1[1] - dest2[1]) ** 2)


# Regrouper les commandes par type de produit et proximité des destinations
# destination_threshold définit la distance maximale pour considérer que deux destinations sont proches.
def group_orders(
    orders: List[Dict], destination_threshold: float
) -> Dict[Tuple[str, int], List[Dict]]:
    # Pour chaque type de produit, nous allons créer des sous-groupes numérotés.
    groups = {}  # clé: (product_type, group_id), valeur: liste d'ordres
    # Structure temporaire pour chaque type
    type_groups = defaultdict(list)

    # D'abord, regrouper par type
    for order in orders:
        order["volume"] = compute_volume(order["dimensions"])
        type_groups[order["product_type"]].append(order)

    # Pour chaque type, regrouper par proximité de destination
    result_groups = {}
    for ptype, orders_list in type_groups.items():
        group_id = 0
        # Liste de groupes pour ce type, chaque groupe est représenté par (rep_dest, [order,...])
        groups_for_type = []
        for order in orders_list:
            assigned = False
            for idx, (rep_dest, group_orders_list) in enumerate(groups_for_type):
                if distance(rep_dest, order["destination"]) <= destination_threshold:
                    group_orders_list.append(order)
                    # Actualiser légèrement le centre (rep_dest) du groupe en faisant la moyenne
                    new_x = (
                        rep_dest[0] * len(group_orders_list) + order["destination"][0]
                    ) / (len(group_orders_list) + 1)
                    new_y = (
                        rep_dest[1] * len(group_orders_list) + order["destination"][1]
                    ) / (len(group_orders_list) + 1)
                    groups_for_type[idx] = ((new_x, new_y), group_orders_list)
                    assigned = True
                    break
            if not assigned:
                # Créer un nouveau groupe avec ce point comme centre
                groups_for_type.append((order["destination"], [order]))

        # Enregistrer chaque groupe avec une clé composée de (product_type, group_id)
        for g in groups_for_type:
            result_groups[(ptype, group_id)] = g[1]
            group_id += 1
    return result_groups


# Calculer une "efficacité" pour chaque commande.
# Ici, nous définissons l'efficacité comme la somme relative de la consommation du poids et du volume,
# par rapport aux capacités maximales du camion.
def order_efficiency(order: Dict, W_max: float, V_max: float) -> float:
    # Par exemple : efficacité = (poids/W_max + volume/V_max)
    return order["weight"] / W_max + order["volume"] / V_max


# Algorithme de chargement heuristique
def optimize_loading(
    orders: List[Dict], W_max: float, V_max: float, destination_threshold: float
) -> List[Dict]:
    """
    orders: liste de commandes (chaque commande doit contenir 'id', 'product_type', 'destination',
            'weight', 'dimensions' (tuple) ; 'volume' sera calculé)
    W_max: poids maximum du camion
    V_max: volume maximum du camion
    destination_threshold: seuil de distance pour regrouper les commandes par proximité
    Retourne la liste des commandes sélectionnées pour remplir le camion.
    """
    # Groupage par type et destination
    grouped_orders = group_orders(orders, destination_threshold)

    # Pour chaque groupe, trier les commandes par efficacité décroissante
    for key, group in grouped_orders.items():
        group.sort(
            key=lambda order: order_efficiency(order, W_max, V_max), reverse=True
        )

    # Tri des groupes par une métrique agrégée (par exemple, somme des efficacités) décroissante
    groups_sorted = sorted(
        grouped_orders.items(),
        key=lambda item: sum(order_efficiency(o, W_max, V_max) for o in item[1]),
        reverse=True,
    )

    current_weight = 0.0
    current_volume = 0.0
    selected_orders = []

    # Parcourir les groupes et tenter d'ajouter chaque commande si elle tient dans le camion
    for group_key, group in groups_sorted:
        for order in group:
            if (
                current_weight + order["weight"] <= W_max
                and current_volume + order["volume"] <= V_max
            ):
                selected_orders.append(order)
                current_weight += order["weight"]
                current_volume += order["volume"]

    return selected_orders


# Exemple d'utilisation :
if __name__ == "__main__":
    # Définir quelques commandes exemples
    orders = [
        {
            "id": "order_1",
            "product_type": "laitiers",
            "destination": (10, 20),
            "weight": 100,  # en kg
            "dimensions": (1.0, 0.5, 0.5),  # en m (volume = 0.25 m^3)
        },
        {
            "id": "order_2",
            "product_type": "laitiers",
            "destination": (11, 21),  # proche de (10,20)
            "weight": 150,
            "dimensions": (1.2, 0.5, 0.5),
        },
        {
            "id": "order_3",
            "product_type": "alimentation",
            "destination": (50, 60),
            "weight": 200,
            "dimensions": (1.0, 1.0, 0.5),
        },
        {
            "id": "order_4",
            "product_type": "alimentation",
            "destination": (51, 61),
            "weight": 100,
            "dimensions": (0.8, 0.5, 0.5),
        },
        {
            "id": "order_5",
            "product_type": "nettoyage",
            "destination": (15, 25),
            "weight": 80,
            "dimensions": (0.5, 0.5, 0.5),
        },
        {
            "id": "order_6",
            "product_type": "nettoyage",
            "destination": (16, 26),
            "weight": 90,
            "dimensions": (0.6, 0.5, 0.5),
        },
    ]

    # Définir les capacités du camion
    W_max = 1000  # poids max en kg
    V_max = 10.0  # volume max en m^3
    destination_threshold = 5.0  # seuil de regroupement en unités de distance (peut être en km ou unité arbitraire)

    loaded_orders = optimize_loading(orders, W_max, V_max, destination_threshold)

    print("Commandes sélectionnées pour le chargement du camion :")
    for o in loaded_orders:
        print(
            f"ID: {o['id']}, Type: {o['product_type']}, Destination: {o['destination']}, Poids: {o['weight']}, Volume: {o['volume']:.2f}"
        )

    print(f"Charge totale: {sum(o['weight'] for o in loaded_orders)} kg")
    print(f"Volume total utilisé: {sum(o['volume'] for o in loaded_orders):.2f} m^3")

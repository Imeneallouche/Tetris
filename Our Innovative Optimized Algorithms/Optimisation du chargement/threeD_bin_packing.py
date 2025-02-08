import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


# --- 1. Détermination de l'ordre de livraison via une simulation météo ---
def determine_delivery_order(orders):
    """
    Simule l'analyse des conditions météo sur l'itinéraire pour déterminer l'ordre de livraison.
    Chaque commande se voit attribuer un 'weather_score' aléatoire (score plus faible = livraison prioritaire).
    Ce score est ensuite utilisé pour trier les commandes.
    """
    for order in orders:
        order["weather_score"] = random.random()  # Simulation d'un score météo
    orders.sort(key=lambda o: o["weather_score"])
    # On enregistre l'ordre de livraison (0 = première livraison)
    for i, order in enumerate(orders):
        order["delivery_order"] = i
    return orders


# --- 2. Optimisation du placement des palettes dans le camion ---
def optimize_truck_loading(orders, truck_dimensions):
    """
    Place les palettes dans le camion en respectant plusieurs contraintes :
    - Le principe LIFO : les commandes à livrer en premier (delivery_order le plus faible)
      seront chargées en dernier et ainsi placées en avant (x plus élevé).
    - Répartition équilibrée du poids : en alternant le placement sur le côté gauche et droit.

    On suppose ici que chaque commande contient des informations sur la palette :
       - dimensions : 'length', 'width', 'height'
       - 'weight'
    truck_dimensions est un dictionnaire contenant 'length', 'width' et 'height' du camion.

    Renvoie une liste de placements avec les coordonnées (x, y, z) et les dimensions associées.
    """
    # Pour respecter LIFO, on inverse l'ordre de livraison.
    orders_sorted = list(orders)
    orders_sorted.reverse()  # Le premier à être livré (delivery_order = 0) sera chargé en dernier, donc placé à l'avant.

    placements = []
    current_x = 0.0
    truck_length = truck_dimensions["length"]
    truck_width = truck_dimensions["width"]

    # Pour chaque commande, on attribue une position dans le camion.
    for idx, order in enumerate(orders_sorted):
        # On récupère les dimensions de la palette ; si absentes, on utilise des valeurs par défaut.
        pallet_length = order.get("length", 1.0)
        pallet_width = order.get("width", 1.0)
        pallet_height = order.get("height", 0.5)

        # Si l'espace en x n'est plus suffisant, dans une solution complète on pourra utiliser plusieurs rangées.
        if current_x + pallet_length > truck_length:
            current_x = 0  # Pour simplifier, on repart du début (ou on pourrait envisager une nouvelle rangée).

        # Pour équilibrer le poids sur la largeur, on alterne le placement sur la gauche et la droite.
        if idx % 2 == 0:
            y = pallet_width / 2  # côté gauche
        else:
            y = truck_width - pallet_width / 2  # côté droit

        placement = {
            "order_id": order["order_id"],
            "x": current_x,
            "y": y,
            "z": 0,  # Toutes les palettes sont posées au sol
            "pallet_length": pallet_length,
            "pallet_width": pallet_width,
            "pallet_height": pallet_height,
            "weight": order["weight"],
            "delivery_order": order["delivery_order"],
        }
        placements.append(placement)
        current_x += pallet_length  # Décalage suivant la longueur de la palette pour éviter le chevauchement

    return placements


# --- 3. Simulation 3D du chargement dans le camion ---
def simulate_truck_loading_3d(placements, truck_dimensions):
    """
    Visualise en 3D la disposition des palettes dans le camion.
    Chaque palette est représentée par un parallélépipède (boîte) dans l'espace.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Dimensions du camion
    truck_length = truck_dimensions["length"]
    truck_width = truck_dimensions["width"]
    truck_height = truck_dimensions["height"]

    # Dessin du camion comme une boîte transparente
    truck_corners = np.array(
        [
            [0, 0, 0],
            [truck_length, 0, 0],
            [truck_length, truck_width, 0],
            [0, truck_width, 0],
        ]
    )
    truck_corners_top = truck_corners.copy()
    truck_corners_top[:, 2] = truck_height

    ax.add_collection3d(Poly3DCollection([truck_corners], facecolors="cyan", alpha=0.1))
    ax.add_collection3d(
        Poly3DCollection([truck_corners_top], facecolors="cyan", alpha=0.1)
    )
    for i in range(4):
        next_i = (i + 1) % 4
        side = [
            truck_corners[i],
            truck_corners[next_i],
            truck_corners_top[next_i],
            truck_corners_top[i],
        ]
        ax.add_collection3d(Poly3DCollection([side], facecolors="cyan", alpha=0.1))

    # Dessin de chaque palette
    for pallet in placements:
        x = pallet["x"]
        y = pallet["y"]
        z = pallet["z"]
        l = pallet["pallet_length"]
        w = pallet["pallet_width"]
        h = pallet["pallet_height"]

        # Coordonnées de la base de la palette
        corners = np.array([[x, y, z], [x + l, y, z], [x + l, y + w, z], [x, y + w, z]])
        # Coordonnées du dessus de la palette
        corners_top = corners.copy()
        corners_top[:, 2] = z + h

        ax.add_collection3d(Poly3DCollection([corners], facecolors="orange", alpha=0.8))
        ax.add_collection3d(
            Poly3DCollection([corners_top], facecolors="orange", alpha=0.8)
        )
        for i in range(4):
            next_i = (i + 1) % 4
            side = [corners[i], corners[next_i], corners_top[next_i], corners_top[i]]
            ax.add_collection3d(
                Poly3DCollection([side], facecolors="orange", alpha=0.8)
            )

        # Annotation avec l'ID de la commande
        ax.text(
            x + l / 2, y + w / 2, z + h / 2, f"ID:{pallet['order_id']}", color="black"
        )

    ax.set_xlabel("Longueur (X)")
    ax.set_ylabel("Largeur (Y)")
    ax.set_zlabel("Hauteur (Z)")
    ax.set_xlim(0, truck_length)
    ax.set_ylim(0, truck_width)
    ax.set_zlim(0, truck_height)
    plt.title("Simulation du placement des palettes dans le camion")
    plt.show()


# --- Exemple de simulation ---
if __name__ == "__main__":
    # Dimensions du camion (exemple)
    truck_dimensions = {"length": 10.0, "width": 3.0, "height": 3.0}

    # Simuler quelques commandes avec leurs caractéristiques de palette
    sample_orders = [
        {
            "order_id": 1,
            "weight": 100,
            "length": 1.5,
            "width": 1.0,
            "height": 0.5,
            "coords": (48.8566, 2.3522),
        },
        {
            "order_id": 2,
            "weight": 80,
            "length": 1.2,
            "width": 1.0,
            "height": 0.5,
            "coords": (48.8570, 2.3530),
        },
        {
            "order_id": 3,
            "weight": 120,
            "length": 1.5,
            "width": 1.0,
            "height": 0.5,
            "coords": (48.8580, 2.3540),
        },
        {
            "order_id": 4,
            "weight": 60,
            "length": 1.0,
            "width": 1.0,
            "height": 0.5,
            "coords": (48.8590, 2.3550),
        },
    ]

    # Détermination de l'ordre de livraison en fonction d'un score météo simulé
    orders_with_order = determine_delivery_order(sample_orders)
    print("Ordre de livraison (score météo et delivery_order) :", orders_with_order)

    # Optimisation du placement dans le camion en appliquant le principe LIFO et la répartition du poids
    placements = optimize_truck_loading(orders_with_order, truck_dimensions)
    print("Placements calculés :", placements)

    # Simulation 3D du chargement dans le camion
    simulate_truck_loading_3d(placements, truck_dimensions)

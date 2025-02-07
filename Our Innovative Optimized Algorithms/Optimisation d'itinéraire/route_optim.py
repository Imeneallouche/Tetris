import time
import random
import plotly.graph_objects as go
import numpy as np

##########################################
# MODULE 1 : Définition des classes et fonctions de base


class Commande:
    def __init__(
        self,
        id,
        client,
        product_type,
        weight,
        length,
        width,
        height,
        delivery_order,
        destination_coords,
    ):
        self.id = id
        self.client = client
        self.product_type = product_type
        self.weight = weight  # en kg
        self.length = length  # en m
        self.width = width  # en m
        self.height = height  # en m
        self.delivery_order = (
            delivery_order  # ordre initial (1 = première livraison, etc.)
        )
        self.destination_coords = destination_coords  # (lat, lon)
        self.pos = (0, 0, 0)  # Position assignée dans le camion


def volume(cmd):
    return cmd.length * cmd.width * cmd.height


##########################################
# MODULE 2 : Optimisation initiale de la route
# Cette fonction simule l’obtention de données externes (température, incidents, trafic)
def get_external_conditions():
    # Pour la simulation, nous renvoyons des données aléatoires
    conditions = {
        "temperature": random.uniform(5, 35),  # en °C
        "accidents": {  # par segment entre clients (clé: segment, valeur: score d’incident)
            "segment_1": random.choice([0, 1]),  # 0 = rien, 1 = accident détecté
            "segment_2": random.choice([0, 1]),
            "segment_3": random.choice([0, 1]),
        },
        "traffic_delay": random.uniform(0, 15),  # en minutes supplémentaires
    }
    return conditions


def optimize_route(commandes, external_conditions):
    """
    Simule un algorithme d'optimisation de route.
    Ici, nous utilisons l'ordre de livraison initial, modifié par un "coût" supplémentaire en fonction des accidents et trafic.
    Pour chaque segment (entre commandes consécutives), on ajoute un coût.
    Puis on réordonne la liste en minimisant le coût total.
    """
    # Pour simplifier, on affecte à chaque commande un "coût" additionnel
    # Basé sur l'incident sur le segment précédent et le retard de trafic
    commandes_optimisees = sorted(commandes, key=lambda c: c.delivery_order)
    total_cost = 0
    # Simulation : si un accident est détecté sur le segment vers la commande, on augmente son coût de livraison.
    for i, cmd in enumerate(commandes_optimisees):
        segment = f"segment_{i+1}"
        accident_cost = (
            external_conditions["accidents"].get(segment, 0) * 10
        )  # coût pénalisant
        traffic_cost = external_conditions["traffic_delay"]
        # Le "coût" final peut être basé sur delivery_order + coûts additionnels
        cmd.route_cost = cmd.delivery_order + accident_cost + (traffic_cost / 10)
        total_cost += cmd.route_cost
    # On trie selon le coût recalculé pour obtenir un nouvel ordre
    nouvelles_commandes = sorted(commandes_optimisees, key=lambda c: c.route_cost)
    return nouvelles_commandes


##########################################
# MODULE 3 : Algorithme de 3D Bin Packing (déjà présenté)
def pack_orders(commandes, truck_length, truck_width, truck_height):
    current_x, current_y, current_z = 0, 0, 0
    current_row_max_width = 0  # Pour avancer en y (largeur)
    current_layer_max_height = 0  # Pour avancer en z (hauteur)

    for cmd in commandes:
        # Si le produit dépasse la longueur restante, recommencer sur une nouvelle rangée (axe y)
        if current_x + cmd.length > truck_length:
            current_x = 0
            current_y += current_row_max_width
            current_row_max_width = 0
        # Si le produit dépasse la largeur restante, passer à une nouvelle couche (axe z)
        if current_y + cmd.width > truck_width:
            current_y = 0
            current_z += current_layer_max_height
            current_layer_max_height = 0
        # Vérifier la hauteur
        if current_z + cmd.height > truck_height:
            raise Exception(
                "Capacité du camion insuffisante pour charger toutes les commandes."
            )

        # Assigner la position (coin inférieur gauche de la boîte)
        cmd.pos = (current_x, current_y, current_z)

        current_x += cmd.length
        current_row_max_width = max(current_row_max_width, cmd.width)
        current_layer_max_height = max(current_layer_max_height, cmd.height)

    return commandes


##########################################
# MODULE 4 : Visualisation 3D avec Plotly
def create_box_mesh(x, y, z, l, w, h, color, name=""):
    vertices = np.array(
        [
            [x, y, z],
            [x + l, y, z],
            [x + l, y + w, z],
            [x, y + w, z],
            [x, y, z + h],
            [x + l, y, z + h],
            [x + l, y + w, z + h],
            [x, y + w, z + h],
        ]
    )
    x_coords = vertices[:, 0]
    y_coords = vertices[:, 1]
    z_coords = vertices[:, 2]

    i = [0, 0, 0, 1, 1, 3, 4, 4, 5, 2, 6, 7]
    j = [1, 4, 3, 2, 5, 7, 5, 7, 6, 6, 7, 0]
    k = [2, 5, 2, 5, 6, 4, 7, 6, 7, 7, 3, 3]

    mesh = go.Mesh3d(
        x=x_coords,
        y=y_coords,
        z=z_coords,
        i=i,
        j=j,
        k=k,
        opacity=0.8,
        color=color,
        name=name,
        flatshading=True,
    )
    return mesh


product_colors = {
    "laitier": "lightblue",
    "alimentaire": "lightgreen",
    "nettoyage": "orange",
}


def visualiser_truck(commandes, truck_length, truck_width, truck_height):
    fig = go.Figure()
    truck_mesh = create_box_mesh(
        0, 0, 0, truck_length, truck_width, truck_height, "lightgrey", "Camion"
    )
    truck_mesh.update(opacity=0.2)
    fig.add_trace(truck_mesh)
    for cmd in commandes:
        col = product_colors.get(cmd.product_type, "grey")
        x, y, z = cmd.pos
        box = create_box_mesh(
            x, y, z, cmd.length, cmd.width, cmd.height, col, f"Commande {cmd.id}"
        )
        fig.add_trace(box)
        fig.add_trace(
            go.Scatter3d(
                x=[x + cmd.length / 2],
                y=[y + cmd.width / 2],
                z=[z + cmd.height / 2],
                mode="text",
                text=[f"{cmd.id}"],
                textposition="middle center",
                showlegend=False,
            )
        )
    fig.update_layout(
        title="Plan de chargement du camion (visualisation 3D)",
        scene=dict(
            xaxis_title="Longueur (m)",
            yaxis_title="Largeur (m)",
            zaxis_title="Hauteur (m)",
            aspectmode="data",
        ),
    )
    fig.show()


##########################################
# MODULE 5 : Algorithme global de ré-optimisation dynamique de l’itinéraire


def dynamic_route_optimization(
    initial_orders, truck_params, update_interval=10, journey_duration=60
):
    """
    initial_orders: liste de commandes regroupées (instances de Commande)
    truck_params: dict contenant 'max_weight', 'max_volume', 'length', 'width', 'height'
    update_interval: temps (en secondes) entre les ré-évaluations de la route
    journey_duration: durée totale simulée du trajet (en secondes)
    """
    # Calcul initial de l'itinéraire basé sur les conditions externes
    conditions = get_external_conditions()
    route_orders = optimize_route(initial_orders, conditions)
    print(
        "Itinéraire initial (ordre de livraison optimisé) :",
        [c.id for c in route_orders],
    )

    # Appliquer l'algorithme de packing pour placer les produits en respectant l'ordre
    packed_orders = pack_orders(
        route_orders,
        truck_params["length"],
        truck_params["width"],
        truck_params["height"],
    )
    # Visualisation initiale
    visualiser_truck(
        packed_orders,
        truck_params["length"],
        truck_params["width"],
        truck_params["height"],
    )

    current_route = route_orders
    start_time = time.time()

    # Boucle dynamique pendant la simulation du trajet
    while time.time() - start_time < journey_duration:
        time.sleep(update_interval)
        # Simuler la réception de nouvelles conditions externes pendant le trajet
        new_conditions = get_external_conditions()
        new_route = optimize_route(current_route, new_conditions)

        # Si le nouvel ordre diffère (par exemple, si un segment présente désormais un accident ou trafic intense)
        if [c.id for c in new_route] != [c.id for c in current_route]:
            print("Mise à jour de l'itinéraire détectée.")
            current_route = new_route
            # Réappliquer le 3D bin packing pour respecter le nouvel ordre de livraison
            packed_orders = pack_orders(
                current_route,
                truck_params["length"],
                truck_params["width"],
                truck_params["height"],
            )
            # Visualiser la nouvelle configuration
            visualiser_truck(
                packed_orders,
                truck_params["length"],
                truck_params["width"],
                truck_params["height"],
            )
            print("Nouvel ordre de livraison :", [c.id for c in current_route])
        else:
            print("Itinéraire inchangé.")

    print("Trajet terminé.")


##########################################
# Exemple d'utilisation globale

if __name__ == "__main__":
    # Définir des commandes (id, client, type, poids, dimensions, ordre de livraison initial, destination)
    commandes = [
        Commande(1, "Client_A", "laitier", 200, 1.2, 0.8, 0.5, 1, (48.8566, 2.3522)),
        Commande(
            2, "Client_B", "alimentaire", 150, 1.0, 0.7, 0.6, 2, (48.8570, 2.3600)
        ),
        Commande(3, "Client_C", "laitier", 180, 1.1, 0.8, 0.5, 3, (48.8580, 2.3700)),
        Commande(4, "Client_A", "nettoyage", 100, 0.9, 0.6, 0.4, 1, (48.8566, 2.3522)),
        Commande(
            5, "Client_B", "alimentaire", 250, 1.3, 0.9, 0.7, 2, (48.8570, 2.3600)
        ),
    ]

    # Paramètres du camion
    truck_params = {
        "max_weight": 1000,  # kg (pour contrôle global, ici pour la simulation)
        "max_volume": 10,  # m^3 (idem)
        "length": 10,  # m
        "width": 3,  # m
        "height": 3,  # m
    }

    # Lancer l'optimisation dynamique de l'itinéraire sur une simulation de 60 secondes avec mises à jour toutes les 10 secondes
    dynamic_route_optimization(
        commandes, truck_params, update_interval=10, journey_duration=60
    )

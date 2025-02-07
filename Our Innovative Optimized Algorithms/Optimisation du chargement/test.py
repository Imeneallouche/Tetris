import plotly.graph_objects as go
import numpy as np


# Définition de la classe Commande
class Commande:
    def __init__(
        self, id, client, product_type, weight, length, width, height, delivery_order
    ):
        self.id = id
        self.client = client  # ex : "Client_A", "Client_B", ...
        self.product_type = (
            product_type  # ex : "laitier", "alimentaire", "nettoyage", etc.
        )
        self.weight = weight  # en kg
        self.length = length  # en m
        self.width = width  # en m
        self.height = height  # en m
        self.delivery_order = (
            delivery_order  # Ordre de passage (1 = première livraison, etc.)
        )
        self.pos = (0, 0, 0)  # Position (x,y,z) dans le camion, à assigner ensuite


# Calcul du volume d'une commande
def volume(cmd):
    return cmd.length * cmd.width * cmd.height


# Étape 1 : Tri par ordre de livraison inversé
def trier_commandes(commandes):
    # On trie par ordre de livraison décroissant (la livraison "1" sera chargée en dernier => à l'avant du camion)
    return sorted(commandes, key=lambda c: c.delivery_order, reverse=True)


# Étape 2 : Un simple algorithme de packing 3D
def pack_orders(commandes, truck_length, truck_width, truck_height):
    """
    Place les commandes dans le camion de manière séquentielle.
    On remplit d'abord le long de l'axe x, ensuite y, puis z.
    On suppose ici que les commandes sont déjà triées par ordre de livraison inversé.
    """
    current_x, current_y, current_z = 0, 0, 0
    current_row_max_height = (
        0  # hauteur maximale de la rangée en cours (pour avancer en y)
    )
    current_layer_max_width = (
        0  # largeur maximale de la couche en cours (pour avancer en z)
    )

    for cmd in commandes:
        # Si le produit ne rentre pas dans la longueur, on passe à la rangée suivante (axe y)
        if current_x + cmd.length > truck_length:
            current_x = 0
            current_y += current_row_max_height
            current_row_max_height = 0
        # Si le produit ne rentre pas dans la largeur, on passe à la couche suivante (axe z)
        if current_y + cmd.width > truck_width:
            current_y = 0
            current_z += current_layer_max_width
            current_layer_max_width = 0
        # Vérifier qu'on reste dans la hauteur du camion
        if current_z + cmd.height > truck_height:
            raise Exception(
                "Capacité du camion insuffisante pour charger toutes les commandes."
            )

        # Assigner la position de la commande
        cmd.pos = (current_x, current_y, current_z)

        # Mettre à jour les indices de remplissage
        current_x += cmd.length
        current_row_max_height = max(current_row_max_height, cmd.width)
        current_layer_max_width = max(current_layer_max_width, cmd.height)

    return commandes


# Étape 3 : Création d'un objet 3D représentant une boîte (commande)
def create_box_mesh(x, y, z, l, w, h, color, name=""):
    """
    Crée un objet Mesh3d pour représenter une boîte.
    Les 8 sommets du cube sont calculés, puis on définit les 12 triangles (faces).
    """
    # Coordonnées des sommets
    vertices = np.array(
        [
            [x, y, z],  # 0
            [x + l, y, z],  # 1
            [x + l, y + w, z],  # 2
            [x, y + w, z],  # 3
            [x, y, z + h],  # 4
            [x + l, y, z + h],  # 5
            [x + l, y + w, z + h],  # 6
            [x, y + w, z + h],  # 7
        ]
    )

    # Décomposer en listes pour Plotly
    x_coords = vertices[:, 0]
    y_coords = vertices[:, 1]
    z_coords = vertices[:, 2]

    # Définition des faces (triangles) par indices
    # Chaque face du cube est décomposée en 2 triangles
    # Les triangles sont définis par trois indices : i, j, k
    # Exemple: face avant (0,1,2) et (0,2,3)
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


# Pour colorer selon le type de produit, on définit un mapping
product_colors = {
    "laitier": "lightblue",
    "alimentaire": "lightgreen",
    "nettoyage": "orange",
    # Ajoutez d'autres types et couleurs si nécessaire
}


# Étape 4 : Visualisation 3D avec Plotly
def visualiser_truck(orders, truck_length, truck_width, truck_height):
    fig = go.Figure()

    # Ajouter un cube transparent pour représenter le camion
    truck_mesh = create_box_mesh(
        0, 0, 0, truck_length, truck_width, truck_height, "lightgrey", "Camion"
    )
    truck_mesh.update(opacity=0.2)
    fig.add_trace(truck_mesh)

    # Pour chaque commande, ajouter une boîte à sa position assignée
    for cmd in orders:
        # Couleur en fonction du type de produit
        col = product_colors.get(cmd.product_type, "grey")
        # Position de la commande
        x, y, z = cmd.pos
        # Créer la boîte pour cette commande
        box = create_box_mesh(
            x, y, z, cmd.length, cmd.width, cmd.height, col, f"Commande {cmd.id}"
        )
        fig.add_trace(box)
        # Ajouter un label pour la commande
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

    # Configurer la mise en page
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


# Algorithme complet pour optimiser le chargement
def optimiser_chargement(
    commandes,
    truck_max_weight,
    truck_max_volume,
    truck_length,
    truck_width,
    truck_height,
):
    # Étape 1 : Trier par ordre de livraison inversé
    commandes_triees = trier_commandes(commandes)

    # Étape 2 : Sélectionner les commandes qui rentrent dans les contraintes globales (ici, nous supposons qu'elles ont déjà été choisies)
    poids_total = sum(cmd.weight for cmd in commandes_triees)
    vol_total = sum(volume(cmd) for cmd in commandes_triees)
    if poids_total > truck_max_weight or vol_total > truck_max_volume:
        print(
            "Attention : Toutes les commandes ne rentrent pas dans le camion. Une sélection préalable est nécessaire."
        )
        # Pour simplifier, on considère ici que les commandes sont compatibles.

    # Étape 3 : Affecter une position à chaque commande avec un algorithme de packing simple
    commandes_positionnees = pack_orders(
        commandes_triees, truck_length, truck_width, truck_height
    )

    return commandes_positionnees


# Exemple d'utilisation
if __name__ == "__main__":
    # Création d'exemples de commandes (id, client, type, poids, longueur, largeur, hauteur, ordre livraison)
    commandes = [
        Commande(1, "Client_A", "laitier", 200, 1.2, 0.8, 0.5, 1),
        Commande(2, "Client_B", "alimentaire", 150, 1.0, 0.7, 0.6, 2),
        Commande(3, "Client_C", "laitier", 180, 1.1, 0.8, 0.5, 3),
        Commande(4, "Client_A", "nettoyage", 100, 0.9, 0.6, 0.4, 1),
        Commande(5, "Client_B", "alimentaire", 250, 1.3, 0.9, 0.7, 2),
    ]

    # Capacités du camion en poids et volume (pour la sélection globale, ici à titre d'exemple)
    truck_max_weight = 500  # kg
    truck_max_volume = 10  # m^3

    # Dimensions internes du camion (zone de chargement)
    truck_length = 10  # m
    truck_width = 3  # m
    truck_height = 3  # m

    # Optimiser le chargement et obtenir les positions assignées
    commandes_chargees = optimiser_chargement(
        commandes,
        truck_max_weight,
        truck_max_volume,
        truck_length,
        truck_width,
        truck_height,
    )

    # Visualiser en 3D le chargement du camion
    visualiser_truck(commandes_chargees, truck_length, truck_width, truck_height)

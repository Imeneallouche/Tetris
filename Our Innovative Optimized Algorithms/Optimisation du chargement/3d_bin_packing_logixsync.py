# Classe représentant une commande à livrer
class Commande:
    def __init__(
        self, id, client, product_type, weight, length, width, height, delivery_order
    ):
        self.id = id
        self.client = client  # Identifiant ou coordonnées du client
        self.product_type = product_type  # ex: laitier, alimentaire, nettoyage, etc.
        self.weight = weight  # en kg
        self.length = length  # en m
        self.width = width  # en m
        self.height = height  # en m
        self.delivery_order = delivery_order  # Ordre de livraison dans la tournée


# Fonction pour calculer le volume d'une commande
def volume(commande):
    return commande.length * commande.width * commande.height


# Étape 1 : Tri des commandes par ordre de livraison
def trier_commandes(commandes):
    # On trie les commandes par delivery_order décroissant pour charger en ordre inverse
    return sorted(commandes, key=lambda c: c.delivery_order, reverse=True)


# Étape 2 : Partitionnement de l'espace en zones latérales pour équilibrer le poids
def assigner_zone(commandes):
    # On définit trois zones : gauche, centre, droite
    zones = {"gauche": [], "centre": [], "droite": []}
    # On peut par exemple affecter les commandes de manière itérative pour équilibrer la somme des poids
    poids_zones = {"gauche": 0, "centre": 0, "droite": 0}
    for cmd in commandes:
        # Affecter la commande à la zone avec le poids total le plus faible
        zone_min = min(poids_zones, key=poids_zones.get)
        zones[zone_min].append(cmd)
        poids_zones[zone_min] += cmd.weight
    return zones


# Étape 3 : Agencement dans le camion
def agencer_chargement(commandes, truck_max_weight, truck_max_volume):
    # Trier par ordre de livraison (inversion)
    commandes_triees = trier_commandes(commandes)

    # Initialiser variables pour suivre la charge du camion
    poids_total = 0
    volume_total = 0
    chargement = []

    # Première boucle : charger en respectant l'ordre (les commandes pour le premier client doivent être en avant)
    for cmd in commandes_triees:
        if (poids_total + cmd.weight <= truck_max_weight) and (
            volume_total + volume(cmd) <= truck_max_volume
        ):
            chargement.append(cmd)
            poids_total += cmd.weight
            volume_total += volume(cmd)
        else:
            # Si l'ajout de la commande dépasse l'une des contraintes, on la saute ou on l'ajuste via une méthode de sélection partielle
            continue

    # Une fois les commandes sélectionnées, on peut utiliser l'étape de répartition latérale pour répartir la charge
    zones = assigner_zone(chargement)

    # La phase finale consiste à déterminer l’ordre précis dans le camion.
    # Par exemple, on peut imaginer que les commandes de la zone 'centre' sont placées au milieu,
    # et celles de 'gauche' et 'droite' sur les côtés. Les commandes de chaque zone restent dans l'ordre trié.
    ordre_final = []
    # Placer en priorité les commandes qui seront déchargées en premier (elles sont à l'avant du camion)
    # Ici, on combine les zones en gardant l'ordre interne de chaque zone.
    for zone in ["gauche", "centre", "droite"]:
        ordre_final.extend(zones[zone])

    # Retourne la liste des commandes avec leur position d'agencement dans le camion
    return ordre_final, poids_total, volume_total


# Exemple d'utilisation
if __name__ == "__main__":
    # Création d'exemples de commandes
    commandes = [
        Commande(1, "Client_A", "laitier", 200, 1.2, 0.8, 0.5, 1),
        Commande(2, "Client_B", "alimentaire", 150, 1.0, 0.7, 0.6, 2),
        Commande(3, "Client_C", "laitier", 180, 1.1, 0.8, 0.5, 3),
        Commande(4, "Client_A", "nettoyage", 100, 0.9, 0.6, 0.4, 1),
        Commande(5, "Client_B", "alimentaire", 250, 1.3, 0.9, 0.7, 2),
        # Ajoutez d'autres commandes selon les besoins...
    ]

    # Capacité d'un camion
    truck_max_weight = 1000  # en kg
    truck_max_volume = 10  # en m^3

    agencement, poids_total, volume_total = agencer_chargement(
        commandes, truck_max_weight, truck_max_volume
    )
    print(
        "Ordre d'agencement des commandes dans le camion (de l'avant vers l'arrière) :"
    )
    for cmd in agencement:
        print(
            f"ID: {cmd.id}, Client: {cmd.client}, Type: {cmd.product_type}, Delivery Order: {cmd.delivery_order}, Poids: {cmd.weight} kg, Volume: {volume(cmd)} m^3"
        )
    print(f"Poids total chargé: {poids_total} kg")
    print(f"Volume total chargé: {volume_total} m^3")

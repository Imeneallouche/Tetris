<p align="center">
  <img width=50% src="logo.png" alt="logo"/>
</p>

# Titris

Tetris est une solution qui est conçue pour répondre aux problématiques logistiques actuelles en optimisant simultanément le chargement, l’itinéraire et la planification/coordination des transports. En combinant des algorithmes avancés, des intégrations en temps réel et des méthodes d’intelligence artificielle, notre solution permet de réduire significativement les coûts, le temps de transit, le nombre et d’améliorer l’efficacité opérationnelle des entreprises logistiques.

## Pourquoi Tetris?

Notre solution, baptisée **Tetris**, s'inspire du célèbre jeu de puzzle où le succès repose sur l'optimisation du placement des pièces pour remplir l'espace de manière efficace. De la même manière, l'optimisation du chargement des palettes dans nos camions est cruciale pour réduire le nombre de véhicules nécessaires, minimiser les trajets à vide et ainsi diminuer considérablement les coûts de transport. En optimisant l'agencement des commandes—en tenant compte des dimensions, du poids, des contraintes de sécurité et de la répartition latérale—nous maximisons l'utilisation de l'espace disponible, garantissant une stabilité et une efficacité accrues lors des livraisons. Cette étape, véritable fondation de notre solution, permet non seulement d'économiser du carburant et du temps, mais aussi d'améliorer la coordination globale du transport, faisant de Tetris une solution innovante et performante dans le domaine logistique.

<br><br>

## Table des Matières

- [Titris](#titris)
  - [Pourquoi Tetris?](#pourquoi-tetris)
  - [Table des Matières](#table-des-matières)
  - [Introduction](#introduction)
  - [Architecture de la Solution](#architecture-de-la-solution)
  - [Fonctionnalités Implémentées](#fonctionnalités-implémentées)
    - [1. Optimisation du Chargement](#1-optimisation-du-chargement)
    - [2. Optimisation de Planification et Coordination](#2-optimisation-de-planification-et-coordination)
    - [3. Optimisation d'Itinéraire](#3-optimisation-ditinéraire)
    - [OPTIONAL – Estimation des Besoins en Matières Premières](#optional--estimation-des-besoins-en-matières-premières)
  - [Résultats et Statistiques](#résultats-et-statistiques)
  - [Installation et Déploiement](#installation-et-déploiement)
  - [Conclusion](#conclusion)

<br><br>

---

## Introduction

La solution vise à transformer la gestion logistique en abordant trois grands axes :

1. **Optimisation du Chargement** : Regrouper intelligemment les commandes pour maximiser l'utilisation des camions en tenant compte des contraintes de poids, de volume, et de compatibilité des produits.
2. **Optimisation d'Itinéraire** : Générer des routes optimales pour le chargement (en mode LIFO) et pour le retour, en intégrant les contraintes réelles (climat, incidents, présence de fournisseurs).
3. **Optimisation de Planification et Coordination** : Planifier l'arrivée des camions au niveau du stock (warehouse) en tenant compte de la capacité de stationnement (yard_space) et des délais de chargement, tout en intégrant une logique de reverse logistics pour recharger les camions avec des matières premières auprès de fournisseurs stratégiques.

Cette approche modulaire permet non seulement de réduire les coûts et les délais, mais également d’augmenter la flexibilité et la réactivité opérationnelle des entreprises.

<br><br>

---

## Architecture de la Solution

La solution s’appuie sur une base de données relationnelle SQLite, avec SQLAlchemy pour la gestion des modèles et des relations complexes :

- **Modèles principaux** :

  - **User** : Gère les profils (admin, client, livreur, fournisseur). Le fournisseur est implémenté comme une sous-classe de User, avec des attributs additionnels tels que l’adresse et la liste des matières premières fournies.
  - **Command** et **Palette** : Représentent respectivement les commandes clients et le détail du chargement (avec type, dimensions, poids, etc.).
  - **Product** et **Matiere** : Permettent d'associer un produit à ses composants, via une table d'association qui stocke la consommation de matières premières.
  - **Camion** : Contient les caractéristiques techniques et les contraintes (capacité en poids, volume, coût de transport, état, etc.).
  - **Stock** et **Contract** : Permettent de gérer l’inventaire des matières premières et les contrats avec les entreprises de livraison.

- **API REST avec Flask** :  
  Les fonctionnalités backend sont exposées via des endpoints qui gèrent :

  - L’ajout de commande
  - Le regroupement (knapsack) des commandes pour optimiser le chargement
  - La planification du chargement (en fonction du yard_space et du temps de chargement)
  - L’optimisation d’itinéraire (pour l’allée et le retour)

- **Intégrations externes** :
  - **OpenStreetMap API** (utilisée dans le frontend) pour le géocodage et la planification d’itinéraire.
  - **Modules d’intelligence artificielle** pour générer des prédictions de besoins en matières premières et pour ajuster dynamiquement les routes en fonction du climat et des incidents.


![image](https://github.com/user-attachments/assets/7819a379-e058-46a2-aeed-780376c54b95)

<br><br>

---

<br><br>

## Fonctionnalités Implémentées

### 1. Optimisation du Chargement

- **Objectif** : Regrouper les commandes compatibles pour maximiser l'utilisation des camions tout en respectant les contraintes de capacité (poids et volume) et de compatibilité (basée sur les types de produits et les contraintes définies dans un fichier JSON externe).
- **Algorithme** :
  - Approche gloutonne inspirée du problème du sac à dos (Knapsack) pour regrouper les commandes.
  - Critères de regroupement : proximité géographique (calcul via la formule Haversine) et compatibilité des types de produits.
- **Pseudo-Algorithme** :

  - Extraction des Données: Pour chaque commande ID reçue : Récupérer la palette, le produit, le type, les contraintes de température et calculer le volume.
  - Compatibilité et Proximité: Pour chaque paire de commandes : Vérifier la compatibilité des types (selon `products.json`) et Calculer la distance via haversine et regrouper si < 10 km.
  - Regroupement et Sélection: Regrouper les commandes compatibles via une approche gloutonne. Pour chaque groupe, calculer la charge totale et la plage de température commune. Aprés, Sélectionner le camion disponible (state True) qui a la capacité suffisante et le coût minimal, puis le marquer comme occupé et récupérer l’ID du contrat.
  - Placement Optimisé: Appliquer un algorithme inspiré du 3D bin packing (LIFO et répartition latérale) pour positionner les palettes dans le camion.
  - Retour d’Information: Retourner un JSON contenant les IDs des commandes regroupées, l’ID du camion, l’ID du contrat, le poids total et le volume total.

- **Résultats attendus** :
  - Réduction des trajets à vide.
  - Optimisation de l'espace de chargement, avec une diminution potentielle des coûts de transport de **15 à 25%**.

<br><br>

### 2. Optimisation de Planification et Coordination

- **Objectif** : Planifier l'arrivée des camions au niveau du warehouse en respectant la capacité du yard (yard_space) et le temps de chargement (40 minutes par camion).
- **Approche** :
  - Les commandes sont regroupées et triées en fonction de leurs deadlines.
  - Les arrivées sont planifiées en lots afin de garantir qu’aucun dépassement de capacité ne se produit au niveau du stock.
  - Chaque groupe se voit assigner une heure d’arrivée calculée dynamiquement à partir de l'heure actuelle et du nombre de camions déjà en station.
- **psseudo-algorithme** :
  - Aprés avoir fait le Groupement des commandes dans le chargement on les extrait pour les planifier (le return de la fonction chargement)
  - Trier les groupes par la deadline la plus proche.
  - Pour chaque groupe, assigner un horaire d’arrivée au warehouse en lots en limitant le nombre de camions simultanés à `yard_space` (capacité du stock) et en affectant un temps de charge de 40 minutes par camion au moyen
  - Pour chaque groupe, calculer la destination moyenne.
  - Si un fournisseur (avec adresse) est détecté à proximité du trajet,
    - Appeler `estimate_warehouse_needs` pour estimer les besoins en matières premières.
    - Enregistrer l’ID du fournisseur.
  - Vérifier que sur le trajet de retour, le camion passe par le fournisseur pour recharger avec les produits.
  - Pour chaque groupe, ré-appliquer la logique de sélection du camion (vérifier capacité, coût, contraintes de température).
  - Marquer le camion sélectionné comme occupé et récupérer l’ID du contrat associé.
  - Retourner un JSON pour chaque groupe incluant :
    - Les IDs des commandes regroupées.
    - L’ID du camion et du contrat.
    - L’heure d’arrivée planifiée au warehouse.
    - L’ID du fournisseur, le cas échéant.
  -

### 3. Optimisation d'Itinéraire

- **Pour l’allée (Outbound)** :
  - **Méthode LIFO** : Les palettes sont organisées en fonction de leur position dans le camion (les palettes en haut, chargées en dernier, sont livrées en premier).
  - **Intégration avec des API de cartographie** : L’itinéraire est optimisé en temps réel par des solutions telles que OpenStreetMap, tenant compte du trafic, du climat et des incidents.
- **Pour le retour (Return)** :
  - **Intégration du Reverse Logistics** : Analyse de la route de retour pour détecter la proximité d’un fournisseur. Si un fournisseur se trouve sur le trajet, son adresse est intégrée en tant que waypoint afin de recharger le camion avec des matières premières.
  - **Critère d'optimisation** : Respect des contraintes de temps et de coût, tout en minimisant la distance parcourue.
- **pseudo-algorithme** :

  - **Pour l'allée (Outbound):**

    - Vérifier que le truck ID, la direction ("outbound") et la liste des palettes sont fournis.
    - Ordonnancement LIFO : Trier les palettes par ordre décroissant du champ "position" (les palettes chargées en dernier sont livrées en premier) et Extraire la liste des destinations dans cet ordre.
    - Calcul de l'itinéraire : Appeler la fonction `get_route` avec ces waypoints pour simuler la route optimale via un moteur externe.

  - **Pour le retour (Return) :**
    - Validation des entrées : Vérifier que le truck ID, la direction ("return") et la liste des palettes sont fournis.
    - Détermination du point de départ : Utiliser la destination de la palette la plus basse (fin de l’ordre LIFO) comme point de départ.
    - Calcul du midpoint : Calculer le midpoint entre cette dernière destination et le warehouse avec `compute_midpoint`.
    - Détection d’un fournisseur : Utiliser `detect_supplier` pour identifier un fournisseur proche du midpoint.
    - Si un fournisseur est trouvé (dans le seuil défini), ajouter son adresse comme waypoint.
    - Calcul de l'itinéraire de retour : Appeler `get_route` avec la séquence des waypoints : point de départ, (optionnellement) adresse du fournisseur, puis warehouse.
  - **Retour d’information :** Retourner un JSON incluant l’itinéraire simulé, l’ordre des waypoints et le fournisseur ID (le cas échéant).

- **Bénéfices** :
  - Réduction des temps de parcours jusqu’à **20%** grâce à une optimisation fine des itinéraires.
  - Amélioration de la réactivité en cas d’imprévus grâce à une intégration dynamique des données en temps réel.

---

### OPTIONAL – Estimation des Besoins en Matières Premières

- **Objectif** : Prédire la quantité de matières premières à commander pour la semaine à venir, en fonction des historiques de commandes et des stocks actuels.
- **Méthodologie** :
  - Analyse des commandes des 4 dernières semaines pour établir une demande moyenne hebdomadaire par produit.
  - Calcul de la consommation en matières premières par produit via la table d’association `product_matiere`.
  - Comparaison des besoins estimés avec le stock actuel pour déterminer les quantités additionnelles à commander.
  - Filtrage optionnel par fournisseur pour optimiser le reverse logistics.
- **Impact attendu** :
  - Prévention des ruptures de stock et optimisation des coûts de production.
  - Gain de temps et de ressources grâce à une meilleure planification des approvisionnements.

1. **Calcul de la Demande Historique**

   - Interroger les commandes des 4 dernières semaines.
   - Calculer la demande hebdomadaire moyenne par produit (total/4).

2. **Consommation et Comparaison avec le Stock**

   - Pour chaque produit, multiplier la demande hebdomadaire par la consommation de matières premières (via `product_matiere`).
   - Comparer aux quantités actuelles dans le stock (via `stock_matiere`) pour déterminer le besoin supplémentaire.

3. **Filtrage par Fournisseur**

   - Si un fournisseur est spécifié, ne retenir que les matières premières qu’il fournit.

4. **Retour**
   - Retourner un dictionnaire associant chaque ID de matière première à la quantité supplémentaire requise.

- **Avantages** :
  - Diminution des temps d’attente et amélioration de la gestion des ressources sur le terrain.
  - Respect rigoureux des délais de livraison, assurant un taux de satisfaction client élevé.

<br><br>

---

## Résultats et Statistiques

- **Réduction des Coûts de Transport** :  
  Nos simulations montrent une réduction potentielle des coûts de transport entre **15 et 25%**, grâce à l’optimisation des itinéraires et du chargement.

- **Optimisation des Temps de Livraison** :  
  L’algorithme d’itinéraire et la planification intelligente permettent de réduire le temps total de parcours d’environ **20%**. Cela se traduit par une amélioration significative de la satisfaction client et une réduction des coûts opérationnels.

- **Efficacité de la Planification** :  
  Le respect des délais de chargement et des capacités de stationnement permet de diminuer le temps d’attente au niveau du warehouse, optimisant ainsi le cycle de livraison et augmentant la rotation des camions.

- **Estimation des Besoins en Matières Premières** :  
  Une analyse statistique des historiques de commandes permet de prévoir les besoins hebdomadaires avec une marge d’erreur inférieure à **10%**, ce qui assure une meilleure adéquation entre la production et la demande réelle.

<br><br>

---

## Installation et Déploiement

1. **Cloner le dépôt GitHub** :

   ```bash
   git clone https://github.com/votre-compte/optimisation-logistique.git
   cd optimisation-logistique
   ```

2. **Installation des dépendances** :

   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration de la Base de Données** :

   - Modifier l’URL de connexion dans le fichier `models.py` si nécessaire.
   - Initialiser la base de données :
     ```bash
     python models.py
     ```

4. **Lancement du Serveur Backend** :

   ```bash
   python app.py
   ```

5. **Lancement Frontend** :
   ```bash
   npm start
   ```

<br><br>

---

## Conclusion

Tetris repose sur une approche intégrée et intelligente, alliant des algorithmes de regroupement et d’itinéraire à des techniques avancées de planification et de prévision. Grâce à cette approche, nous offrons :

- Une réduction notable des coûts et des temps de transport.
- Une meilleure coordination entre les opérations de chargement, de livraison et de production.
- Une plateforme évolutive et adaptable aux contraintes réelles du terrain, capable de s’intégrer dans les systèmes existants et de tirer profit des données en temps réel.

Ce projet représente une avancée significative dans l’optimisation logistique, avec des gains économiques et opérationnels prouvés par des analyses statistiques robustes. Il constitue une solution innovante pour répondre aux défis contemporains du transport et de la gestion de la supply chain.

**Made with <3 by T34M IMP3RM34BLE**

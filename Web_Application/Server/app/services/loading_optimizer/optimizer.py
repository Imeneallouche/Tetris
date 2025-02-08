# services/loading_optimizer/optimizer.py
from datetime import datetime
import json
from math import sqrt
from typing import List, Dict, Optional, Tuple
import numpy as np
from itertools import groupby
from operator import attrgetter
import osmnx as ox
import requests
from app.models import Camion, Command, Palette, Product, ProductType, TruckAssignment
from .models import LoadRequirements, Position3D, LoadedPalette, LoadingSuggestion, ProductTypeConstraints
from .utils import load_product_constraints, get_route_distance
from .utils import load_product_constraints, get_route_distance
import networkx as nx


class InitialGroupingOptimizer:
    def __init__(self, products_config_path: str):
        self.product_types = self._load_product_types(products_config_path)
        self.destination_cache = {}
        
    def _load_product_types(self, config_path: str) -> Dict[str, ProductTypeConstraints]:
        """Charge la configuration des types de produits depuis le fichier JSON."""
        with open(config_path, 'r') as f:
            data = json.load(f)
            return {
                pt['type']: ProductTypeConstraints.from_dict(pt)
                for pt in data['product_types']
            }
    
    def optimize_grouping(self, commands: List[Command]) -> Dict[str, List[List[Command]]]:
        """Processus principal d'optimisation du groupement."""
        # 1. Grouper par date
        date_groups = self._group_by_delivery_date(commands)
        
        final_groups = {}
        for date, date_commands in date_groups.items():
            # 2. Grouper par compatibilité de produits
            product_compatible_groups = self._group_by_product_compatibility(date_commands)
            
            # 3. Pour chaque groupe compatible, vérifier les routes
            route_groups = []
            for prod_group in product_compatible_groups:
                route_compatible = self._group_by_route_compatibility(prod_group)
                route_groups.extend(route_compatible)
                
            final_groups[date] = route_groups
            
        return final_groups
    
    def _group_by_delivery_date(self, commands: List[Command]) -> Dict[str, List[Command]]:
        """Groupe les commandes par date de livraison."""
        sorted_commands = sorted(commands, key=attrgetter('delivery_date'))
        return {
            date.strftime('%Y-%m-%d'): list(group)
            for date, group in groupby(sorted_commands, key=lambda x: x.delivery_date.date())
        }
    
    def _are_products_compatible(self, products1: List[Product], products2: List[Product]) -> bool:
        """Vérifie si deux ensembles de produits sont compatibles."""
        # Récupérer tous les types de produits pour les deux groupes
        types1 = {p.type for p in products1}
        types2 = {p.type for p in products2}
        
        # Vérifier les incompatibilités
        for type1 in types1:
            prod_type1 = self.product_types[type1]
            for type2 in types2:
                prod_type2 = self.product_types[type2]
                
                # Vérifier les incompatibilités directes
                if (type2 in prod_type1.incompatible_types or 
                    type1 in prod_type2.incompatible_types):
                    return False
                
                # Vérifier la compatibilité des températures
                temp_range1 = (prod_type1.min_temperature, prod_type1.max_temperature)
                temp_range2 = (prod_type2.min_temperature, prod_type2.max_temperature)
                
                if not (temp_range1[1] >= temp_range2[0] and 
                       temp_range2[1] >= temp_range1[0]):
                    return False
                
        return True
    
    def _group_by_product_compatibility(self, commands: List[Command]) -> List[List[Command]]:
        """Groupe les commandes par compatibilité de produits."""
        if not commands:
            return []
            
        groups = []
        remaining_commands = commands.copy()
        
        while remaining_commands:
            current_group = [remaining_commands.pop(0)]
            
            i = 0
            while i < len(remaining_commands):
                cmd = remaining_commands[i]
                # Vérifier la compatibilité avec tous les produits du groupe actuel
                compatible = all(
                    self._are_products_compatible(
                        existing_cmd.products, 
                        cmd.products
                    )
                    for existing_cmd in current_group
                )
                
                if compatible:
                    current_group.append(cmd)
                    remaining_commands.pop(i)
                else:
                    i += 1
                    
            groups.append(current_group)
            
        return groups
    
    def _get_coordinates(self, address: str) -> tuple[float, float]:
        """Récupère les coordonnées d'une adresse via OpenStreetMap."""
        if address in self.destination_cache:
            return self.destination_cache[address]
            
        try:
            headers = {'User-Agent': 'LogixSync/1.0'}
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            if response.json():
                location = response.json()[0]
                coords = (float(location['lon']), float(location['lat']))
                self.destination_cache[address] = coords
                return coords
                
        except Exception as e:
            print(f"Erreur lors de la récupération des coordonnées pour {address}: {e}")
            
        return None
        
    def _calculate_route_compatibility(self, coord1: tuple, coord2: tuple) -> float:
        """Calcule la compatibilité de route entre deux points."""
        try:
            # Créer un graphe routier autour des points
            center_lat = (coord1[1] + coord2[1]) / 2
            center_lon = (coord1[0] + coord2[0]) / 2
            
            # Calculer la distance à vol d'oiseau
            direct_dist = ox.distance.great_circle(coord1[1], coord1[0], 
                                                 coord2[1], coord2[0])
                                                 
            # Récupérer le graphe routier
            G = ox.graph_from_point((center_lat, center_lon), 
                                  dist=direct_dist*1.5, 
                                  network_type='drive')
                                  
            # Trouver les nœuds les plus proches
            origin_node = ox.distance.nearest_nodes(G, coord1[0], coord1[1])
            dest_node = ox.distance.nearest_nodes(G, coord2[0], coord2[1])
            
            # Calculer le plus court chemin
            route = nx.shortest_path(G, origin_node, dest_node, weight='length')
            route_length = sum(ox.utils_graph.get_route_edge_attributes(G, route, 'length'))
            
            # Si la route est moins de 30% plus longue que la distance directe,
            # considérer les destinations comme compatibles
            return route_length <= direct_dist * 1.3
            
        except Exception as e:
            print(f"Erreur lors du calcul de la route: {e}")
            return False
    
    def _group_by_route_compatibility(self, commands: List[Command]) -> List[List[Command]]:
        """Groupe les commandes par compatibilité de route."""
        if not commands:
            return []
            
        # Récupérer les coordonnées de toutes les destinations
        destinations = {}
        for cmd in commands:
            coords = self._get_coordinates(cmd.destination)
            if coords:
                destinations[cmd.destination] = coords
                
        groups = []
        remaining_commands = commands.copy()
        
        while remaining_commands:
            current_group = [remaining_commands.pop(0)]
            current_dest = current_group[0].destination
            
            if current_dest not in destinations:
                continue
                
            i = 0
            while i < len(remaining_commands):
                cmd = remaining_commands[i]
                dest = cmd.destination
                
                if dest not in destinations:
                    i += 1
                    continue
                    
                # Vérifier la compatibilité de route avec toutes les destinations du groupe
                compatible = all(
                    self._calculate_route_compatibility(
                        destinations[existing_cmd.destination],
                        destinations[dest]
                    )
                    for existing_cmd in current_group
                )
                
                if compatible:
                    current_group.append(cmd)
                    remaining_commands.pop(i)
                else:
                    i += 1
                    
            groups.append(current_group)
            
        return groups

class TruckLoadingOptimizer:
    def __init__(self, available_trucks: List['Camion']):
        self.available_trucks = [truck for truck in available_trucks if truck.state]
        
    def calculate_load_requirements(self, command_group: List['Command']) -> LoadRequirements:
        """Calcule les besoins totaux pour un groupe de commandes."""
        total_volume = 0
        total_weight = 0
        needs_refrigeration = False
        min_temp = float('inf')
        palette_counts = {"european": 0, "american": 0}

        for cmd in command_group:
            for palette in cmd.palettes:
                total_volume += palette.volume
                total_weight += palette.total_weight

                # Récupérer les spécifications du produit
                product_specs = self.get_product_type_specs(palette.prod.type)
                
                # Vérifier si une température est requise
                if product_specs["min_temperature"] is not None or product_specs["max_temperature"] is not None:
                    needs_refrigeration = True
                    if product_specs["min_temperature"] is not None:
                        min_temp = min(min_temp, product_specs["min_temperature"])
                
                # Compter les palettes
                if palette.prod.palette_type:
                    palette_counts[palette.prod.palette_type] += 1

        return LoadRequirements(
            total_volume=total_volume,
            total_weight=total_weight,
            needs_refrigeration=needs_refrigeration,
            temperature_required=min_temp if min_temp != float('inf') else None,
            num_palettes=sum(palette_counts.values())
        )

    def get_product_type_specs(self, product_type: str) -> dict:
        """Récupère les spécifications d'un type de produit à partir du fichier JSON."""
        with open("Server/products.json", "r") as file:
            data = json.load(file)
        
        for product in data["product_types"]:
            if product["type"] == product_type:
                return product  # Retourne les spécifications du produit

        return {"min_temperature": None, "max_temperature": None}  # Valeurs par défaut si non trouvé

        
    def calculate_truck_compatibility(self, truck: 'Camion', requirements: LoadRequirements) -> float:
        """Calcule un score de compatibilité entre 0 et 1 pour un camion."""

        truck_specs = truck.specifications  # Récupération des spécifications du camion

        # Vérifier si le camion peut transporter des produits réfrigérés
        if requirements.needs_refrigeration:
            if not truck_specs["frigo"]:  # On regarde dans les spécifications
                return 0  # Ce camion ne peut pas transporter de produits réfrigérés
            
            if requirements.temperature_required is not None:
                # On suppose que la température du camion est stockée dans truck.temperature
                if truck.temperature is None or not (truck.temperature <= requirements.temperature_required):
                    return 0  # La température minimale requise n'est pas respectée

        # Vérifier les capacités de base du camion
        if requirements.total_volume > truck_specs["volume"] or \
        requirements.total_weight > truck_specs["charge_utile"]:
            return 0  # Le camion ne peut pas supporter la charge demandée

        # Vérifier la capacité en palettes
        if requirements.palette_type == "european":
            truck_palette_capacity = truck_specs["palettes_euro"]
        else:
            truck_palette_capacity = truck_specs["palettes_us"]
        
        if truck_palette_capacity < requirements.num_palettes:
            return 0  # Pas assez d'espace pour les palettes

        # Calculer les scores d'utilisation
        volume_score = requirements.total_volume / truck_specs["volume"]
        weight_score = requirements.total_weight / truck_specs["charge_utile"]
        palette_score = requirements.num_palettes / truck_palette_capacity

        # Pénaliser la sous-utilisation et la sur-utilisation
        def utilization_score(ratio):
            if ratio > 1:
                return 0
            if 0.75 <= ratio <= 0.9:
                return 1
            if ratio < 0.75:
                return ratio / 0.75
            return 1 - ((ratio - 0.9) / 0.1)

        scores = [
            utilization_score(volume_score),
            utilization_score(weight_score),
            utilization_score(palette_score)
        ]

        return np.mean(scores)

    
    def optimize_truck_assignment(self, 
                                command_groups: List[List['Command']]) -> Dict[str, TruckAssignment]:
        """Optimise l'attribution des camions pour tous les groupes de commandes."""
        assignments = {}
        used_trucks = set()
        
        # Trier les groupes par volume total décroissant
        sorted_groups = sorted(
            command_groups,
            key=lambda g: self.calculate_load_requirements(g).total_volume,
            reverse=True
        )
        
        for group in sorted_groups:
            requirements = self.calculate_load_requirements(group)
            
            # Trouver le meilleur camion disponible
            best_truck = None
            best_score = -1
            
            for truck in self.available_trucks:
                if truck.id in used_trucks:
                    continue
                    
                score = self.calculate_truck_compatibility(truck, requirements)
                if score > best_score:
                    best_score = score
                    best_truck = truck
            
            if best_truck and best_score > 0:
                used_trucks.add(best_truck.id)
                assignments[best_truck.id] = TruckAssignment(
                    truck_id=best_truck.id,
                    commands=[cmd.id for cmd in group],
                    utilization_score=best_score,
                    volume_usage=requirements.total_volume / best_truck.volume_max,
                    weight_usage=requirements.total_weight / best_truck.poids_max
                )
            else:
                print(f"Impossible de trouver un camion adapté pour le groupe")
        
        return assignments


class TruckLoadingOptimizer:
    def __init__(self, db_session, config_path: str):
        self.session = db_session
        self.product_constraints = load_product_constraints(config_path)
        self.min_spacing = 0.1  # Minimum space between palettes (meters)

    def optimize_loading(self, commands: List['Command'], available_trucks: List['Camion']) -> Dict[int, LoadingSuggestion]:
        """Main optimization function for loading palettes into trucks."""
        # Group commands by delivery date
        date_grouped_commands = self._group_by_delivery_date(commands)
        loading_suggestions = {}

        for date, date_commands in date_grouped_commands.items():
            # Group by compatible routes (filtre par date)
            route_groups = self._group_by_route_compatibility(date_commands)
            
            for route_group in route_groups:
                # Find optimal truck combination
                truck_assignments = self._optimize_truck_assignment(route_group, available_trucks)
                
                for truck_id, assigned_palettes in truck_assignments.items():
                    truck = next(t for t in available_trucks if t.id == truck_id)
                    loading_plan = self._optimize_loading_arrangement(
                        assigned_palettes,
                        truck
                    )
                    
                    if loading_plan:
                        loading_suggestions[truck_id] = loading_plan

        return loading_suggestions

    def _group_by_delivery_date(self, commands: List['Command']) -> Dict[str, List['Command']]:
        """Group commands by delivery date."""
        sorted_commands = sorted(commands, key=attrgetter('delivery_date'))
        return {
            date: list(group)
            for date, group in groupby(sorted_commands, key=attrgetter('delivery_date'))
        }

    def _group_by_route_compatibility(self, commands: List['Command']) -> List[List['Command']]:
        """Group commands by route compatibility using a simple distance-based approach."""
        if not commands:
            return []

        # Get all unique destinations
        destinations = list(set(cmd.destination for cmd in commands))
        
        # Calculate distances between all pairs
        distances = {}
        for i, dest1 in enumerate(destinations):
            for dest2 in destinations[i+1:]:
                dist = get_route_distance([dest1], [dest2])[0]
                distances[(dest1, dest2)] = dist
                distances[(dest2, dest1)] = dist
        
        # Simple greedy clustering
        groups = []
        remaining_commands = commands.copy()
        
        while remaining_commands:
            current_group = [remaining_commands.pop(0)]
            center = current_group[0].destination
            
            # Find all commands within threshold distance
            i = 0
            while i < len(remaining_commands):
                cmd = remaining_commands[i]
                key = (center, cmd.destination)
                if distances.get(key, float('inf')) <= 50:  # 50km threshold
                    current_group.append(cmd)
                    remaining_commands.pop(i)
                else:
                    i += 1
            
            groups.append(current_group)
        
        return groups

    def _optimize_truck_assignment(
        self,
        commands: List['Command'],
        available_trucks: List['Camion']
    ) -> Dict[int, List['Palette']]:
        """Optimize assignment of palettes to trucks."""
        # Sort trucks by cost efficiency
        sorted_trucks = sorted(
            available_trucks,
            key=lambda t: t.transport_cost / t.specifications['volume']
        )
        
        # Group palettes by product type and temperature requirements
        palette_groups = self._group_palettes_by_constraints(
            [p for cmd in commands for p in cmd.palettes]
        )
        
        assignments = {}
        
        for group in palette_groups:
            # Find suitable trucks for this group
            suitable_trucks = self._find_suitable_trucks(group, sorted_trucks)
            
            if not suitable_trucks:
                continue
                
            # Try to fit in single truck first
            best_truck = self._find_best_fitting_truck(group, suitable_trucks)
            
            if best_truck:
                assignments[best_truck.id] = assignments.get(best_truck.id, []) + group
            else:
                # Split between multiple trucks if necessary
                self._split_between_trucks(group, suitable_trucks, assignments)
                
        return assignments

    def _optimize_loading_arrangement(
        self,
        palettes: List['Palette'],
        truck: 'Camion'
    ) -> Optional[LoadingSuggestion]:
        """Optimize the physical arrangement of palettes in a truck."""
        # Sort palettes by various criteria
        sorted_palettes = self._sort_palettes_for_loading(palettes)
        
        # Initialize 3D space representation
        truck_space = self._initialize_truck_space(truck)
        loaded_palettes = []
        
        for palette in sorted_palettes:
            position = self._find_optimal_position(
                palette,
                truck_space,
                loaded_palettes,
                truck
            )
            
            if position:
                loaded_palette = LoadedPalette(
                    palette_id=palette.id,
                    position=position,
                    weight=palette.weight,
                    dimensions=self._get_palette_dimensions(palette),
                    product_type=palette.product.type,
                    destination=palette.command.destination,
                    is_rotated=position.rotation == 90
                )
                loaded_palettes.append(loaded_palette)
                self._update_truck_space(truck_space, loaded_palette)
            else:
                return None  # Loading arrangement not possible
                
        # Calculate metrics
        weight_score = self._calculate_weight_distribution_score(loaded_palettes)
        space_score = self._calculate_space_utilization(loaded_palettes, truck)
        
        return LoadingSuggestion(
            truck_id=truck.id,
            loaded_palettes=loaded_palettes,
            weight_distribution_score=weight_score,
            space_utilization=space_score,
            estimated_cost=truck.transport_cost
        )

    def _find_optimal_position(
        self,
        palette: 'Palette',
        truck_space: np.ndarray,
        loaded_palettes: List[LoadedPalette],
        truck: 'Camion'
    ) -> Optional[Position3D]:
        """Find optimal position for a palette considering all constraints."""
        dimensions = self._get_palette_dimensions(palette)
        constraints = self.product_constraints[palette.product.type]
        
        # Try both orientations if allowed
        orientations = [(0, dimensions)]
        if constraints.rotatable:
            orientations.append((
                90,
                {
                    'length': dimensions['width'],
                    'width': dimensions['length'],
                    'height': dimensions['height']
                }
            ))
            
        best_position = None
        best_score = float('-inf')
        
        for rotation, dims in orientations:
            # Get all possible positions
            positions = self._generate_possible_positions(truck_space, dims)
            
            for pos in positions:
                if self._is_position_valid(pos, dims, palette, loaded_palettes):
                    score = self._evaluate_position(
                        pos,
                        dims,
                        palette,
                        loaded_palettes,
                        truck
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_position = Position3D(
                            x=pos[0],
                            y=pos[1],
                            z=pos[2],
                            rotation=rotation
                        )
                        
        return best_position

    def _is_position_valid(
        self,
        position: Tuple[float, float, float],
        dimensions: Dict[str, float],
        palette: 'Palette',
        loaded_palettes: List[LoadedPalette]
    ) -> bool:
        """Validate position against all constraints."""
        x, y, z = position
        
        # Check basic boundaries
        if not self._is_within_bounds(position, dimensions):
            return False
            
        # Check collisions
        if self._has_collision(position, dimensions, loaded_palettes):
            return False
            
        # Check weight stacking
        if not self._is_weight_stack_valid(position, dimensions, palette, loaded_palettes):
            return False
            
        # Check fragility constraints
        if not self._check_fragility_constraints(position, dimensions, palette, loaded_palettes):
            return False
            
        # Check product compatibility
        if not self._check_product_compatibility(palette, loaded_palettes):
            return False
            
        return True

    def _evaluate_position(
        self,
        position: Tuple[float, float, float],
        dimensions: Dict[str, float],
        palette: 'Palette',
        loaded_palettes: List[LoadedPalette],
        truck: 'Camion'
    ) -> float:
        """Score a potential position based on multiple criteria."""
        scores = [
            (0.3, self._evaluate_weight_distribution(position, palette, loaded_palettes)),
            (0.3, self._evaluate_loading_sequence(position, palette, loaded_palettes)),
            (0.2, self._evaluate_space_utilization(position, dimensions, truck)),
            (0.2, self._evaluate_stability(position, dimensions, loaded_palettes))
        ]
        
        return sum(weight * score for weight, score in scores)

    def _evaluate_weight_distribution(
        self,
        position: Tuple[float, float, float],
        palette: 'Palette',
        loaded_palettes: List[LoadedPalette]
    ) -> float:
        """Evaluate weight distribution balance."""
        x, y, z = position
        
        # Calculate center of gravity
        total_weight = palette.weight + sum(p.weight for p in loaded_palettes)
        current_cog_x = sum(p.position.x * p.weight for p in loaded_palettes)
        current_cog_y = sum(p.position.y * p.weight for p in loaded_palettes)
        
        new_cog_x = (current_cog_x + x * palette.weight) / total_weight
        new_cog_y = (current_cog_y + y * palette.weight) / total_weight
        
        # Ideal center of gravity is in the middle
        ideal_x = self.truck_dimensions['length'] / 2
        ideal_y = self.truck_dimensions['width'] / 2
        
        # Calculate deviation from ideal
        deviation = sqrt((new_cog_x - ideal_x)**2 + (new_cog_y - ideal_y)**2)
        max_deviation = sqrt((self.truck_dimensions['length']/2)**2 + 
                           (self.truck_dimensions['width']/2)**2)
        
        return 1 - (deviation / max_deviation)

    def _evaluate_loading_sequence(
        self,
        position: Tuple[float, float, float],
        palette: 'Palette',
        loaded_palettes: List[LoadedPalette]
    ) -> float:
        """Evaluate position based on loading/unloading sequence."""
        x, _, _ = position

    def _group_palettes_by_constraints(self, palettes: List['Palette']) -> List[List['Palette']]:
        """
        Groupe les palettes selon leurs contraintes (température, type, incompatibilités)
        """
        palette_groups = []
        remaining_palettes = palettes.copy()
        
        while remaining_palettes:
            current_group = [remaining_palettes.pop(0)]
            base_constraints = self.product_constraints[current_group[0].product.type]
            base_temp_range = (base_constraints.min_temperature, base_constraints.max_temperature)
            
            i = 0
            while i < len(remaining_palettes):
                palette = remaining_palettes[i]
                constraints = self.product_constraints[palette.product.type]
                
                # Vérifier les incompatibilités
                if (palette.product.type in base_constraints.incompatible_types or
                    current_group[0].product.type in constraints.incompatible_types):
                    i += 1
                    continue
                    
                # Vérifier la compatibilité des températures
                temp_range = (constraints.min_temperature, constraints.max_temperature)
                if (temp_range[1] >= base_temp_range[0] and 
                    base_temp_range[1] >= temp_range[0]):
                    current_group.append(palette)
                    remaining_palettes.pop(i)
                else:
                    i += 1
                    
            palette_groups.append(current_group)
        
        return palette_groups

    def _find_suitable_trucks(self, palettes: List['Palette'], available_trucks: List['Camion']) -> List['Camion']:
        """
        Trouve les camions adaptés pour un groupe de palettes.
        """
        total_volume = sum(p.volume for p in palettes)
        total_weight = sum(p.weight for p in palettes)
        
        # Déterminer les besoins en température
        needs_temp_control = False
        min_temp = float('inf')
        max_temp = float('-inf')
        
        for palette in palettes:
            constraints = self.product_constraints[palette.product.type]
            if constraints.min_temperature is not None:
                needs_temp_control = True
                min_temp = min(min_temp, constraints.min_temperature)
            if constraints.max_temperature is not None:
                needs_temp_control = True
                max_temp = max(max_temp, constraints.max_temperature)
        
        suitable_trucks = []
        for truck in available_trucks:
            specs = truck.specifications
            
            # Vérifier la capacité de base
            if (specs['volume'] < total_volume or 
                specs['charge_utile'] < total_weight):
                continue
                
            # Vérifier les besoins en température
            if needs_temp_control:
                if not specs['frigo']:
                    continue
                if not (truck.temperature <= min_temp):
                    continue
                    
            suitable_trucks.append(truck)
        
        return suitable_trucks

    def _find_best_fitting_truck(self, palettes: List['Palette'], trucks: List['Camion']) -> Optional['Camion']:
        """
        Trouve le camion le plus adapté pour un groupe de palettes.
        """
        total_volume = sum(p.volume for p in palettes)
        total_weight = sum(p.weight for p in palettes)
        
        best_truck = None
        best_score = float('-inf')
        
        for truck in trucks:
            # Calculer les ratios d'utilisation
            volume_ratio = total_volume / truck.specifications['volume']
            weight_ratio = total_weight / truck.specifications['charge_utile']
            
            # Le score optimal est proche de 0.85 (85% d'utilisation)
            volume_score = 1 - abs(0.85 - volume_ratio)
            weight_score = 1 - abs(0.85 - weight_ratio)
            
            # Inclure le coût de transport dans le score
            cost_per_unit = truck.transport_cost / (truck.specifications['volume'] * truck.specifications['charge_utile'])
            cost_score = 1 / (1 + cost_per_unit)  # Normaliser le score de coût
            
            # Score final pondéré
            score = (0.4 * volume_score + 0.4 * weight_score + 0.2 * cost_score)
            
            if score > best_score and volume_ratio <= 1 and weight_ratio <= 1:
                best_score = score
                best_truck = truck
        
        return best_truck

    def _split_between_trucks(self, palettes: List['Palette'], trucks: List['Camion'], assignments: Dict[int, List['Palette']]):
        """
        Répartit les palettes entre plusieurs camions si nécessaire.
        """
        remaining_palettes = palettes.copy()
        
        while remaining_palettes:
            # Créer un sous-groupe de palettes qui peut tenir dans un camion
            current_group = []
            total_volume = 0
            total_weight = 0
            
            for palette in remaining_palettes[:]:
                if (total_volume + palette.volume <= trucks[0].specifications['volume'] and
                    total_weight + palette.weight <= trucks[0].specifications['charge_utile']):
                    current_group.append(palette)
                    total_volume += palette.volume
                    total_weight += palette.weight
                    remaining_palettes.remove(palette)
                    
            if current_group:
                # Trouver le meilleur camion pour ce sous-groupe
                best_truck = self._find_best_fitting_truck(current_group, trucks)
                if best_truck:
                    assignments[best_truck.id] = assignments.get(best_truck.id, []) + current_group
                    # Retirer le camion utilisé
                    trucks = [t for t in trucks if t.id != best_truck.id]
            else:
                # Impossible de diviser davantage
                break

    def _sort_palettes_for_loading(self, palettes: List['Palette']) -> List['Palette']:
        """
        Trie les palettes pour optimiser le chargement.
        """
        # Créer une liste de tuples (palette, score) pour le tri
        scored_palettes = []
        for palette in palettes:
            constraints = self.product_constraints[palette.product.type]
            
            # Calculer un score basé sur plusieurs critères
            score = 0
            # Priorité aux objets lourds (ils vont en bas)
            score += palette.weight * 0.4
            # Priorité aux objets non-fragiles
            score += (0 if constraints.fragility else 1) * 0.3
            # Priorité aux objets non-rotatifs (plus difficiles à placer)
            score += (0 if constraints.rotatable else 1) * 0.2
            # Priorité aux gros volumes
            score += (palette.volume / max(p.volume for p in palettes)) * 0.1
            
            scored_palettes.append((palette, score))
        
        # Trier par score décroissant
        return [p for p, _ in sorted(scored_palettes, key=lambda x: x[1], reverse=True)]

    def _initialize_truck_space(self, truck: 'Camion') -> np.ndarray:
        """
        Initialise l'espace 3D du camion.
        """
        # Créer une grille 3D avec une résolution de 10cm
        resolution = 0.1  # mètres
        length = int(truck.specifications['length'] / resolution)
        width = int(truck.specifications['width'] / resolution)
        height = int(truck.specifications['height'] / resolution)
        
        # 0 = espace libre, 1 = espace occupé
        return np.zeros((length, width, height), dtype=np.int8)

    def _get_palette_dimensions(self, palette: 'Palette') -> Dict[str, float]:
        """
        Récupère les dimensions d'une palette.
        """
        return {
            'length': palette.length,
            'width': palette.width,
            'height': palette.height
        }

    def _calculate_weight_distribution_score(self, loaded_palettes: List[LoadedPalette]) -> float:
        """
        Calcule un score pour la distribution du poids.
        """
        if not loaded_palettes:
            return 1.0
            
        # Calculer le centre de gravité
        total_weight = sum(p.weight for p in loaded_palettes)
        cog_x = sum(p.position.x * p.weight for p in loaded_palettes) / total_weight
        cog_y = sum(p.position.y * p.weight for p in loaded_palettes) / total_weight
        
        # Position idéale au centre du camion
        ideal_x = self.truck_dimensions['length'] / 2
        ideal_y = self.truck_dimensions['width'] / 2
        
        # Calculer la déviation normalisée
        max_deviation = sqrt((self.truck_dimensions['length']/2)**2 + 
                            (self.truck_dimensions['width']/2)**2)
        actual_deviation = sqrt((cog_x - ideal_x)**2 + (cog_y - ideal_y)**2)
        
        return 1 - (actual_deviation / max_deviation)

    def _calculate_space_utilization(self, loaded_palettes: List[LoadedPalette], truck: 'Camion') -> float:
        """
        Calcule le taux d'utilisation de l'espace.
        """
        total_volume = truck.specifications['volume']
        used_volume = sum(
            p.dimensions['length'] * p.dimensions['width'] * p.dimensions['height']
            for p in loaded_palettes
        )
        
        return used_volume / total_volume

    def _generate_possible_positions(self, truck_space: np.ndarray, dimensions: Dict[str, float]) -> List[Tuple[float, float, float]]:
        """
        Génère toutes les positions possibles pour une palette.
        """
        resolution = 0.1  # mètres
        positions = []
        
        # Convertir les dimensions en indices de grille
        length = int(dimensions['length'] / resolution)
        width = int(dimensions['width'] / resolution)
        height = int(dimensions['height'] / resolution)
        
        # Parcourir l'espace du camion
        for x in range(truck_space.shape[0] - length + 1):
            for y in range(truck_space.shape[1] - width + 1):
                for z in range(truck_space.shape[2] - height + 1):
                    # Convertir les indices en mètres
                    pos = (x * resolution, y * resolution, z * resolution)
                    positions.append(pos)
        
        return positions

    def _is_within_bounds(self, position: Tuple[float, float, float], dimensions: Dict[str, float]) -> bool:
        """
        Vérifie si une position est dans les limites du camion.
        """
        x, y, z = position
        return (0 <= x + dimensions['length'] <= self.truck_dimensions['length'] and
                0 <= y + dimensions['width'] <= self.truck_dimensions['width'] and
                0 <= z + dimensions['height'] <= self.truck_dimensions['height'])

    def _has_collision(self, position: Tuple[float, float, float], dimensions: Dict[str, float], 
                    loaded_palettes: List[LoadedPalette]) -> bool:
        """
        Vérifie s'il y a collision avec d'autres palettes.
        """
        x, y, z = position
        for palette in loaded_palettes:
            # Vérifier le chevauchement sur chaque axe
            x_overlap = (x < palette.position.x + palette.dimensions['length'] and 
                        x + dimensions['length'] > palette.position.x)
            y_overlap = (y < palette.position.y + palette.dimensions['width'] and 
                        y + dimensions['width'] > palette.position.y)
            z_overlap = (z < palette.position.z + palette.dimensions['height'] and 
                        z + dimensions['height'] > palette.position.z)
            
            if x_overlap and y_overlap and z_overlap:
                return True
        
        return False

    def _is_weight_stack_valid(self, position: Tuple[float, float, float], dimensions: Dict[str, float],
                            palette: 'Palette', loaded_palettes: List[LoadedPalette]) -> bool:
        """
        Vérifie si l'empilement des poids est valide.
        """
        x, y, z = position
        
        # Vérifier les palettes en dessous
        for loaded in loaded_palettes:
            if (loaded.position.z + loaded.dimensions['height'] == z and  # Contact direct
                loaded.weight < palette.weight):  # Palette plus légère en dessous
                # Vérifier le chevauchement horizontal
                x_overlap = (x < loaded.position.x + loaded.dimensions['length'] and 
                            x + dimensions['length'] > loaded.position.x)
                y_overlap = (y < loaded.position.y + loaded.dimensions['width'] and 
                            y + dimensions['width'] > loaded.position.y)
                
                if x_overlap and y_overlap:
                    return False
        
        return True

    def _check_fragility_constraints(self, position: Tuple[float, float, float], dimensions: Dict[str, float],
                                palette: 'Palette', loaded_palettes: List[LoadedPalette]) -> bool:
        """
        Vérifie les contraintes de fragilité.
        """
        x, y, z = position
        palette_constraints = self.product_constraints[palette.product.type]
        
        # Si la palette est fragile, vérifier qu'il n'y a rien au-dessus
        if palette_constraints.fragility:
            for loaded in loaded_palettes:
                if loaded.position.z > z:  # Palette au-dessus
                    # Vérifier le chevauchement horizontal
                    x_overlap = (x < loaded.position.x + loaded.dimensions['length'] and 
                                x + dimensions['length'] > loaded.position.x)
                    y_overlap = (y < loaded.position.y + loaded.dimensions['width'] and 
                                y + dimensions['width'] > loaded.position.y)
                    
                    if x_overlap and y_overlap:
                        return False
        
        return True

    def _check_product_compatibility(self, palette: 'Palette', loaded_palettes: List[LoadedPalette]) -> bool:
        """
        Vérifie la compatibilité des produits.
        """
        palette_constraints = self.product_constraints[palette.product.type]
        
        for loaded in loaded_palettes:
            loaded_constraints = self.product_constraints[loaded.product_type]
            
            # Vérifier les incompatibilités directes
            if (loaded.product_type in palette_constraints.incompatible_types or
                palette.product.type in loaded_constraints.incompatible_types):
                return False
        
        return True

    def _evaluate_space_utilization(self, position: Tuple[float, float, float], dimensions: Dict[str, float],
                              truck: 'Camion') -> float:
        """
        Évalue l'utilisation de l'espace pour une position donnée.
        
        Retourne un score entre 0 et 1, où 1 représente une utilisation optimale de l'espace.
        """
        x, y, z = position
        
        # Calculer la distance aux parois du camion
        dist_to_walls = [
            x,  # Distance à la paroi avant
            truck.specifications['length'] - (x + dimensions['length']),  # Distance à la paroi arrière
            y,  # Distance à la paroi gauche
            truck.specifications['width'] - (y + dimensions['width']),  # Distance à la paroi droite
            z,  # Distance au plancher
            truck.specifications['height'] - (z + dimensions['height'])  # Distance au plafond
        ]
        
        # Pénaliser les grands espaces vides
        max_gap = max(dist_to_walls)
        gap_score = 1 - (max_gap / max(truck.specifications['length'], 
                                    truck.specifications['width'],
                                    truck.specifications['height']))
        
        # Favoriser le placement près des parois et du sol
        contact_score = sum(1 for dist in dist_to_walls if dist < 0.1) / 6
        
        # Combiner les scores avec des poids
        return 0.7 * gap_score + 0.3 * contact_score

    def _evaluate_stability(self, position: Tuple[float, float, float], dimensions: Dict[str, float],
                        loaded_palettes: List[LoadedPalette]) -> float:
        """
        Évalue la stabilité de la palette à la position donnée.
        
        Retourne un score entre 0 et 1, où 1 représente une stabilité maximale.
        """
        x, y, z = position
        
        if z == 0:  # Au sol = stabilité maximale
            return 1.0
            
        # Calculer la surface de support nécessaire
        required_support = dimensions['length'] * dimensions['width']
        actual_support = 0
        
        # Trouver les palettes qui supportent directement cette position
        supporting_palettes = []
        for palette in loaded_palettes:
            if abs(palette.position.z + palette.dimensions['height'] - z) < 0.01:  # Contact direct
                # Calculer la surface de chevauchement
                x_overlap = max(0, min(x + dimensions['length'], 
                                    palette.position.x + palette.dimensions['length']) -
                                max(x, palette.position.x))
                y_overlap = max(0, min(y + dimensions['width'],
                                    palette.position.y + palette.dimensions['width']) -
                                max(y, palette.position.y))
                
                overlap_area = x_overlap * y_overlap
                actual_support += overlap_area
                supporting_palettes.append((palette, overlap_area))
        
        # Score de support de base
        support_score = min(1.0, actual_support / required_support)
        
        # Bonus pour une distribution équilibrée du support
        if supporting_palettes:
            total_support = sum(area for _, area in supporting_palettes)
            max_support_ratio = max(area / total_support for _, area in supporting_palettes)
            distribution_score = 1 - (max_support_ratio - 1/len(supporting_palettes))
        else:
            distribution_score = 0
        
        # Points bonus pour support aux coins
        corners_supported = 0
        corner_positions = [
            (x, y),
            (x + dimensions['length'], y),
            (x, y + dimensions['width']),
            (x + dimensions['length'], y + dimensions['width'])
        ]
        
        for corner_x, corner_y in corner_positions:
            for palette, _ in supporting_palettes:
                if (palette.position.x <= corner_x <= palette.position.x + palette.dimensions['length'] and
                    palette.position.y <= corner_y <= palette.position.y + palette.dimensions['width']):
                    corners_supported += 1
                    break
        
        corner_score = corners_supported / 4
        
        # Combiner tous les scores avec des poids appropriés
        final_score = (0.5 * support_score + 
                    0.3 * distribution_score +
                    0.2 * corner_score)
        
        return final_score
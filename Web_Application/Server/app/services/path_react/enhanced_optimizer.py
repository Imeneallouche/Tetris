
# enhanced_optimizer.py
from typing import Dict, List

from sqlalchemy import Tuple
from Web_Application.Server.app.services.path_react.osm_manager import OSMManager
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np

class EnhancedOptimizer:
    def __init__(self, osm_manager: OSMManager):
        self.osm_manager = osm_manager
        self.manager = None
        self.routing = None
        self.solution = None
        
    def optimize_route(self, locations: List[Dict], 
                      vehicle_capacity: int = 0,
                      time_windows: List[Tuple] = None) -> Tuple[List, List[List[Tuple[float, float]]]]:
        """
        Optimise une route avec contraintes de capacité et fenêtres temporelles
        """
        # Création de la matrice de distance
        coords = [(loc['latitude'], loc['longitude']) for loc in locations]
        distance_matrix = self.osm_manager.calculate_route_matrix(coords)
        
        # Configuration du problème
        manager = pywrapcp.RoutingIndexManager(len(locations), 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 1000)

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Ajout des contraintes de capacité si nécessaire
        if vehicle_capacity > 0:
            def demand_callback(from_index):
                node = manager.IndexToNode(from_index)
                return locations[node].get('demand', 0)

            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                [vehicle_capacity],  # vehicle maximum capacities
                True,  # start cumul to zero
                'Capacity'
            )

        # Ajout des fenêtres temporelles si spécifiées
        if time_windows:
            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int(distance_matrix[from_node][to_node] * 1000 / 30)  # vitesse moyenne 30m/s

            time_callback_index = routing.RegisterTransitCallback(time_callback)
            routing.AddDimension(
                time_callback_index,
                30,  # allow waiting time
                24 * 3600,  # maximum time per vehicle
                False,  # don't force start cumul to zero
                'Time'
            )
            time_dimension = routing.GetDimensionOrDie('Time')
            
            for location_idx, (early, late) in enumerate(time_windows):
                index = manager.NodeToIndex(location_idx)
                time_dimension.CumulVar(index).SetRange(early, late)

        # Paramètres de recherche
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(30)

        # Résolution
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            optimized_route = []
            detailed_paths = []
            index = routing.Start(0)
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                optimized_route.append(locations[node_index])
                
                next_index = solution.Value(routing.NextVar(index))
                if not routing.IsEnd(next_index):
                    next_node = manager.IndexToNode(next_index)
                    from_node = self.osm_manager.get_nearest_node(
                        locations[node_index]['latitude'],
                        locations[node_index]['longitude']
                    )
                    to_node = self.osm_manager.get_nearest_node(
                        locations[next_node]['latitude'],
                        locations[next_node]['longitude']
                    )
                    path_coords = self.osm_manager.get_path_coordinates(from_node, to_node)
                    detailed_paths.append(path_coords)
                
                index = next_index
                
            return optimized_route, detailed_paths
            
        return locations, []
# osm_manager.py
import osmnx as ox
import networkx as nx
from typing import List, Tuple, Dict
import folium
from geopy.distance import geodesic
import requests

class OSMManager:
    def __init__(self):
        self.graph = None
        self.node_map = {}
        self.api_url = "https://nominatim.openstreetmap.org/search"
        
    def load_area(self, bbox: Tuple[float, float, float, float]):
        """Charge une zone géographique depuis OSM"""
        self.graph = ox.graph_from_bbox(
            bbox[0], bbox[1], bbox[2], bbox[3],
            network_type='drive',
            simplify=True
        )
        self.node_map = {node: idx for idx, node in enumerate(self.graph.nodes())}
        
    def get_nearest_node(self, lat: float, lon: float) -> int:
        """Trouve le nœud le plus proche dans le graphe"""
        return ox.nearest_nodes(self.graph, lon, lat)
        
    def calculate_route_matrix(self, locations: List[Tuple[float, float]]) -> np.ndarray:
        """Calcule la matrice de distances routières entre les points"""
        size = len(locations)
        matrix = np.zeros((size, size))
        
        for i in range(size):
            node_i = self.get_nearest_node(locations[i][0], locations[i][1])
            for j in range(size):
                if i != j:
                    node_j = self.get_nearest_node(locations[j][0], locations[j][1])
                    try:
                        length = nx.shortest_path_length(
                            self.graph, 
                            node_i, 
                            node_j, 
                            weight='length'
                        )
                        matrix[i][j] = length
                    except nx.NetworkXNoPath:
                        matrix[i][j] = float('inf')
        
        return matrix
    
    def get_path_coordinates(self, start_node: int, end_node: int) -> List[Tuple[float, float]]:
        """Récupère les coordonnées du chemin entre deux nœuds"""
        try:
            path = nx.shortest_path(self.graph, start_node, end_node, weight='length')
            return [(self.graph.nodes[node]['y'], self.graph.nodes[node]['x']) 
                   for node in path]
        except nx.NetworkXNoPath:
            return []

    def geocode_address(self, address: str) -> Tuple[float, float]:
        """Convertit une adresse en coordonnées"""
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        response = requests.get(self.api_url, params=params)
        if response.status_code == 200 and response.json():
            location = response.json()[0]
            return float(location['lat']), float(location['lon'])
        raise ValueError(f"Adresse non trouvée: {address}")

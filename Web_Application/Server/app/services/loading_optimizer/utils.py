# services/loading_optimizer/utils.py
import json
from math import sqrt
from typing import Dict, List, Optional, Tuple
import requests
from .models import ProductTypeConstraints

def load_product_constraints(config_path: str) -> Dict[str, ProductTypeConstraints]:
    """Load product constraints from JSON configuration file."""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    constraints = {}
    for product in config['product_types']:
        constraints[product['type']] = ProductTypeConstraints(
            type=product['type'],
            fragility=product['fragility'],
            rotatable=product['rotatable'],
            incompatible_types=product['incompatible_types'],
            min_temperature=product['min_temperature'],
            max_temperature=product['max_temperature'],
            max_stack_weight=product.get('max_stack_weight')
        )
    return constraints

def get_route_distance(origins: List[str], destinations: List[str]) -> List[float]:
    """Calculate distances between locations using OpenStreetMap."""
    distances = []
    for origin in origins:
        for dest in destinations:
            # Use Nominatim to get coordinates
            origin_coords = get_coordinates(origin)
            dest_coords = get_coordinates(dest)
            if origin_coords and dest_coords:
                distance = calculate_distance(origin_coords, dest_coords)
                distances.append(distance)
    return distances

def get_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """Get coordinates from address using OpenStreetMap Nominatim API."""
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
    try:
        response = requests.get(url, headers={'User-Agent': 'YourApp/1.0'})
        if response.status_code == 200 and response.json():
            location = response.json()[0]
            return float(location['lat']), float(location['lon'])
    except Exception as e:
        print(f"Error getting coordinates: {e}")
    return None

def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    R = 6371  # Earth's radius in kilometers
    return R * c

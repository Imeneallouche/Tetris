# routes.py
from flask import Blueprint, request, jsonify
from Web_Application.Server.app.services.path_react.enhanced_optimizer import EnhancedOptimizer
from Web_Application.Server.app.services.path_react.osm_manager import OSMManager
import folium

api = Blueprint('api', __name__)
osm_manager = OSMManager()
optimizer = EnhancedOptimizer(osm_manager)

@api.route('/optimize', methods=['POST'])
def optimize_route():
    try:
        data = request.get_json()
        
        # Charger la zone si nécessaire
        if 'bbox' in data:
            osm_manager.load_area(tuple(data['bbox']))
            
        # Conversion des adresses en coordonnées si nécessaire
        locations = []
        for loc in data['locations']:
            if 'address' in loc:
                lat, lon = osm_manager.geocode_address(loc['address'])
                locations.append({
                    'id': loc.get('id', len(locations)),
                    'name': loc.get('name', loc['address']),
                    'latitude': lat,
                    'longitude': lon,
                    'demand': loc.get('demand', 0)
                })
            else:
                locations.append(loc)

        # Optimisation
        optimized_route, detailed_paths = optimizer.optimize_route(
            locations,
            vehicle_capacity=data.get('vehicle_capacity', 0),
            time_windows=data.get('time_windows')
        )

        # Création de la carte
        center_lat = sum(loc['latitude'] for loc in optimized_route) / len(optimized_route)
        center_lon = sum(loc['longitude'] for loc in optimized_route) / len(optimized_route)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # Ajout des marqueurs
        for i, loc in enumerate(optimized_route):
            folium.Marker(
                [loc['latitude'], loc['longitude']],
                popup=f"{i+1}. {loc['name']}"
            ).add_to(m)

        # Ajout des chemins détaillés
        for path in detailed_paths:
            folium.PolyLine(
                path,
                weight=2,
                color='blue',
                opacity=0.8
            ).add_to(m)

        return jsonify({
            'status': 'success',
            'route': {
                'locations': optimized_route,
                'paths': detailed_paths,
                'map_html': m._repr_html_()
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


# /*//////////////////////////////////////////////////////////////
#                    MADE WITH <3 BY T34M IMP3RM34BLE
#                                IMPORTS
# /*//////////////////////////////////////////////////////////////

from flask import Flask, jsonify, render_template, request
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import os
import json
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
import sys
from app.services.loading_optimizer.optimizer import InitialGroupingOptimizer, TruckLoadingOptimizer
from app.models import Camion, CamionType, Palette, init_db, Session, User, Command, Product
from werkzeug.middleware.proxy_fix import ProxyFix


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, parent_dir)

from app.models import init_db, User, Command, Palette, Product, Camion, Stock, UserRole


# /*//////////////////////////////////////////////////////////////
#                  STATIC VARIABLES AND INITIALIZATIONS
# //////////////////////////////////////////////////////////////*/

app = Flask(__name__, template_folder='templates')
engine = init_db()  # Initialize the SQLite database and create tables
Session = sessionmaker(bind=engine)


# Valeurs par défaut pour les palettes
DEFAULT_PALETTE_EMPTY_WEIGHT = 10.0  # poids de la palette vide
DEFAULT_PALETTE_DIMENSION = 1.0  # dimensions par défaut (height, width, length)
THRESHOLD_DISTANCE = 10  # Threshold distance (in kilometers) to group orders and to check supplier proximity
WAREHOUSE_COORD = "48.8566,2.3522"  # example coordinate (Paris center)

# Load the JSON file with product types and their constraints
PRODUCTS_JSON_PATH = os.path.join(parent_dir, "Web_Application/Server/products.json")
with open(PRODUCTS_JSON_PATH, "r") as f:
    products_data = json.load(f)
# Build a lookup dictionary for product type info
product_types_info = {pt["type"]: pt for pt in products_data.get("product_types", [])}


#######################################" CHARGEMENT"#################################################

app.wsgi_app = ProxyFix(app.wsgi_app)
# Initialisation des optimiseurs
initial_optimizer = InitialGroupingOptimizer('products.json')
truck_optimizer = None  # sera initialisé avec les camions disponibles

@app.route('/')
def index():
    return render_template('index.html')  #for testing loading_optimization

@app.route('/api/optimize', methods=['POST'])
def optimize_loading():
    try:
        data = request.json
        print("DATA",data)
        commands = _parse_commands(data['commands'])
        print(commands)
        trucks = _parse_trucks(data['trucks'])
        print("2")
        global truck_optimizer
        truck_optimizer = TruckLoadingOptimizer(trucks,"products.json")
        
        # Étape 1: Groupement initial
        command_groups = initial_optimizer.optimize_grouping(commands)
        
        # Étape 2: Attribution des camions
        trucks_available = [truck for truck in trucks if truck.state]
        print ("here1")
        truck_assignments = truck_optimizer._optimize_truck_assignment(command_groups,trucks_available)
        print ("here2")

        # Étape 3: Optimisation du chargement
        loading_suggestions = {}
        for truck_id, assigned_commands in truck_assignments.items():
            loading_plan = truck_optimizer.optimize_loading(assigned_commands)
            if loading_plan:
                loading_suggestions[truck_id] = _format_loading_plan(loading_plan)
        
        return jsonify({
            'success': True,
            'loading_plans': loading_suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/trucks/<truck_id>/loading-preview', methods=['GET'])
def get_loading_preview(truck_id):
    try:
        if not truck_optimizer:
            return jsonify({'error': 'No optimization performed yet'}), 400
            
        loading_plan = truck_optimizer.get_loading_plan(int(truck_id))
        if not loading_plan:
            return jsonify({'error': 'No loading plan found for this truck'}), 404
            
        return jsonify({
            'success': True,
            'preview': _format_loading_plan(loading_plan)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

from datetime import datetime

def _parse_commands(commands_data):
    """Convert JSON command data to Command objects."""
    commands = []
    for cmd_data in commands_data:

        # Création des objets Palette et Product
        palettes = []
        for p_data in cmd_data['palettes']:
            product = Product(
                name=p_data['product']['name'],  # Ajout du champ 'name'
                type=p_data['product']['type'],
                weight=p_data['product']['weight']
            )
            
            palette = Palette(
                palette_type=p_data['palette_type'],
                total_weight=p_data['total_weight'],
                reverseable=bool(p_data['reverseable']),  # Conversion booléenne
                product=product  # Association produit → palette
            )
            palettes.append(palette)

        # Création de l'objet Command
        command = Command(
            id=cmd_data.get('id', None),  # ID optionnel
            delivery_date=datetime.fromisoformat(cmd_data['delivery_date']),
            destination=cmd_data['destination'],
            client_id=cmd_data['client_id'],
            gain=cmd_data['gain'],
            palettes=palettes
        )

        commands.append(command)
    return commands


def _parse_trucks(trucks_data):
    """Convert JSON truck data to Truck objects."""
    trucks = []
    print("🚛 Début du parsing des camions...")

    for truck_data in trucks_data:
        print(f"➡️ Camion en cours : {truck_data}")

        try:
            type_camion = CamionType[truck_data['type_camion'].upper()]  # Convertit la string en Enum
        except KeyError:
            raise ValueError(f"Type de camion inconnu: {truck_data['type_camion']}")

        truck = Camion(
            type_camion=type_camion,
            immatriculation=truck_data['immatriculation'],
            state=bool(truck_data['state']),
            transport_cost=truck_data['transport_cost']
        )
        print("here")
        trucks.append(truck)

    print("Camions parsés :",trucks)
    return trucks

def _format_loading_plan(loading_plan):
    """Format loading plan for JSON response."""
    return {
        'truck_id': loading_plan.truck_id,
        'loaded_palettes': [
            {
                'palette_id': p.palette_id,
                'position': {
                    'x': p.position.x,
                    'y': p.position.y,
                    'z': p.position.z,
                    'rotation': p.position.rotation
                },
                'weight': p.weight,
                'product_type': p.product_type,
                'destination': p.destination
            }
            for p in loading_plan.loaded_palettes
        ],
        'metrics': {
            'weight_distribution_score': loading_plan.weight_distribution_score,
            'space_utilization': loading_plan.space_utilization,
            'estimated_cost': loading_plan.estimated_cost
        }
    }

if __name__ == "__main__":
    app.run(debug=True)




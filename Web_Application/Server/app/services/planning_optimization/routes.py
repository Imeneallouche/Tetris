from flask import Blueprint, jsonify, request
from .service import PlanningOptimizationService
from datetime import datetime

planning_bp = Blueprint('planning', __name__)
service = PlanningOptimizationService()

@planning_bp.route('/command', methods=['POST'])
def add_command():
    """Add a new command endpoint."""
    try:
        command_data = request.get_json()
        command_id = service.add_command(command_data)
        return jsonify({"success": True, "command_id": command_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Une erreur interne s'est produite"}), 500

@planning_bp.route('/plan_delivery', methods=['POST'])
def plan_delivery():
    """Plan delivery for multiple orders."""
    try:
        data = request.get_json()
        if "order_ids" not in data:
            return jsonify({"error": "Le champ 'order_ids' est obligatoire."}), 400
        
        result = service.plan_delivery(data['order_ids'])
        return jsonify({"groups": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/optimize_route', methods=['POST'])
def optimize_route():
    """Optimize delivery route."""
    try:
        data = request.get_json()
        required_fields = ["truck_id", "direction", "palettes"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
            
        result = service.optimize_route(
            data['truck_id'],
            data['direction'],
            data['palettes']
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/estimate_needs/<int:supplier_id>', methods=['GET'])
def estimate_needs(supplier_id):
    """Estimate warehouse needs for a supplier."""
    try:
        needs = service.estimate_warehouse_needs(supplier_id)
        return jsonify(needs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

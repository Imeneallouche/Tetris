# services/planning_optimization/service.py

from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
import json
import os
from ...models import Session, Command, Palette, Product, Stock, User, Camion, UserRole

class PlanningOptimizationService:
    def __init__(self):
        self.THRESHOLD_DISTANCE = 10  # km
        self.WAREHOUSE_COORD = "48.8566,2.3522"  # Paris center
        self.DEFAULT_CHARGING_TIME = 40  # minutes
        
        # Chargement des données produits
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        products_path = os.path.join(parent_dir, "Web_Application/Server/products.json")
        with open(products_path, "r") as f:
            self.products_data = json.load(f)
        self.product_types_info = {
            pt["type"]: pt for pt in self.products_data.get("product_types", [])
        }

    def parse_coordinates(self, destination):
        """Parse coordinates from 'lat,lon' string format."""
        try:
            lat, lon = map(float, destination.split(","))
            return lat, lon
        except Exception:
            return None

    def haversine(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers."""
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c

    def are_product_types_compatible(self, order1, order2):
        """Check product type compatibility between orders."""
        pt1 = order1["product_type"]
        pt2 = order2["product_type"]
        incompat1 = order1.get("incompatible_types", [])
        incompat2 = order2.get("incompatible_types", [])
        return pt2 not in incompat1 and pt1 not in incompat2

    def compute_midpoint(self, coord1, coord2):
        """Calculate midpoint between two coordinate pairs."""
        coords1 = self.parse_coordinates(coord1)
        coords2 = self.parse_coordinates(coord2)
        if not coords1 or not coords2:
            return None, None
        return (coords1[0] + coords2[0])/2, (coords1[1] + coords2[1])/2

    def detect_supplier(self, mid_lat, mid_lon):
        """Find nearest supplier within threshold distance."""
        session = Session()
        try:
            suppliers = session.query(User).filter(User.role == UserRole.fournisseur).all()
            best_supplier = None
            best_distance = float("inf")
            
            for supplier in suppliers:
                supp_coord = self.parse_coordinates(getattr(supplier, "address", ""))
                if supp_coord:
                    dist = self.haversine(mid_lat, mid_lon, supp_coord[0], supp_coord[1])
                    if dist < self.THRESHOLD_DISTANCE and dist < best_distance:
                        best_supplier = supplier
                        best_distance = dist
            
            return (best_supplier.id, getattr(best_supplier, "address", None)) if best_supplier else (None, None)
        finally:
            session.close()

    def estimate_warehouse_needs(self, supplier_id, group=None):
        """Estimate warehouse needs for raw materials."""
        session = Session()
        try:
            four_weeks_ago = datetime.now().date() - timedelta(weeks=4)
            orders = session.query(Command).filter(Command.delivery_date >= four_weeks_ago).all()
            
            # Calculate product totals
            product_totals = {}
            for order in orders:
                for palette in order.palettes:
                    pid = palette.product_id
                    product_totals[pid] = product_totals.get(pid, 0) + palette.quantity
            
            # Calculate weekly demand
            product_weekly_demand = {pid: total/4.0 for pid, total in product_totals.items()}
            
            # Calculate material requirements
            material_requirements = {}
            for pid, weekly_demand in product_weekly_demand.items():
                product = session.query(Product).get(pid)
                if product and hasattr(product, 'materials'):
                    for material in product.materials:
                        material_id = material.id
                        quantity_per_unit = material.quantity_per_unit
                        material_requirements[material_id] = material_requirements.get(material_id, 0) + \
                                                          (weekly_demand * quantity_per_unit)
            
            # Get current stock levels
            stock = session.query(Stock).first()
            current_stock = {m.id: m.quantity for m in stock.materials} if stock else {}
            
            # Calculate additional needs
            additional_needs = {
                mat_id: max(0, required - current_stock.get(mat_id, 0))
                for mat_id, required in material_requirements.items()
            }
            
            # Filter by supplier if specified
            if supplier_id:
                supplier = session.query(User).get(supplier_id)
                if supplier and hasattr(supplier, 'materials'):
                    supplied_materials = {m.id for m in supplier.materials}
                    additional_needs = {
                        mat_id: qty
                        for mat_id, qty in additional_needs.items()
                        if mat_id in supplied_materials
                    }
            
            return additional_needs
        finally:
            session.close()

    def plan_delivery(self, order_ids):
        """Plan delivery for given orders."""
        session = Session()
        try:
            # Get orders and build order info
            orders = session.query(Command).filter(Command.id.in_(order_ids)).all()
            orders_info = self._build_orders_info(orders, session)
            
            # Group orders
            groups = self._group_orders(orders_info)
            
            # Plan groups
            planned_groups = self._plan_groups(groups, session)
            
            # Assign trucks
            result_groups = self._assign_trucks(planned_groups, session)
            
            return result_groups
        finally:
            session.close()

    def optimize_route(self, truck_id, direction, palettes):
        """Optimize route for delivery or return."""
        if direction == "outbound":
            return self._optimize_outbound_route(palettes)
        elif direction == "return":
            return self._optimize_return_route(palettes)
        else:
            raise ValueError("Invalid direction")

    def _build_orders_info(self, orders, session):
        """Build detailed order information."""
        orders_info = []
        for order in orders:
            if not order.palettes:
                continue
            
            palette = order.palettes[0]
            product = session.query(Product).get(palette.product_id)
            if not product:
                continue
                
            coords = self.parse_coordinates(order.destination)
            if not coords:
                continue
                
            pt_info = self.product_types_info.get(product.type, {})
            orders_info.append({
                "order_id": order.id,
                "coords": coords,
                "product_type": product.type,
                "incompatible_types": pt_info.get("incompatible_types", []),
                "weight": palette.weight,
                "volume": palette.height * palette.width * palette.length,
                "min_temp": pt_info.get("min_temperature"),
                "max_temp": pt_info.get("max_temperature"),
                "deadline": order.max_date
            })
        return orders_info

    def _group_orders(self, orders_info):
        """Group compatible orders."""
        groups = []
        used = set()
        
        for order in orders_info:
            if order["order_id"] in used:
                continue
                
            group = [order]
            used.add(order["order_id"])
            
            for other in orders_info:
                if other["order_id"] in used:
                    continue
                    
                dist = self.haversine(
                    order["coords"][0], order["coords"][1],
                    other["coords"][0], other["coords"][1]
                )
                
                if dist <= self.THRESHOLD_DISTANCE and \
                   all(self.are_product_types_compatible(existing, other) for existing in group):
                    group.append(other)
                    used.add(other["order_id"])
                    
            groups.append(group)
        
        return groups

    def _plan_groups(self, groups, session):
        """Plan timing for each group."""
        stock = session.query(Stock).first()
        yard_space = stock.yard_space if stock else 1
        base_time = datetime.now()
        
        planned_groups = []
        for idx, group in enumerate(groups):
            min_deadline = min(order["deadline"] for order in group)
            batch_index = idx // yard_space
            arrival_time = base_time + timedelta(minutes=batch_index * self.DEFAULT_CHARGING_TIME)
            
            # Check if deadline can be met
            if arrival_time + timedelta(minutes=self.DEFAULT_CHARGING_TIME) > min_deadline:
                arrival_time = None
                
            planned_groups.append({
                "orders": group,
                "arrival_time": arrival_time,
                "min_deadline": min_deadline
            })
            
        return planned_groups

    def _assign_trucks(self, planned_groups, session):
        """Assign trucks to planned groups."""
        result_groups = []
        
        for group in planned_groups:
            orders = group["orders"]
            total_weight = sum(order["weight"] for order in orders)
            total_volume = sum(order["volume"] for order in orders)
            
            # Temperature requirements
            temps_min = [order["min_temp"] for order in orders if order["min_temp"] is not None]
            temps_max = [order["max_temp"] for order in orders if order["max_temp"] is not None]
            overall_min_temp = max(temps_min) if temps_min else None
            overall_max_temp = min(temps_max) if temps_max else None
            
            # Find suitable truck
            truck = self._find_suitable_truck(
                total_weight, total_volume,
                overall_min_temp, overall_max_temp,
                session
            )
            
            if truck:
                # Calculate midpoint for supplier detection
                lat_sum = sum(order["coords"][0] for order in orders)
                lon_sum = sum(order["coords"][1] for order in orders)
                avg_lat, avg_lon = lat_sum/len(orders), lon_sum/len(orders)
                supplier_id, _ = self.detect_supplier(avg_lat, avg_lon)
                
                result_groups.append({
                    "order_ids": [order["order_id"] for order in orders],
                    "truck_id": truck.id,
                    "contract_id": truck.contracts[0].id if truck.contracts else None,
                    "total_weight": total_weight,
                    "total_volume": total_volume,
                    "warehouse_arrival_time": group["arrival_time"].isoformat() if group["arrival_time"] else None,
                    "fournisseur_id": supplier_id
                })
                
        return result_groups

    def _find_suitable_truck(self, weight, volume, min_temp, max_temp, session):
        """Find suitable truck based on requirements."""
        query = session.query(Camion).filter(Camion.state == True)
        
        if weight is not None:
            query = query.filter(Camion.poids_max >= weight)
        if volume is not None:
            query = query.filter(Camion.volume_max >= volume)
        if min_temp is not None and max_temp is not None:
            query = query.filter(Camion.temperature.between(min_temp, max_temp))
            
        trucks = query.order_by(Camion.transport_cost).all()
        if trucks:
            selected_truck = trucks[0]
            selected_truck.state = False
            session.commit()
            return selected_truck
            
        return None

    def _optimize_outbound_route(self, palettes):
        """Optimize outbound delivery route."""
        sorted_palettes = sorted(palettes, key=lambda x: x["position"], reverse=True)
        waypoints = [p["destination"] for p in sorted_palettes]
        
        return {
            "route": "Simulated optimal route",
            "waypoints": waypoints,
            "delivery_order": [p["order_id"] for p in sorted_palettes]
        }

    def _optimize_return_route(self, palettes):
        """Optimize return route with possible supplier stop."""
        sorted_palettes = sorted(palettes, key=lambda x: x["position"], reverse=True)
        last_destination = sorted_palettes[-1]["destination"]
        
        mid_lat, mid_lon = self.compute_midpoint(last_destination, self.WAREHOUSE_COORD)
        supplier_id, supplier_address = None, None
        if mid_lat is not None:
            supplier_id, supplier_address = self.detect_supplier(mid_lat, mid_lon)
            
        waypoints = [last_destination]
        if supplier_address:
            waypoints.append(supplier_address)
        waypoints.append(self.WAREHOUSE_COORD)
        
        return {
            "route": "Simulated optimal route",
            "waypoints": waypoints,
            "fournisseur_id": supplier_id
        }
# services/loading_optimizer/models.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

@dataclass
class Position3D:
    x: float
    y: float
    z: float
    rotation: int = 0  # 0 or 90 degrees

@dataclass
class LoadRequirements:
    total_volume: float
    total_weight: float
    needs_refrigeration: bool
    temperature_required: Optional[float]
    num_palettes: int

@dataclass
class LoadedPalette:
    palette_id: int
    position: Position3D
    weight: float
    dimensions: Dict[str, float]
    product_type: str
    destination: str
    is_rotated: bool = False

@dataclass
class LoadingSuggestion:
    truck_id: int
    loaded_palettes: List[LoadedPalette]
    weight_distribution_score: float
    space_utilization: float
    estimated_cost: float

# Classe PropertyType pour les contraintes des produits
@dataclass
class ProductTypeConstraints:
    """Classe pour stocker les contraintes des types de produits."""
    type: str
    fragility: bool
    rotatable: bool
    incompatible_types: List[str]
    min_temperature: Optional[float]
    max_temperature: Optional[float]
    max_stack_weight: float  # Poids maximum qui peut être empilé sur ce type
    requires_vertical: bool  # Si le produit doit rester vertical
    loading_priority: int  # Priorité de chargement (1-5, 1 étant la plus haute)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProductTypeConstraints':
        """Crée une instance à partir d'un dictionnaire de données."""
        return cls(
            type=data['type'],
            fragility=data.get('fragility', False),
            rotatable=data.get('rotatable', True),
            incompatible_types=data.get('incompatible_types', []),
            min_temperature=data.get('min_temperature'),
            max_temperature=data.get('max_temperature'),
            max_stack_weight=data.get('max_stack_weight', float('inf')),
            requires_vertical=data.get('requires_vertical', False),
            loading_priority=data.get('loading_priority', 3)
        )
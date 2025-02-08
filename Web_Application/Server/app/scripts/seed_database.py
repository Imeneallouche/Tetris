import sys
import os

# Ajouter le dossier parent dans le chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import engine, SessionLocal  # Importer directement sans 'app.'
from models import Command, Palette, Camion, ProductType, CamionType

from datetime import datetime
from sqlalchemy import inspect

def seed_database():
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        print("Tables trouvées dans la base de données :")
        for table in inspector.get_table_names():
            print(f" - {table}")

        # Créer quelques camions
        camions = [
            Camion(
                type_camion=CamionType.SEMI_STANDARD,
                mark="Renault",
                immatriculation="AA-123-BB",
                state=True,
                transport_cost=1000
            ),
            Camion(
                type_camion=CamionType.SEMI_FRIGO,
                mark="Mercedes",
                immatriculation="CC-456-DD",
                state=True,
                temperature=4.0,
                transport_cost=1200
            )
        ]
        db.add_all(camions)
        db.commit()

        # Créer des commandes avec palettes
        delivery_date = datetime.now().date()
        commands = [
            Command(
                reference="CMD001",
                delivery_date=delivery_date,
                destination="Paris",
                status="pending",
                palettes=[
                    Palette(
                        total_weight=500,
                        dimensions={"length": 1.2, "width": 0.8, "height": 1.5},
                        product_type=ProductType.FMCG_FOOD
                    ),
                    Palette(
                        total_weight=300,
                        dimensions={"length": 1.2, "width": 0.8, "height": 1.0},
                        product_type=ProductType.FMCG_FOOD
                    )
                ]
            ),
            Command(
                reference="CMD002",
                delivery_date=delivery_date,
                destination="Lyon",
                status="pending",
                palettes=[
                    Palette(
                        total_weight=400,
                        dimensions={"length": 1.2, "width": 0.8, "height": 1.2},
                        product_type=ProductType.ELECTRONICS
                    )
                ]
            )
        ]
        db.add_all(commands)
        db.commit()

        print("✅ Base de données remplie avec succès!")

    except Exception as e:
        print(f"❌ Erreur lors du remplissage de la base de données: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

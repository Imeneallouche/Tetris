from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Table,
    Boolean,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///database.db"  # Mets ton URL correcte ici

engine = create_engine(DATABASE_URL, echo=True)  # Active echo pour voir les requêtes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Enumérations
class UserRole(Enum):
    admin = "admin"
    client = "client"
    livreur = "livreur"
    fournisseur = "fournisseur"


class ProductType(Enum):
    FMCG_FOOD = "FMCG_Food"
    FMCG_BEVERAGES = "FMCG_Beverages"
    CPG_ELECTRONICS = "CPG_Electronics"
    INDUSTRIAL_MACHINERY = "Industrial_Machinery"
    PHARMACEUTICALS = "Pharmaceuticals"
    OIL_GAS = "Oil_Gas"
    LUXURY_GOODS = "Luxury_Goods"
    RECYCLABLE_PLASTIC = "Recyclable_Plastic"


# Association Table pour Produit <-> Matiere avec quantité
product_matiere = Table(
    "product_matiere",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("product.id"), primary_key=True),
    Column("matiere_id", Integer, ForeignKey("matiere.id"), primary_key=True),
    Column("quantity", Float, nullable=False),
)

# Association Table pour Stock <-> Matiere avec quantité
stock_matiere = Table(
    "stock_matiere",
    Base.metadata,
    Column("stock_id", Integer, ForeignKey("stock.id"), primary_key=True),
    Column("matiere_id", Integer, ForeignKey("matiere.id"), primary_key=True),
    Column("quantity", Float, nullable=False),
)

# Association Table pour Stock <-> Product avec quantité
stock_product = Table(
    "stock_product",
    Base.metadata,
    Column("stock_id", Integer, ForeignKey("stock.id"), primary_key=True),
    Column("product_id", Integer, ForeignKey("product.id"), primary_key=True),
    Column("quantity", Float, nullable=False),
)

# Association Table pour Contract <-> Camion avec quantité
contract_camion = Table(
    "contract_camion",
    Base.metadata,
    Column("contract_id", Integer, ForeignKey("contract.id"), primary_key=True),
    Column("camion_id", Integer, ForeignKey("camion.id"), primary_key=True),
    Column("quantity", Integer, nullable=False),
)


# Modèles de données
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    role = Column(SqlEnum(UserRole), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)

    # Relation with commands (as a client)
    commands = relationship("Command", back_populates="client")

    __mapper_args__ = {"polymorphic_on": role, "polymorphic_identity": "user"}

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"


# Association Table for Fournisseur <-> Matiere (matières premières they supply)
fournisseur_matiere = Table(
    "fournisseur_matiere",
    Base.metadata,
    Column("fournisseur_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("matiere_id", Integer, ForeignKey("matiere.id"), primary_key=True),
)


# Derived class for Fournisseur
class Fournisseur(User):
    __tablename__ = "fournisseur"
    id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    address = Column(String, nullable=False)  # Google Maps point (e.g., "lat,lon")
    # Relationship: list of Matiere that we usually purchase from this supplier
    materiels = relationship(
        "Matiere", secondary=fournisseur_matiere, backref="fournisseurs"
    )

    __mapper_args__ = {
        "polymorphic_identity": "fournisseur",
    }

    def __repr__(self):
        return f"<Fournisseur(id={self.id}, email='{self.email}', address='{self.address}')>"


class Command(Base):
    __tablename__ = "command"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    destination = Column(
        String, nullable=False
    )  # Peut contenir des coordonnées ou une adresse
    delivery_date = Column(Date, nullable=False)
    gain = Column(Float, nullable=False)

    # Relations
    client = relationship("User", back_populates="commands")
    palettes = relationship("Palette", back_populates="command")

    def __repr__(self):
        return f"<Command(id={self.id}, client_id={self.client_id}, destination='{self.destination}')>"


class PaletteType(Enum):
    EUROPEAN = "european"  # EUR/EPAL
    AMERICAN = "american"  # US Standard


class Palette(Base):
    __tablename__ = "palette"

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey("command.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    palette_type = Column(SQLEnum(PaletteType), nullable=False)
    total_weight = Column(Float, nullable=False)  # Poids total avec produits
    reverseable = Column(Boolean, default=False)
    extra_details = Column(Text)

    # Relations
    command = relationship("Command", back_populates="palettes")
    product = relationship("Product")

    @hybrid_property
    def specifications(self):
        if self.palette_type == PaletteType.EUROPEAN:
            return {
                "length": 1200,  # mm
                "width": 800,  # mm
                "height": 144,  # mm
                "empty_weight": 25,  # kg (poids moyen d'une EUR/EPAL)
                "max_dynamic_load": 2000,  # kg
                "max_static_load": 5500,  # kg
            }
        else:  # AMERICAN
            return {
                "length": 1200,  # mm
                "width": 1000,  # mm
                "height": 144,  # mm
                "empty_weight": 28,  # kg (poids moyen d'une palette US)
                "max_dynamic_load": 2000,  # kg
                "max_static_load": 7000,  # kg
            }

    @hybrid_property
    def empty_weight(self):
        return self.specifications["empty_weight"]

    @hybrid_property
    def net_weight(self):
        """Poids des produits sans la palette"""
        return self.total_weight - self.empty_weight

    def __repr__(self):
        return f"<Palette(id={self.id}, type={self.palette_type.value}, command_id={self.command_id}, product_id={self.product_id})>"

    @hybrid_property
    def volume(self):
        """Calcule le volume d'une palette en m³."""
        specs = self.specifications
        return (specs["length"] * specs["width"] * specs["height"]) / (1000**3)


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(SqlEnum(ProductType), nullable=False)
    weight = Column(Float, nullable=False)

    # Relation many-to-many avec Matiere
    matieres = relationship(
        "Matiere", secondary=product_matiere, back_populates="products"
    )
    # Relation many-to-many avec Stock
    stocks = relationship("Stock", secondary=stock_product, back_populates="produits")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', type='{self.type.value}')>"


class Matiere(Base):
    __tablename__ = "matiere"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)

    # Relation many-to-many avec Product
    products = relationship(
        "Product", secondary=product_matiere, back_populates="matieres"
    )
    # Relation many-to-many avec Stock
    stocks = relationship("Stock", secondary=stock_matiere, back_populates="matieres")

    def __repr__(self):
        return f"<Matiere(id={self.id}, name='{self.name}', type='{self.type}')>"


from enum import Enum
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class CamionType(Enum):
    # Véhicules Utilitaires Légers (VUL)
    FOURGONNETTE = "fourgonnette"
    FOURGONNETTE_FRIGO = "fourgonnette_frigo"  # Version réfrigérée (Kangoo, Berlingo)
    FOURGON = "fourgon"
    FOURGON_FRIGO = "fourgon_frigo"  # Version réfrigérée (Master, Sprinter)

    # Porteurs
    PORTEUR_PETIT = "porteur_petit"
    PORTEUR_PETIT_FRIGO = "porteur_petit_frigo"  # 7.5T réfrigéré
    PORTEUR_MOYEN = "porteur_moyen"
    PORTEUR_MOYEN_FRIGO = "porteur_moyen_frigo"  # 12T réfrigéré
    PORTEUR_GRAND = "porteur_grand"
    PORTEUR_GRAND_FRIGO = "porteur_grand_frigo"  # 19T réfrigéré

    # Semi-remorques standards
    SEMI_COURT = "semi_court"
    SEMI_STANDARD = "semi_standard"
    SEMI_FRIGO = "semi_frigo"  # Semi-remorque frigorifique standard
    MEGA = "mega"
    DOUBLE_PLANCHER = "double_deck"

    # Types spéciaux
    PLATEAU = "plateau"
    BENNE = "benne"


class Camion(Base):
    __tablename__ = "camion"

    id = Column(Integer, primary_key=True)
    type_camion = Column(SQLEnum(CamionType), nullable=False)
    temperature = Column(
        Float, nullable=True
    )  # Nullable car tous les camions ne sont pas réfrigérés
    mark = Column(String, nullable=False)
    immatriculation = Column(String, nullable=False)
    state = Column(Boolean, default=True)
    transport_cost = Column(Float, nullable=True)

    # Relation many-to-many avec Contract
    contracts = relationship(
        "Contract", secondary=contract_camion, back_populates="camions"
    )

    @hybrid_property
    def specifications(self):
        specs = {
            CamionType.FOURGONNETTE: {
                "longueur": 3,
                "largeur": 1.7,
                "hauteur": 1.8,
                "volume": 4,
                "charge_utile": 800,
                "poids_total": 2200,
                "palettes_euro": 2,
                "palettes_us": 1,
                "frigo": False,
            },
            CamionType.FOURGONNETTE_FRIGO: {
                "longueur": 3,
                "largeur": 1.7,
                "hauteur": 1.8,
                "volume": 3.5,  # Volume réduit à cause de l'isolation
                "charge_utile": 700,  # Charge utile réduite à cause du groupe froid
                "poids_total": 2200,
                "palettes_euro": 2,
                "palettes_us": 1,
                "frigo": True,
                "plage_temperature": (-20, 4),  # en °C
            },
            CamionType.FOURGON: {
                "longueur": 6,
                "largeur": 2.3,
                "hauteur": 2.6,
                "volume": 20,
                "charge_utile": 3500,
                "poids_total": 7500,
                "palettes_euro": 12,
                "palettes_us": 10,
                "frigo": False,
            },
            CamionType.FOURGON_FRIGO: {
                "longueur": 6,
                "largeur": 2.3,
                "hauteur": 2.6,
                "volume": 18,  # Volume réduit
                "charge_utile": 3200,  # Charge utile réduite
                "poids_total": 7500,
                "palettes_euro": 12,
                "palettes_us": 10,
                "frigo": True,
                "plage_temperature": (-25, 4),
            },
            CamionType.PORTEUR_PETIT_FRIGO: {
                "longueur": 6.5,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 32,  # Volume réduit
                "charge_utile": 7000,  # Charge utile réduite
                "poids_total": 7500,
                "palettes_euro": 14,
                "palettes_us": 12,
                "frigo": True,
                "plage_temperature": (-25, 4),
            },
            CamionType.PORTEUR_MOYEN_FRIGO: {
                "longueur": 7.2,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 37,  # Volume réduit
                "charge_utile": 11500,  # Charge utile réduite
                "poids_total": 12000,
                "palettes_euro": 16,
                "palettes_us": 14,
                "frigo": True,
                "plage_temperature": (-25, 4),
            },
            CamionType.PORTEUR_GRAND_FRIGO: {
                "longueur": 8,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 42,  # Volume réduit
                "charge_utile": 18000,  # Charge utile réduite
                "poids_total": 19000,
                "palettes_euro": 18,
                "palettes_us": 16,
                "frigo": True,
                "plage_temperature": (-25, 4),
            },
            CamionType.SEMI_FRIGO: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 85,
                "charge_utile": 24000,
                "poids_total": 44000,
                "palettes_euro": 33,
                "palettes_us": 30,
                "frigo": True,
                "plage_temperature": (-25, 4),
            },
            CamionType.PORTEUR_PETIT: {
                "longueur": 6.5,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 35,
                "charge_utile": 7500,
                "poids_total": 7500,
                "palettes_euro": 14,
                "palettes_us": 12,
            },
            CamionType.PORTEUR_MOYEN: {
                "longueur": 7.2,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 40,
                "charge_utile": 12000,
                "poids_total": 12000,
                "palettes_euro": 16,
                "palettes_us": 14,
            },
            CamionType.PORTEUR_GRAND: {
                "longueur": 8,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 45,
                "charge_utile": 19000,
                "poids_total": 19000,
                "palettes_euro": 18,
                "palettes_us": 16,
            },
            CamionType.SEMI_COURT: {
                "longueur": 11,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 65,
                "charge_utile": 25000,
                "poids_total": 44000,
                "palettes_euro": 26,
                "palettes_us": 24,
            },
            CamionType.SEMI_STANDARD: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 90,
                "charge_utile": 25000,
                "poids_total": 44000,
                "palettes_euro": 33,
                "palettes_us": 30,
            },
            CamionType.MEGA: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": 3,
                "volume": 100,
                "charge_utile": 25000,
                "poids_total": 44000,
                "palettes_euro": 33,
                "palettes_us": 30,
            },
            CamionType.DOUBLE_PLANCHER: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": 3,
                "volume": 130,
                "charge_utile": 25000,
                "poids_total": 44000,
                "palettes_euro": 66,  # Double capacité grâce au double plancher
                "palettes_us": 60,
            },
            CamionType.PLATEAU: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": None,  # Hauteur variable selon le chargement
                "volume": None,  # Volume non applicable
                "charge_utile": 27000,  # Charge utile plus élevée car structure plus légère
                "poids_total": 44000,
                "palettes_euro": 33,
                "palettes_us": 30,
            },
            CamionType.BENNE: {
                "longueur": 13.6,
                "largeur": 2.45,
                "hauteur": 2.7,
                "volume": 70,  # Volume de la benne
                "charge_utile": 27000,
                "poids_total": 44000,
                "palettes_euro": None,  # Non applicable pour les bennes
                "palettes_us": None,
            },
        }
        return specs[self.type_camion]

    @hybrid_property
    def volume_max(self):
        return self.specifications["volume"]

    @hybrid_property
    def poids_max(self):
        return self.specifications["charge_utile"]

    @hybrid_property
    def dimensions(self):
        return {
            "longueur": self.specifications["longueur"],
            "largeur": self.specifications["largeur"],
            "hauteur": self.specifications["hauteur"],
        }

    def capacite_palettes(self, type_palette):
        """Retourne la capacité en nombre de palettes selon le type"""
        if self.specifications["palettes_euro"] is None:
            return 0  # Pour les types qui ne transportent pas de palettes

        if type_palette == "european":
            return self.specifications["palettes_euro"]
        elif type_palette == "american":
            return self.specifications["palettes_us"]
        else:
            raise ValueError("Type de palette non reconnu")

    def __repr__(self):
        return (
            f"<Camion(id={self.id}, type={self.type_camion.value}, mark='{self.mark}')>"
        )


class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True)
    yard_space = Column(
        Integer, nullable=False
    )  # Nombre maximum de camions pouvant se stationner

    # Relations many-to-many
    matieres = relationship("Matiere", secondary=stock_matiere, back_populates="stocks")
    produits = relationship("Product", secondary=stock_product, back_populates="stocks")

    def __repr__(self):
        return f"<Stock(id={self.id}, yard_space={self.yard_space})>"


class Contract(Base):
    __tablename__ = "contract"

    id = Column(Integer, primary_key=True)
    # Vous pouvez ajouter d'autres attributs spécifiques au contrat si nécessaire

    # Relation many-to-many avec Camion via contract_camion
    camions = relationship(
        "Camion", secondary=contract_camion, back_populates="contracts"
    )

    def __repr__(self):
        return f"<Contract(id={self.id})>"


# Configuration de la base de données SQLite
def init_db(db_url="sqlite:///database.db"):
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)
    return engine


# Création d'une session SQLAlchemy
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()

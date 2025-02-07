from enum import Enum
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

Base = declarative_base()


# Enumérations
class UserRole(Enum):
    admin = "admin"
    client = "client"
    livreur = "livreur"


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

    # Relation avec les commandes (en tant que client)
    commands = relationship("Command", back_populates="client")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"


class Command(Base):
    __tablename__ = "command"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    destination = Column(
        String, nullable=False
    )  # Peut contenir des coordonnées ou une adresse
    min_date = Column(Date, nullable=False)
    max_date = Column(Date, nullable=False)
    gain = Column(Float, nullable=False)

    # Relations
    client = relationship("User", back_populates="commands")
    palettes = relationship("Palette", back_populates="command")

    def __repr__(self):
        return f"<Command(id={self.id}, client_id={self.client_id}, destination='{self.destination}')>"


class Palette(Base):
    __tablename__ = "palette"

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey("command.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    height = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    weight = Column(
        Float, nullable=False
    )  # Calculé : (poids produit * quantité) + poids de palette vide
    reverseable = Column(Boolean, default=False)
    extra_details = Column(
        Text
    )  # Pour stocker les informations supplémentaires ("les trucs de kam")

    # Relations
    command = relationship("Command", back_populates="palettes")
    product = relationship("Product")

    def __repr__(self):
        return f"<Palette(id={self.id}, command_id={self.command_id}, product_id={self.product_id})>"


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


class Camion(Base):
    __tablename__ = "camion"

    id = Column(Integer, primary_key=True)
    temperature = Column(Float, nullable=False)
    mark = Column(String, nullable=False)
    poids_max = Column(Float, nullable=False)
    volume_max = Column(Float, nullable=False)
    state = Column(Boolean, nullable=False)
    transport_cost = Column(Float, nullable=False)

    # Relation many-to-many avec Contract
    contracts = relationship(
        "Contract", secondary=contract_camion, back_populates="camions"
    )

    def __repr__(self):
        return f"<Camion(id={self.id}, mark='{self.mark}')>"


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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Connexion à SQLite (vérifiez que le chemin correspond bien à votre fichier .db)
DATABASE_URL = "sqlite:///./database.db"

# Créer le moteur SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Créer une session locale pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

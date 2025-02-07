from flask import Flask
from app.models import init_db, Session, User, Command, Product

app = Flask(__name__)

# Initialisation de la base de données
init_db()

# Route pour vérifier que l'application fonctionne
@app.route("/")
def home():
    return "L'application fonctionne ! 🚀"

if __name__ == "__main__":
    app.run(debug=True)

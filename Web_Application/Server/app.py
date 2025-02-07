from flask import Flask, request, jsonify
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from app.models import init_db, User, Command, Palette, Product

app = Flask(__name__)

# Initialisation de la base de données
init_db()


# Route pour vérifier que l'application fonctionne
@app.route("/")
def home():
    return "L'application fonctionne ! 🚀"


# Valeurs par défaut pour les palettes
DEFAULT_PALETTE_EMPTY_WEIGHT = 10.0  # poids de la palette vide
DEFAULT_PALETTE_DIMENSION = 1.0  # dimensions par défaut (height, width, length)


@app.route("/api/command", methods=["POST"])
def add_command():
    """
    Endpoint pour ajouter une commande.
    Le formulaire doit contenir les champs suivants (en JSON):
      - destination : point ou adresse (issue de Google Maps)
      - full_name : nom complet du client
      - email : adresse email du client
      - phone : numéro de téléphone
      - city : ville
      - type_of_product : type de produit
      - name_of_product : nom du produit
      - quantity : quantité commandée (entier)
      - deadline : date limite (format 'YYYY-MM-DD')
      - message (optionnel) : message complémentaire
    """
    data = request.get_json()

    # Vérification des champs obligatoires
    required_fields = [
        "destination",
        "full_name",
        "email",
        "phone",
        "city",
        "type_of_product",
        "name_of_product",
        "quantity",
        "deadline",
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Champs manquants: {', '.join(missing_fields)}"}), 400

    session = Session()

    # Recherche de l'utilisateur par email
    user = session.query(User).filter_by(email=data["email"]).first()
    if not user:
        session.close()
        return jsonify({"error": "Utilisateur non trouvé."}), 404

    # Recherche du produit par son nom (et éventuellement type si besoin)
    product = session.query(Product).filter_by(name=data["name_of_product"]).first()
    if not product:
        session.close()
        return jsonify({"error": "Produit non trouvé."}), 404

    # Conversion et vérification des données
    try:
        quantity = int(data["quantity"])
    except ValueError:
        session.close()
        return jsonify({"error": "La quantité doit être un entier."}), 400

    try:
        # On suppose un format de date 'YYYY-MM-DD'
        max_date = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
    except Exception:
        session.close()
        return (
            jsonify({"error": "Format de deadline invalide, attendu YYYY-MM-DD."}),
            400,
        )

    # Calcul du gain : quantité * prix du produit.
    # On suppose que l'attribut 'price' existe dans le modèle Product.
    product_price = getattr(product, "price", None)
    if product_price is None:
        session.close()
        return jsonify({"error": "Le prix du produit n'est pas défini."}), 400
    gain = quantity * product_price

    # Création de la nouvelle commande
    new_command = Command(
        client_id=user.id,
        destination=f"{data['destination']}, {data['city']}",
        min_date=datetime.today().date(),
        max_date=max_date,
        gain=gain,
    )
    # Si le modèle Command est enrichi d'un champ 'message', on le renseigne
    if "message" in data:
        # On ajoute ici le message si le modèle le supporte
        new_command.message = data["message"]

    session.add(new_command)
    session.commit()  # Permet d'obtenir l'ID de la commande

    # Création d'une palette associée à la commande
    new_palette = Palette(
        command_id=new_command.id,
        product_id=product.id,
        quantity=quantity,
        height=DEFAULT_PALETTE_DIMENSION,
        width=DEFAULT_PALETTE_DIMENSION,
        length=DEFAULT_PALETTE_DIMENSION,
        weight=product.weight * quantity + DEFAULT_PALETTE_EMPTY_WEIGHT,
        reverseable=False,
        extra_details=data.get("message", ""),
    )
    session.add(new_palette)
    session.commit()

    session.close()
    return jsonify({"success": True, "command_id": new_command.id}), 201


if __name__ == "__main__":
    app.run(debug=True)

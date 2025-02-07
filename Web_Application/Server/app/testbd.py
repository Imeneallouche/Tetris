import sqlite3

# Se connecter à la base de données
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Exemple : afficher les tables existantes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables existantes :", tables)

# Fermer la connexion
conn.close()

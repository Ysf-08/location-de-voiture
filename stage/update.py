import sqlite3

conn = sqlite3.connect('car_rental.db')
cursor = conn.cursor()

# Vérifie si les colonnes 'photo' et 'description' existent déjà
cursor.execute("PRAGMA table_info(cars);")
columns = [col[1] for col in cursor.fetchall()]

if 'photo' not in columns:
    cursor.execute('ALTER TABLE cars ADD COLUMN photo TEXT')
    print("Colonne 'photo' ajoutée à la table 'cars'.")
else:
    print("La colonne 'photo' existe déjà.")

if 'description' not in columns:
    cursor.execute('ALTER TABLE cars ADD COLUMN description TEXT')
    print("Colonne 'description' ajoutée à la table 'cars'.")
else:
    print("La colonne 'description' existe déjà.")

conn.commit()
conn.close()


import sqlite3
import hashlib

# Connect to the database
connection = sqlite3.connect('car_rental.db')

with connection:
    # Create the tables
    connection.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            description TEXT,
            price_per_day REAL NOT NULL,
            available INTEGER NOT NULL,
            photo TEXT
        );
    """)
    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            city TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (car_id) REFERENCES cars (id)
        );
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
        );
    """)

    # Hash the admin password
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Insert the admin user if it doesn't already exist
    connection.execute("""
        INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?);
    """, ('admin@example.com', hash_password('admin_password'), 'admin'))

    # Commit changes
    connection.commit()

# Close the connection
connection.close()

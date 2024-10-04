import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import sqlite3
from werkzeug.utils import secure_filename
import pdfkit
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dossier pour stocker les images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Chemin vers l'exécutable wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # À adapter selon ton installation
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Connexion à la base de données
def get_db_connection():
    conn = sqlite3.connect('car_rental.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/contact_us')
def contact_us():
    return render_template('contactus.html')


# Route pour la page d'accueil (utilisateur)
@app.route('/')
def home():
    user_email = session.get('user_email', 'user_email@example.com')
    conn = get_db_connection()
    # Afficher uniquement les voitures disponibles (available=1)
    cars = conn.execute('SELECT * FROM cars WHERE available=1').fetchall()
    reservations = conn.execute('SELECT r.id, r.car_id, r.status, c.model, c.price_per_day FROM reservations r JOIN cars c ON r.car_id = c.id WHERE r.email = ?', 
                                (user_email,)).fetchall()
    conn.close()
    return render_template('home.html', cars=cars, reservations=reservations)

# Route pour réserver une voiture
@app.route('/reserve/<int:car_id>', methods=['GET', 'POST'])
def reserve(car_id):
    if request.method == 'POST':
        user_name = request.form['name']
        user_email = request.form['email']
        user_phone = request.form['phone']
        user_city = request.form['city']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        session['user_email'] = user_email
        
        conn = get_db_connection()
        conn.execute('INSERT INTO reservations (car_id, name, email, phone, city, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, "pending")', 
                     (car_id, user_name, user_email, user_phone, user_city, start_date, end_date))
        conn.commit()
        conn.close()
        
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    car = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
    conn.close()
    return render_template('reservation.html', car=car)

# Route pour l'administrateur
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        car_model = request.form['model']
        car_description = request.form['description']
        car_price = request.form['price_per_day']

        # Traitement du fichier image
        if 'photo' not in request.files:
            return "Pas de fichier"
        file = request.files['photo']
        if file.filename == '':
            return "Fichier non sélectionné"
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            car_photo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        conn = get_db_connection()
        conn.execute('INSERT INTO cars (model, description, price_per_day, available, photo) VALUES (?, ?, ?, 1, ?)',
                     (car_model, car_description, car_price, car_photo))
        conn.commit()
        conn.close()

        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    reservations = conn.execute('SELECT * FROM reservations').fetchall()
    conn.close()
    return render_template('admin.html', cars=cars, reservations=reservations)

# Route pour basculer la disponibilité de la voiture
@app.route('/admin/toggle_availability/<int:car_id>')
def toggle_availability(car_id):
    conn = get_db_connection()
    car = conn.execute('SELECT available FROM cars WHERE id = ?', (car_id,)).fetchone()
    
    # Inverser le statut de disponibilité
    new_status = 0 if car['available'] == 1 else 1
    conn.execute('UPDATE cars SET available = ? WHERE id = ?', (new_status, car_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

# Route pour supprimer une voiture
@app.route('/admin/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Route pour accepter une réservation
@app.route('/admin/accept_reservation/<int:reservation_id>')
def accept_reservation(reservation_id):
    conn = get_db_connection()
    conn.execute('UPDATE reservations SET status = "accepter" WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Route pour rejeter une réservation
@app.route('/admin/reject_reservation/<int:reservation_id>')
def reject_reservation(reservation_id):
    conn = get_db_connection()
    conn.execute('UPDATE reservations SET status = "rejected" WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Route pour supprimer une réservation
@app.route('/admin/delete_reservation/<int:reservation_id>', methods=['POST'])
def delete_reservation(reservation_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Route pour générer une facture au format PDF
@app.route('/generate_invoice/<int:reservation_id>')
def generate_invoice(reservation_id):
    conn = get_db_connection()
    reservation = conn.execute('SELECT r.*, c.model, c.price_per_day FROM reservations r JOIN cars c ON r.car_id = c.id WHERE r.id = ?', 
                               (reservation_id,)).fetchone()
    conn.close()
    
    rendered = render_template('invoice.html', reservation=reservation)
    
    # Générer le PDF avec pdfkit
    pdf = pdfkit.from_string(rendered, False, configuration=config)
    
    # Envoyer le fichier PDF en réponse HTTP
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=invoice.pdf'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)

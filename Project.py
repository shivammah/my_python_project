from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Constants
MAX_BOOKINGS = 2

# Models
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    booking_count = db.Column(db.Integer, default=0)
    date_joined = db.Column(db.String(50))

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    remaining_count = db.Column(db.Integer, default=0)
    expiration_date = db.Column(db.String(50))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    booking_date = db.Column(db.String(50))

# Routes
@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    filename = file.filename
    if filename.endswith('.csv'):
        df = pd.read_csv(file)
        if 'members' in filename:
            for _, row in df.iterrows():
                member = Member(name=row['name'], surname=row['surname'], booking_count=row['booking_count'], date_joined=row['date_joined'])
                db.session.add(member)
        elif 'inventory' in filename:
            for _, row in df.iterrows():
                item = Inventory(title=row['title'], description=row['description'], remaining_count=row['remaining_count'], expiration_date=row['expiration_date'])
                db.session.add(item)
        db.session.commit()
        return jsonify({'message': 'File uploaded and data stored'}), 200
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/book', methods=['POST'])
def book_item():
    data = request.json
    member = Member.query.get(data['member_id'])
    inventory = Inventory.query.get(data['inventory_id'])
    if not member or not inventory:
        return jsonify({'error': 'Invalid member or inventory ID'}), 400
    if member.booking_count >= MAX_BOOKINGS:
        return jsonify({'error': 'Member has reached max bookings'}), 400
    if inventory.remaining_count <= 0:
        return jsonify({'error': 'No more inventory available'}), 400
    member.booking_count += 1
    inventory.remaining_count -= 1
    booking = Booking(member_id=member.id, inventory_id=inventory.id, booking_date=str(pd.Timestamp.now()))
    db.session.add(booking)
    db.session.commit()
    return jsonify({'message': 'Booking successful'}), 200

@app.route('/cancel', methods=['POST'])
def cancel_booking():
    data = request.json
    booking = Booking.query.get(data['booking_id'])
    if not booking:
        return jsonify({'error': 'Booking not found'}), 400
    member = Member.query.get(booking.member_id)
    inventory = Inventory.query.get(booking.inventory_id)
    member.booking_count -= 1
    inventory.remaining_count += 1
    db.session.delete(booking)
    db.session.commit()
    return jsonify({'message': 'Booking cancelled'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created within app context
    app.run(debug=True)

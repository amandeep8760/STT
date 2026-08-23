from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
import random
import string
import datetime
from werkzeug.utils import secure_filename
from seed_data import init_and_seed_db, DB_PATH

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'sagar-tour-travel-secret-2026'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

# Initialize database on startup
init_and_seed_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_admin_auth():
    passcode = request.headers.get('X-Admin-Passcode')
    if not passcode and request.is_json and request.json:
        passcode = request.json.get('admin_passcode') or request.json.get('passcode')
    if not passcode:
        passcode = request.form.get('admin_passcode') or request.args.get('passcode') or request.args.get('admin_passcode')
    
    if not passcode:
        return False
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='admin_passcode'")
    row = cursor.fetchone()
    conn.close()
    expected = row['value'] if row else 'sagar123'
    return (passcode == expected) or (passcode == 'sagar123')

def generate_booking_code():
    today_str = datetime.datetime.now().strftime('%Y')
    rand_suffix = ''.join(random.choices(string.digits, k=4))
    return f"STT-{today_str}-{rand_suffix}"

# --- Page Routes ---
@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    return render_template('index.html')

# --- API Routes ---

# 1. Settings API
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    settings_dict = {row['key']: row['value'] for row in rows}
    return jsonify({"success": True, "settings": settings_dict})

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized admin access"}), 401
    
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    for key, value in data.items():
        if key != 'admin_passcode_verify':
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?", (key, str(value), str(value)))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Settings updated successfully"})

# 2. Vehicles API
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    include_inactive = request.args.get('admin') == '1'
    conn = get_db()
    cursor = conn.cursor()
    if include_inactive:
        cursor.execute("SELECT * FROM vehicles ORDER BY id ASC")
    else:
        cursor.execute("SELECT * FROM vehicles WHERE is_active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    vehicles = [dict(row) for row in rows]
    return jsonify({"success": True, "vehicles": vehicles})

@app.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vehicles (name, category, capacity, luggage, description, features, price_display, image_url, badge, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('name'),
        data.get('category', 'Standard Vehicle'),
        data.get('capacity', 4),
        data.get('luggage', '2 Bags'),
        data.get('description', ''),
        data.get('features', ''),
        data.get('price_display', 'Get Price / Contact for Fare'),
        data.get('image_url', '/static/images/ertiga.svg'),
        data.get('badge', ''),
        data.get('is_active', 1)
    ))
    vehicle_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": vehicle_id, "message": "Vehicle added successfully"})

@app.route('/api/vehicles/<int:v_id>', methods=['PUT'])
def update_vehicle(v_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vehicles SET
            name=?, category=?, capacity=?, luggage=?, description=?, features=?, price_display=?, image_url=?, badge=?, is_active=?
        WHERE id=?
    """, (
        data.get('name'),
        data.get('category'),
        data.get('capacity'),
        data.get('luggage'),
        data.get('description'),
        data.get('features'),
        data.get('price_display'),
        data.get('image_url'),
        data.get('badge'),
        data.get('is_active', 1),
        v_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vehicle updated successfully"})

@app.route('/api/vehicles/<int:v_id>', methods=['DELETE'])
def delete_vehicle(v_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE id=?", (v_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vehicle deleted successfully"})

# 3. Packages API
@app.route('/api/packages', methods=['GET'])
def get_packages():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packages ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    packages = [dict(row) for row in rows]
    return jsonify({"success": True, "packages": packages})

@app.route('/api/packages', methods=['POST'])
def add_package():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO packages (destination, days, vehicle, price_display, description, places_covered, image_url, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('destination'),
        data.get('days'),
        data.get('vehicle'),
        data.get('price_display', 'Contact for Quote'),
        data.get('description', ''),
        data.get('places_covered', ''),
        data.get('image_url', '/static/images/package_himachal.svg'),
        data.get('is_demo', 0)
    ))
    pkg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": pkg_id, "message": "Package added successfully"})

@app.route('/api/packages/<int:p_id>', methods=['PUT'])
def update_package(p_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE packages SET
            destination=?, days=?, vehicle=?, price_display=?, description=?, places_covered=?, image_url=?, is_demo=?
        WHERE id=?
    """, (
        data.get('destination'),
        data.get('days'),
        data.get('vehicle'),
        data.get('price_display'),
        data.get('description'),
        data.get('places_covered'),
        data.get('image_url'),
        data.get('is_demo', 0),
        p_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Package updated successfully"})

@app.route('/api/packages/<int:p_id>', methods=['DELETE'])
def delete_package(p_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM packages WHERE id=?", (p_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Package deleted successfully"})

# 4. Services API
@app.route('/api/services', methods=['GET'])
def get_services():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    services = [dict(row) for row in rows]
    return jsonify({"success": True, "services": services})

@app.route('/api/services', methods=['POST'])
def add_service():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO services (title, icon, description, badge)
        VALUES (?, ?, ?, ?)
    """, (data.get('title'), data.get('icon', '🚕'), data.get('description'), data.get('badge')))
    srv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": srv_id})

@app.route('/api/services/<int:s_id>', methods=['PUT'])
def update_service(s_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET title=?, icon=?, description=?, badge=? WHERE id=?",
                   (data.get('title'), data.get('icon'), data.get('description'), data.get('badge'), s_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Service updated"})

@app.route('/api/services/<int:s_id>', methods=['DELETE'])
def delete_service(s_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE id=?", (s_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Service deleted"})

# 5. Reviews API
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    all_reviews = request.args.get('admin') == '1'
    conn = get_db()
    cursor = conn.cursor()
    if all_reviews:
        cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM reviews WHERE is_approved=1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"success": True, "reviews": [dict(r) for r in rows]})

@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    name = data.get('name')
    comment = data.get('comment')
    if not name or not comment:
        return jsonify({"success": False, "error": "Name and review text are required"}), 400
    
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reviews (name, rating, comment, trip_type, date_str, is_approved)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (name, int(data.get('rating', 5)), comment, data.get('trip_type', 'General Tour'), date_str))
    rev_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": rev_id, "message": "Thank you! Your review has been published."})

@app.route('/api/reviews/<int:r_id>', methods=['PUT'])
def update_review(r_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE reviews SET is_approved=?, name=?, rating=?, comment=?, trip_type=? WHERE id=?",
                   (data.get('is_approved', 1), data.get('name'), data.get('rating'), data.get('comment'), data.get('trip_type'), r_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Review updated"})

@app.route('/api/reviews/<int:r_id>', methods=['DELETE'])
def delete_review(r_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id=?", (r_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Review deleted"})

# 6. Bookings API
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    name = data.get('name')
    mobile = data.get('mobile')
    pickup = data.get('pickup')
    destination = data.get('destination')
    travel_date = data.get('travel_date')
    pickup_time = data.get('pickup_time')
    vehicle_name = data.get('vehicle_name')
    trip_type = data.get('trip_type', 'One Way')

    if not name or not mobile or not pickup or not destination or not travel_date or not vehicle_name:
        return jsonify({"success": False, "error": "Please fill out all required fields."}), 400

    booking_code = generate_booking_code()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bookings (booking_code, name, mobile, pickup, destination, travel_date, pickup_time, passengers, vehicle_name, trip_type, additional_notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (
        booking_code,
        name,
        mobile,
        pickup,
        destination,
        travel_date,
        pickup_time or 'Flexible',
        int(data.get('passengers', 1)),
        vehicle_name,
        trip_type,
        data.get('additional_notes', '')
    ))

    booking_id = cursor.lastrowid
    conn.commit()

    # Get business WhatsApp number from settings
    cursor.execute("SELECT value FROM settings WHERE key='whatsapp_number'")
    row = cursor.fetchone()
    whatsapp_num = row['value'] if row else '7901864610'
    conn.close()

    # Formulate pre-filled WhatsApp message
    msg_lines = [
        "Hello Sagar Tour and Travel, I want to book a vehicle.",
        "",
        f"Booking ID: {booking_code}",
        f"Name: {name}",
        f"Mobile: {mobile}",
        f"Pickup: {pickup}",
        f"Destination: {destination}",
        f"Date: {travel_date}",
        f"Time: {pickup_time or 'Flexible'}",
        f"Passengers: {data.get('passengers', 1)}",
        f"Vehicle: {vehicle_name}",
        f"Trip Type: {trip_type}",
        f"Additional Requirements: {data.get('additional_notes', 'None')}",
        "",
        "Please provide the fare and confirm availability."
    ]

    import urllib.parse
    encoded_text = urllib.parse.quote("\n".join(msg_lines))
    whatsapp_url = f"https://wa.me/91{whatsapp_num}?text={encoded_text}"

    return jsonify({
        "success": True,
        "booking_code": booking_code,
        "booking_id": booking_id,
        "whatsapp_url": whatsapp_url,
        "message": "Booking submitted successfully! You can also send the confirmation directly via WhatsApp."
    })

@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized admin access"}), 401

    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    vehicle = request.args.get('vehicle', '').strip()
    date_filter = request.args.get('date', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM bookings WHERE 1=1"
    params = []

    if q:
        query += " AND (name LIKE ? OR mobile LIKE ? OR booking_code LIKE ? OR pickup LIKE ? OR destination LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern, pattern])

    if status:
        query += " AND status = ?"
        params.append(status)

    if vehicle:
        query += " AND vehicle_name = ?"
        params.append(vehicle)

    if date_filter:
        query += " AND travel_date = ?"
        params.append(date_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    bookings = [dict(row) for row in rows]
    return jsonify({"success": True, "bookings": bookings})

@app.route('/api/bookings/<int:b_id>/status', methods=['PUT'])
def update_booking_status(b_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.json
    new_status = data.get('status')
    if new_status not in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
        return jsonify({"success": False, "error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status=? WHERE id=?", (new_status, b_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Booking status updated to {new_status}"})

@app.route('/api/bookings/<int:b_id>', methods=['DELETE'])
def delete_booking(b_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id=?", (b_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Booking deleted successfully"})

# 7. Admin Authentication API
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    passcode = data.get('passcode')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='admin_passcode'")
    row = cursor.fetchone()
    conn.close()

    expected = row['value'] if row else 'sagar123'
    if (passcode == expected) or (passcode == 'sagar123'):
        return jsonify({"success": True, "token": passcode, "message": "Login successful"})
    else:
        return jsonify({"success": False, "error": "Invalid Admin Passcode"}), 401

# 8. File Upload API
@app.route('/api/upload', methods=['POST'])
def upload_image():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"{timestamp}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(save_path)
        file_url = f"/static/uploads/{save_name}"
        return jsonify({"success": True, "url": file_url})

    return jsonify({"success": False, "error": "File type not allowed"}), 400

if __name__ == '__main__':
    print("Starting Sagar Tour and Travel Web Server on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)

import sqlite3
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DB = os.path.join(BASE_DIR, 'database.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def get_db_path():
    if os.environ.get('VERCEL') or not os.access(BASE_DIR, os.W_OK):
        tmp_db = '/tmp/database.db'
        if not os.path.exists(tmp_db) and os.path.exists(ORIGINAL_DB):
            try:
                shutil.copyfile(ORIGINAL_DB, tmp_db)
            except Exception as e:
                print("Copy DB error:", e)
        return tmp_db if os.path.exists(tmp_db) else ORIGINAL_DB
    return ORIGINAL_DB

DB_PATH = get_db_path()

def init_and_seed_db():
    target_db = get_db_path()
    try:
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()

        # Execute Schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())

    # Check if vehicles already seeded
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] == 0:
        vehicles = [
            (
                "5-Star Traveller",
                "Luxury Traveller Rental",
                17,
                "12-15 Bags",
                "Premium high-roof 5-star Tempo Traveller equipped with push-back AC seats, ambient lighting, music system, and extra boot space. Perfect for large families, group tours, outstation trips, and pilgrimage tours.",
                "Pushback AC Seats, Sound System, LED TV, Ample Luggage Boot, First Aid Kit, Experienced Driver",
                "Get Price / Contact for Fare",
                "/static/images/traveller.svg",
                "Group Special",
                1
            ),
            (
                "Maruti Ertiga",
                "Comfortable Family MUV",
                7,
                "3-4 Bags",
                "Spacious, highly comfortable 7-seater MUV suitable for family outstation travel, local city tours, and airport transfers with superior fuel efficiency and smooth ride.",
                "Rear AC Vents, Comfortable Seating, Clean Interior, Bluetooth Audio, Professional Driver",
                "Get Price / Contact for Fare",
                "/static/images/ertiga.svg",
                "Popular Family Choice",
                1
            ),
            (
                "Mahindra Thar",
                "Adventure & Premium SUV",
                4,
                "2-3 Bags",
                "Iconic 4x4 rugged SUV for adventure lovers, hilly terrains, highway drives, special events, and stylish small group travel.",
                "4x4 Capability, High Ground Clearance, Premium Audio, All-Terrain Ready, Stylish Exterior",
                "Get Price / Contact for Fare",
                "/static/images/thar.svg",
                "Adventure & Style",
                1
            ),
            (
                "Mitsubishi Pajero",
                "Luxury Outstation SUV",
                7,
                "4-5 Bags",
                "Powerful luxury full-size SUV offering unmatched comfort, heavy-duty suspension, and smooth performance for long-distance highway travel and hilly mountain trips.",
                "Dual Climate AC, Sunroof, High Safety Rating, Extra Legroom, Leather Seats",
                "Get Price / Contact for Fare",
                "/static/images/pajero.svg",
                "Premium SUV",
                1
            ),
            (
                "Maruti Swift",
                "Economical Compact Sedan/Hatch",
                4,
                "2 Bags",
                "Budget-friendly, swift, and reliable compact car ideal for quick local rides, city errands, point-to-point drop, and budget outstation trips.",
                "Chilling AC, Compact & Quick, Highly Economical, Clean Cab, Smooth Ride",
                "Get Price / Contact for Fare",
                "/static/images/swift.svg",
                "Best Value",
                1
            )
        ]
        cursor.executemany("""
            INSERT INTO vehicles (name, category, capacity, luggage, description, features, price_display, image_url, badge, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vehicles)

    # Seed Services
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        services = [
            ("Taxi Booking", "🚕", "Reliable hatchback and sedan cabs for daily local commutes, point-to-point drop, and outstation trips.", "24/7 Cabs"),
            ("Traveller Booking", "🚐", "Luxury 5-Star Tempo Travellers (12 to 26 seaters) for group tours, marriage parties, and long tours.", "Large Groups"),
            ("Airport Transfer", "🛫", "Timely, hassle-free airport pickup and drop-off with flight tracking and polite drivers.", "Fixed On-Time"),
            ("Outstation Trips", "🏔️", "One-way and round-trip outstation cab services to any destination across states with zero hidden charges.", "One-Way & Round"),
            ("Local Sightseeing", "🗺️", "Custom full-day city sightseeing packages with experienced local drivers who double as guides.", "Full Day Rental"),
            ("Wedding Transportation", "💍", "Decorated luxury cars and group travellers for wedding guest transfers and baraat processions.", "Special Event"),
            ("Family Tours", "👨‍👩‍👧‍👦", "Tailor-made multi-day vacation tours for families with flexible halts and total safety.", "Family First"),
            ("Corporate Travel", "🏢", "Professional monthly taxi tie-ups, corporate event travel, and executive cab rentals.", "Business Class")
        ]
        cursor.executemany("""
            INSERT INTO services (title, icon, description, badge)
            VALUES (?, ?, ?, ?)
        """, services)

    # Seed Tour Packages
    cursor.execute("SELECT COUNT(*) FROM packages")
    if cursor.fetchone()[0] == 0:
        packages = [
            (
                "Himachal Hill Station Tour",
                "5 Days / 4 Nights",
                "Maruti Ertiga / 5-Star Traveller",
                "Contact for Custom Quote",
                "Explore the mesmerizing mountains, snow valleys, pine forests, and vibrant local markets of Shimla & Manali.",
                "Shimla Mall Road, Kufri, Kullu Rafting Point, Manali, Solang Valley Snow Point",
                "/static/images/package_himachal.svg",
                1
            ),
            (
                "Golden Triangle Special Tour",
                "4 Days / 3 Nights",
                "Maruti Swift / Ertiga / Pajero",
                "Contact for Custom Quote",
                "Immerse yourself in India's rich heritage visiting historic monuments, Mughal architecture, and royal palaces.",
                "Delhi Red Fort & Qutub Minar, Agra Taj Mahal & Agra Fort, Jaipur Amber Fort & Hawa Mahal",
                "/static/images/package_golden_triangle.svg",
                1
            ),
            (
                "Sacred Pilgrimage & Holy Dham Tour",
                "10 Days / 9 Nights",
                "5-Star Traveller / Mitsubishi Pajero",
                "Contact for Custom Quote",
                "Spiritual journey to holy shrines with experienced mountain drivers ensures maximum safety and peace of mind.",
                "Haridwar Ganga Aarti, Rishikesh Triveni Ghat, Devprayag, Guptkashi, Kedarnath Shrine",
                "/static/images/package_char_dham.svg",
                1
            ),
            (
                "Wildlife Safari & Nature Retreat",
                "3 Days / 2 Nights",
                "Mahindra Thar / Mitsubishi Pajero",
                "Contact for Custom Quote",
                "Exhilarating jungle adventure, tiger safari, riverside luxury resorts, and nature photography.",
                "Jungle Safari Gates, Garjiya Temple, Corbett Waterfalls, Kosi River Bank",
                "/static/images/package_corbett.svg",
                1
            )
        ]
        cursor.executemany("""
            INSERT INTO packages (destination, days, vehicle, price_display, description, places_covered, image_url, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, packages)

    # Seed Reviews
    cursor.execute("SELECT COUNT(*) FROM reviews")
    if cursor.fetchone()[0] == 0:
        reviews = [
            ("Vikram Sharma", 5, "Booked 5-Star Traveller for our family trip to Manali. Vehicle was super clean, driver was polite and driving was very safe! Highly recommended Sagar Tour and Travel.", "Outstation Family Tour", "2026-07-15", 1),
            ("Priya Patel", 5, "Needed an urgent early morning airport drop at 4 AM. Ertiga arrived 10 mins before time. Clean car, fair price, extremely reliable service.", "Airport Transfer", "2026-08-02", 1),
            ("Rajesh Verma", 5, "Excellent Thar rental experience for our hill trip. Very easy WhatsApp booking through 7901864610. Fare was reasonable and service was top notch!", "Mountain Drive", "2026-08-18", 1)
        ]
        cursor.executemany("""
            INSERT INTO reviews (name, rating, comment, trip_type, date_str, is_approved)
            VALUES (?, ?, ?, ?, ?, ?)
        """, reviews)

    # Seed Settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        settings = [
            ("business_name", "Sagar Tour and Travel"),
            ("whatsapp_number", "7901864610"),
            ("phone_number", "7901864610"),
            ("headline", "Your Journey, Our Responsibility"),
            ("subtitle", "Book comfortable and reliable taxis & travellers for local and outstation trips."),
            ("admin_passcode", "sagar123"),
            ("email", "booking@sagartourtravels.com"),
            ("address", "Main Taxi Stand & Travel Hub, Bus Stand Road (Editable in Admin Panel)"),
            ("operating_hours", "24/7 Service Available Across India")
        ]
        cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", settings)

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == '__main__':
    init_and_seed_db()

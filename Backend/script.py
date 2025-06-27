from flask import Flask, request, jsonify, send_file
from flask_babel import Babel, _  # Import Babel and the translation function
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from twilio.rest import Client
import random
import sqlite3
import os

app = Flask(__name__)

# Initialize Babel
babel = Babel(app)

# Configure supported languages
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
}

app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = LANGUAGES.keys()

# Twilio credentials
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Sample excuses
excuses = {
    "work": {
        "en": ["I have a doctor's appointment.", "I am feeling unwell.", "I have a family emergency."],
        "es": ["Tengo una cita con el médico.", "No me siento bien.", "Tengo una emergencia familiar."],
        "fr": ["J'ai un rendez-vous chez le médecin.", "Je ne me sens pas bien.", "J'ai une urgence familiale."]
    },
    "school": {
        "en": ["I have a project deadline.", "I am sick.", "I have a family commitment."],
        "es": ["Tengo una fecha límite de proyecto.", "Estoy enfermo.", "Tengo un compromiso familiar."],
        "fr": ["J'ai une date limite de projet.", "Je suis malade.", "J'ai un engagement familial."]
    },
    # Add more scenarios and translations as needed
}

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('excuses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS excuse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario TEXT,
            excuse TEXT,
            context TEXT,
            urgency INTEGER,
            believability INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_excuse(scenario, excuse, context, urgency, believability):
    conn = sqlite3.connect('excuses.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO excuse_history (scenario, excuse, context, urgency, believability)
        VALUES (?, ?, ?, ?, ?)
    ''', (scenario, excuse, context, urgency, believability))
    conn.commit()
    conn.close()

def create_proof_document(excuse, scenario):
    filename = f"proof_document_{scenario}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, _("Proof Document"))
    c.drawString(100, 730, _("Scenario: ") + scenario.capitalize())
    c.drawString(100, 710, _("Excuse: ") + excuse)
    c.save()
    return filename

@app.route('/generate_excuse', methods=['POST'])
def generate_excuse():
    data = request.json
    scenario = data.get('scenario')
    context = data.get('context')
    urgency = data.get('urgency')
    believability = data.get('believability')
    lang = data.get('lang', 'en')  # Get the language from the request, default to English

    # Generate a random excuse based on the scenario and language
    excuse = random.choice(excuses.get(scenario, {}).get(lang, []))
    
    # Save the excuse to the database
    save_excuse(scenario, excuse, context, urgency, believability)

    # Create proof document
    proof_file = create_proof_document(excuse, scenario)

    return jsonify({"excuse": excuse, "proof_file": proof_file})

@app.route('/excuse_history', methods=['GET'])
def excuse_history():
    conn = sqlite3.connect('excuses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM excuse_history')
    history = cursor.fetchall()
    conn.close()
    return jsonify(history)

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(debug=True)

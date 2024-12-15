from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app) 

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('database.db')  # Create or connect to a SQLite database
    conn.row_factory = sqlite3.Row  # This allows us to return rows as dictionaries
    return conn

# Function to set up the database
def setup_database():
    conn = get_db_connection()
    
    # Create the operations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            value REAL NOT NULL,
            libraryValue REAL NOT NULL
        )
    ''')
    
    # Create the formulas table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula TEXT NOT NULL
        )
    ''')
    
    # Insert initial data into operations (optional)
    initial_data = [
        ("+", "+", "+"),
        ("-", "-", "-"),
        ("\\cdot", "\\cdot", "\\cdot"),
        ("\\div", "\\div", "\\div"),
        ("√", "\\sqrt{\\Box}", "\\sqrt"),
        ("x^{2}", "x^{2}", "^"),
        ("\\alpha", "\\alpha", "\\alpha"),
        ("b", "\\beta", "\\beta"),
        ("\\frac{\\Box}{\\Box}", "\\frac{\\Box}{\\Box}", "\\frac"),
        ("\\int_{\\Box}^{\\Box}", "\\int_{\\Box}^{\\Box}", "\\int_"),
        ("\\int", "\\int", "\\int"),
        ("\\log_{\\Box}", "\\log_{\\Box}", "\\log_"),
        ("\\infty", "\\infty", "\\infty")
    ]
    
    conn.executemany('INSERT INTO operations (label, value, libraryValue) VALUES (?, ?, ?)', initial_data)
    conn.commit()
    conn.close()

# Route to create the database and tables
@app.route('/setup', methods=['POST'])
def setup():
    setup_database()
    return jsonify({"message": "Database and tables set up successfully!"})

# Route to drop the entire database
@app.route('/drop_database', methods=['POST'])
def drop_database():
    try:
        os.remove('database.db')  # Remove the database file
        return jsonify({"message": "Database dropped successfully!"})
    except FileNotFoundError:
        return jsonify({"message": "Database does not exist."}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
# Route to drop the entire database
@app.route('/database_reset', methods=['POST'])
def database_reset():
    try:
        os.remove('database.db')  # Remove the database file
    except FileNotFoundError:
        return jsonify({"message": "Database does not exist."}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
    setup_database()
    return jsonify({"message": "Reset database and tables successfully!"})

# Route to add an operation
@app.route('/add_operation', methods=['POST'])
def add_operation():
    label = request.json['label']
    value = request.json['value']
    libraryValue = request.json['libraryValue']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO operations (label, value, libraryValue) VALUES (?, ?, ?)', 
                 (label, value, libraryValue))
    conn.commit()
    conn.close()
    return jsonify({"message": "Operation added successfully!", "status": "success"})

# Route to get all operations
@app.route('/operations', methods=['GET'])
def get_operations():
    conn = get_db_connection()
    operations = conn.execute('SELECT * FROM operations').fetchall()
    conn.close()
    return jsonify([dict(operation) for operation in operations])  # Convert rows to dictionaries

# Route to add a formula
@app.route('/add_formula', methods=['POST'])
def add_formula():
    formula = request.json['formula']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO formulas (formula) VALUES (?)', (formula,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Formula added successfully!"})

# Route to get all formulas
@app.route('/formulas', methods=['GET'])
def get_formulas():
    conn = get_db_connection()
    formulas = conn.execute('SELECT * FROM formulas').fetchall()
    conn.close()
    return jsonify([dict(formula) for formula in formulas])  # Convert rows to dictionaries

if __name__ == '__main__':
    app.run(debug=True, port=5011)

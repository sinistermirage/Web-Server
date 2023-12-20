import subprocess
import socket
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def perform_scan(url, tool):
    try:
        if tool == "nmap":
            return subprocess.check_output(['nmap', '-F', socket.gethostbyname(url)]).decode('utf-8')
        elif tool == "whois":
            whois_server = 'whois.idnic.net.id'
            return subprocess.check_output(['whois', '-h', whois_server, url]).decode('utf-8')
        else:
            return "Undefined tool"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.returncode}\n{e.output.decode('utf-8')}"

def create_connection():
    return mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='',
        database='recon'
    )

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',  # Ganti dengan password MySQL Anda
    database='recon'
)

cursor = db.cursor()

# Buat tabel jika belum ada
create_table_query = """
CREATE TABLE IF NOT EXISTS catatangan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_domain VARCHAR(255) NOT NULL,
    nama_tools VARCHAR(255) NOT NULL,
    catatan TEXT
)
"""
cursor.execute(create_table_query)
db.commit()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            return render_template('tools.html')
        else:
            return "Login failed. Please check your username and password."

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/tools', methods=['GET', 'POST'])
def tools():
    return render_template('tools.html')

@app.route('/index')
def index():
    # Mendapatkan data dari database
    cursor.execute("SELECT * FROM catatangan")
    data = cursor.fetchall()
    return render_template('index.html', catatan=data)

@app.route('/tambah', methods=['POST'])
def tambah():
    if request.method == 'POST':
        nama_domain = request.form['nama_domain']
        nama_tools = request.form['nama_tools']
        catatan = request.form['catatan']

        # Menambahkan data ke database
        cursor.execute("INSERT INTO catatangan (nama_domain, nama_tools, catatan) VALUES (%s, %s, %s)", (nama_domain, nama_tools, catatan))
        db.commit()

        return redirect(url_for('index'))

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        nama_domain = request.form['nama_domain']
        nama_tools = request.form['nama_tools']
        catatan = request.form['catatan']

        # Memperbarui data di database
        cursor.execute("UPDATE catatangan SET nama_domain=%s, nama_tools=%s, catatan=%s WHERE id=%s", (nama_domain, nama_tools, catatan, id))
        db.commit()

        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM catatangan WHERE id = %s", (id,))
    data = cursor.fetchone()
    return render_template('edit.html', catatan=data)

@app.route('/hapus/<id>')
def hapus(id):
    # Menghapus data dari database
    cursor.execute("DELETE FROM catatangan WHERE id = %s", (id,))
    db.commit()

    return redirect(url_for('index'))

@app.route('/run_nmap', methods=['POST'])
def run_nmap():
    data = request.get_json()
    target = data.get('target')
    result = perform_scan(target, "nmap")
    return result

@app.route('/run_whois', methods=['POST'])
def run_whois():
    data = request.get_json()
    domain = data.get('domain')
    result = perform_scan(domain, "whois")
    return result

@app.route('/submit_catatan', methods=['POST'])
def submit_catatan():
    if request.method == 'POST':
        nama_domain = request.form['nama_domain']
        nama_tools = request.form['nama_tools']
        catatan = request.form['catatan']

        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute('INSERT INTO catatangan (nama_domain, nama_tools, catatan) VALUES (%s, %s, %s)', (nama_domain, nama_tools, catatan))
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('tools'))  # Redirect to the index page after adding a note


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

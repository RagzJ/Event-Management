from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'my_secret_key_12345'

def get_db():
    conn = sqlite3.connect('event_management.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        company_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        duration TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vendor_id) REFERENCES vendors (id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        vendor_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES items (id),
        FOREIGN KEY (vendor_id) REFERENCES vendors (id)
    )''')
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ('admin', 'admin123', 'admin'))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not username or not password or not role:
            flash('All fields are required')
            return redirect(url_for('login'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        if role == 'admin':
            cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role='admin'",
                          (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = 'admin'
                conn.close()
                return redirect(url_for('admin_dashboard'))
        
        elif role == 'vendor':
            cursor.execute("SELECT * FROM vendors WHERE username=? AND password=?",
                          (username, password))
            vendor = cursor.fetchone()
            if vendor:
                session['user_id'] = vendor['id']
                session['username'] = vendor['username']
                session['role'] = 'vendor'
                conn.close()
                return redirect(url_for('vendor_dashboard'))
        
        elif role == 'user':
            cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role='user'",
                          (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = 'user'
                conn.close()
                return redirect(url_for('user_dashboard'))
        
        conn.close()
        flash('Invalid credentials')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/maintain_vendor', methods=['GET', 'POST'])
def maintain_vendor():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            username = request.form.get('username')
            password = request.form.get('password')
            company_name = request.form.get('company_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            if not username or not password or not company_name or not email or not phone or not address:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('maintain_vendor'))
            
            try:
                cursor.execute('''INSERT INTO vendors (username, password, company_name, email, phone, address)
                                 VALUES (?, ?, ?, ?, ?, ?)''',
                              (username, password, company_name, email, phone, address))
                conn.commit()
                flash('Vendor added successfully')
            except sqlite3.IntegrityError:
                flash('Username already exists')
        
        elif action == 'update':
            vendor_id = request.form.get('vendor_id')
            username = request.form.get('username')
            password = request.form.get('password')
            company_name = request.form.get('company_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            if not vendor_id or not username or not password or not company_name or not email or not phone or not address:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('maintain_vendor'))
            
            cursor.execute('''UPDATE vendors SET username=?, password=?, company_name=?, 
                             email=?, phone=?, address=? WHERE id=?''',
                          (username, password, company_name, email, phone, address, vendor_id))
            conn.commit()
            flash('Vendor updated successfully')
    
    cursor.execute("SELECT * FROM vendors")
    vendors = cursor.fetchall()
    conn.close()
    
    return render_template('maintain_vendor.html', vendors=vendors)

@app.route('/admin/maintain_user', methods=['GET', 'POST'])
def maintain_user():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            if not username or not password or not email or not phone or not address:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('maintain_user'))
            
            try:
                cursor.execute('''INSERT INTO users (username, password, role, email, phone, address)
                                 VALUES (?, ?, 'user', ?, ?, ?)''',
                              (username, password, email, phone, address))
                conn.commit()
                flash('User added successfully')
            except sqlite3.IntegrityError:
                flash('Username already exists')
        
        elif action == 'update':
            user_id = request.form.get('user_id')
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            if not user_id or not username or not password or not email or not phone or not address:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('maintain_user'))
            
            cursor.execute('''UPDATE users SET username=?, password=?, email=?, phone=?, address=? 
                             WHERE id=? AND role='user' ''',
                          (username, password, email, phone, address, user_id))
            conn.commit()
            flash('User updated successfully')
    
    cursor.execute("SELECT * FROM users WHERE role='user'")
    users = cursor.fetchall()
    conn.close()
    
    return render_template('maintain_user.html', users=users)

@app.route('/admin/membership', methods=['GET', 'POST'])
def membership():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            user_id = request.form.get('user_id')
            duration = request.form.get('duration')
            
            if not user_id or not duration:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('membership'))
            
            start_date = datetime.now().date()
            
            if duration == '6months':
                end_date = start_date + timedelta(days=180)
            elif duration == '1year':
                end_date = start_date + timedelta(days=365)
            elif duration == '2years':
                end_date = start_date + timedelta(days=730)
            
            cursor.execute('''INSERT INTO memberships (user_id, duration, start_date, end_date, status)
                             VALUES (?, ?, ?, ?, 'active')''',
                          (user_id, duration, start_date, end_date))
            conn.commit()
            flash('Membership added successfully')
        
        elif action == 'update':
            membership_id = request.form.get('membership_id')
            duration = request.form.get('duration')
            cancel = request.form.get('cancel')
            
            if not membership_id or not duration:
                flash('All fields are mandatory')
                conn.close()
                return redirect(url_for('membership'))
            
            cursor.execute("SELECT start_date FROM memberships WHERE id=?", (membership_id,))
            result = cursor.fetchone()
            start_date = datetime.strptime(result['start_date'], '%Y-%m-%d').date()
            
            if duration == '6months':
                end_date = start_date + timedelta(days=180)
            elif duration == '1year':
                end_date = start_date + timedelta(days=365)
            elif duration == '2years':
                end_date = start_date + timedelta(days=730)
            
            status = 'cancelled' if cancel else 'active'
            
            cursor.execute('''UPDATE memberships SET duration=?, end_date=?, status=? WHERE id=?''',
                          (duration, end_date, status, membership_id))
            conn.commit()
            flash('Membership updated successfully')
    
    cursor.execute('''SELECT m.*, u.username FROM memberships m 
                     JOIN users u ON m.user_id = u.id''')
    memberships = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role='user'")
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('membership.html', memberships=memberships, users=users)

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'role' not in session or session['role'] != 'vendor':
        return redirect(url_for('login'))
    return render_template('vendor_dashboard.html')

@app.route('/vendor/add_item', methods=['GET', 'POST'])
def add_item():
    if 'role' not in session or session['role'] != 'vendor':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        description = request.form.get('description')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        
        if not item_name or not description or not price or not quantity:
            flash('All fields are mandatory')
            return redirect(url_for('add_item'))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO items (vendor_id, item_name, description, price, quantity)
                         VALUES (?, ?, ?, ?, ?)''',
                      (session['user_id'], item_name, description, price, quantity))
        conn.commit()
        conn.close()
        flash('Item added successfully')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('add_item.html')

@app.route('/vendor/my_items')
def vendor_items():
    if 'role' not in session or session['role'] != 'vendor':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE vendor_id=?", (session['user_id'],))
    items = cursor.fetchall()
    conn.close()
    
    return render_template('vendor_items.html', items=items)

@app.route('/user/dashboard')
def user_dashboard():
    if 'role' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

@app.route('/user/request_item', methods=['GET', 'POST'])
def request_item():
    if 'role' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        quantity = request.form.get('quantity')
        
        if not item_id or not quantity:
            flash('All fields are mandatory')
            conn.close()
            return redirect(url_for('request_item'))
        
        cursor.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            flash('Item not found')
            conn.close()
            return redirect(url_for('request_item'))
        
        if int(quantity) > item['quantity']:
            flash('Requested quantity not available')
            conn.close()
            return redirect(url_for('request_item'))
        
        total_price = item['price'] * int(quantity)
        
        cursor.execute('''INSERT INTO transactions (user_id, item_id, vendor_id, quantity, total_price, status)
                         VALUES (?, ?, ?, ?, ?, 'pending')''',
                      (session['user_id'], item_id, item['vendor_id'], quantity, total_price))
        
        new_quantity = item['quantity'] - int(quantity)
        cursor.execute("UPDATE items SET quantity=? WHERE id=?", (new_quantity, item_id))
        
        conn.commit()
        conn.close()
        flash('Item requested successfully')
        return redirect(url_for('user_dashboard'))
    
    cursor.execute("SELECT * FROM items WHERE quantity > 0")
    items = cursor.fetchall()
    conn.close()
    
    return render_template('request_item.html', items=items)

@app.route('/user/my_orders')
def user_orders():
    if 'role' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT t.*, i.item_name, v.company_name 
                     FROM transactions t 
                     JOIN items i ON t.item_id = i.id 
                     JOIN vendors v ON t.vendor_id = v.id 
                     WHERE t.user_id=?''', (session['user_id'],))
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('user_orders.html', orders=orders)

@app.route('/admin/reports')
def admin_reports():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT t.*, i.item_name, v.company_name, u.username 
                     FROM transactions t 
                     JOIN items i ON t.item_id = i.id 
                     JOIN vendors v ON t.vendor_id = v.id 
                     JOIN users u ON t.user_id = u.id''')
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('admin_reports.html', orders=orders)

@app.route('/admin/update_status/<int:transaction_id>', methods=['POST'])
def update_status(transaction_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status=? WHERE id=?", (status, transaction_id))
    conn.commit()
    conn.close()
    
    flash('Status updated successfully')
    return redirect(url_for('admin_reports'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
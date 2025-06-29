from flask import Flask, render_template, request, redirect, session, url_for, flash
import json
import os
import random
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'MagickJersey-super-secret-key-2025'

ORDERS_FILE = 'Main/orders.json'
USERS_FILE = 'Main/users.json'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'Stronaa', 'templates'),
           static_folder=os.path.join(BASE_DIR, 'Stronaa', 'static'))
DELIVERY_COST = 20
if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({
            "admin": {
                "password": "admin123",
                "is_admin": True
            }
        }, f)

products = [
    {"id": 1, "name": "Mystery Box NBA", "image": "Ikona.jpg", "description": "Losowa koszulka NBA.", "price": 250, "category": "mystery_jersey"},
    {"id": 2, "name": "Mystery Box NBA CITY", "image": "Ikona.jpg", "description": "Losowa koszulka CITY Editon NBA.", "price": 350, "category": "mystery_jersey"},
    {"id": 3, "name": "Mystery Box NBA ALL TIME", "image": "Ikona.jpg", "description": "Losowa koszulka Autentyk NBA.", "price": 450, "category": "mystery_jersey"},

]

ORDER_STATUSES = ["Oczekiwanie na płatność", "Płatność zaksięgowana", "W trakcie przygotowania", "Wysłane", "Dostarczone", "Anulowane"]
PAYMENT_METHODS = ["Przelew bankowy", "BLIK", "Płatność przy odbiorze"]

def login_required(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Musisz być zalogowany.', 'error')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return decorated

def admin_required(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Musisz być zalogowany.', 'error')
            return redirect(url_for('login'))
        with open(USERS_FILE) as user_file:
            users = json.load(user_file)
        if not users.get(session['username'], {}).get('is_admin'):
            flash('Brak dostępu.', 'error')
            return redirect(url_for('index'))
        return view_func(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    mystery_jerseys = [p for p in products if p['category'] == 'mystery_jersey']
    return render_template('index.html', products=products, mystery_jerseys=mystery_jerseys)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash('Produkt nie został znaleziony.', 'error')
        return redirect(url_for('index'))
    return render_template('product.html', product=product)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    pid = request.form['product_id']
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[pid] = cart.get(pid, 0) + qty
    session['cart'] = cart
    flash('Dodano do koszyka.', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0
    for pid, qty in cart.items():
        product = next((p for p in products if str(p['id']) == pid), None)
        if product:
            item_total = product['price'] * qty
            subtotal += item_total
            cart_items.append({'product': product, 'quantity': qty, 'item_total': item_total})

    total = subtotal + DELIVERY_COST
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, delivery=DELIVERY_COST, total=total)


from datetime import datetime

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        payment_method = request.form['payment_method']


        delivery_method = request.form.get('delivery_method')
        address = request.form.get('address') if delivery_method == 'adres' else None
        locker_code = request.form.get('locker_code') if delivery_method == 'paczkomat' else None
        size = request.form.get('size')
        exclusions = request.form.get('exclusions')
        print("--- FORM DATA ---")
        print("delivery_method:", delivery_method)
        print("address:", address)
        print("locker_code:", locker_code)
        print("size:", size)
        print("exclusions:", exclusions)
        cart = session.get('cart', {})
        order_items = []
        total = DELIVERY_COST
        for pid, qty in cart.items():
            product = next((p for p in products if str(p['id']) == pid), None)
            if product:
                total += product['price'] * qty
                order_items.append({'product_id': pid, 'name': product['name'], 'qty': qty, 'price': product['price']})

        order = {
            'order_number': f"MJ{random.randint(10000, 99999)}",
            'name': name,
            'email': email,
            'payment_method': payment_method,
            'delivery_method': delivery_method,
            'address': address,
            'locker_code': locker_code,
            'size': size,
            'exclusions': exclusions,
            'items': order_items,
            'total': total,
            'status': ORDER_STATUSES[0],
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(ORDERS_FILE, 'r+') as f:
            orders = json.load(f)
            orders.append(order)
            f.seek(0)
            json.dump(orders, f, indent=4)
            f.truncate()

        session.pop('cart', None)
        return render_template('thankyou.html', name=name, order_number=order['order_number'])

    else:
        cart = session.get('cart', {})
        cart_items = []
        total = DELIVERY_COST
        for pid, qty in cart.items():
           product = next((p for p in products if str(p['id']) == pid), None)
           if product:
            cart_items.append({'product': product, 'quantity': qty})
            total += product['price'] * qty

    return render_template('checkout.html', cart_items=cart_items, total=total, payment_methods=PAYMENT_METHODS)








@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(USERS_FILE) as f:
            users = json.load(f)
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['is_admin'] = user.get('is_admin', False)
            flash('Zalogowano.', 'success')
            return redirect(url_for('admin') if user.get('is_admin') else url_for('index'))
        flash('Błędne dane logowania.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Wylogowano.', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin():
    with open(ORDERS_FILE) as f:
        orders = json.load(f)

    pending_payment = sum(1 for o in orders if o['status'] == "Oczekiwanie na płatność")
    paid = sum(1 for o in orders if o['status'] == "Płatność zaksięgowana")
    in_progress = sum(1 for o in orders if o['status'] == "W trakcie przygotowania")
    shipped = sum(1 for o in orders if o['status'] == "Wysłane")

    return render_template("admin.html",
        admin_name=session["username"],
        pending_payment=pending_payment,
        paid=paid,
        in_progress=in_progress,
        shipped=shipped
    )


@app.route('/admin/orders')
@admin_required
def admin_orders():
    with open(ORDERS_FILE) as f:
        orders = json.load(f)
    return render_template("admin_order.html", orders=orders)
@app.route('/admin/status/<status>')
@admin_required
def admin_filter_by_status(status):
    with open(ORDERS_FILE) as f:
        orders = json.load(f)
    filtered = [o for o in orders if o["status"] == status]
    return render_template("admin_order.html", orders=filtered)

@app.route('/admin/order/<order_number>')
@admin_required
def admin_order_detail(order_number):
    with open(ORDERS_FILE) as f:
        orders = json.load(f)

    order = next((o for o in orders if o["order_number"] == order_number), None)

    if order:
        return render_template('admin_order_detail.html', order=order, order_id=order_number, statuses=ORDER_STATUSES)
    else:
        flash("Zamówienie nie istnieje.", "error")
        return redirect(url_for('admin_orders'))


@app.route('/admin/update_order_status/<order_number>', methods=['POST'])
@admin_required
def update_order_status(order_number):
    new_status = request.form.get("status")

    with open(ORDERS_FILE, 'r+') as f:
        orders = json.load(f)
        for order in orders:
            if order["order_number"] == order_number:
                order["status"] = new_status
                break
        f.seek(0)
        json.dump(orders, f, indent=4)
        f.truncate()

    flash("Zmieniono status.", "success")
    return redirect(url_for('admin_order_detail', order_number=order_number))



@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    pid = request.form.get('product_id')
    cart = session.get('cart', {})
    if pid in cart:
        cart.pop(pid)
        session['cart'] = cart
        flash("Usunięto produkt z koszyka", "success")
    return redirect(url_for('cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', {})
    updated_cart = {}
    for key in request.form:
        if key.startswith("quantity_"):
            pid = key.split("_")[1]
            quantity = int(request.form[key])
            if quantity > 0:
                updated_cart[pid] = quantity
    session['cart'] = updated_cart
    flash("Koszyk został zaktualizowany.", "success")
    return redirect(url_for('cart'))



if __name__ == '__main__':
    app.run(debug=True)

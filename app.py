from flask import Flask, render_template, request, redirect, url_for, make_response, json
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    amount_available = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def shop_front():
    products = Product.query.all()
    return render_template('shop_front.html', products=products, not_available=False)

@app.route('/cart')
def cart():
    cart_products = []
    total_cost = 0  # Initialize total cost variable

    if 'cart' in request.cookies:
        cart_products = json.loads(request.cookies.get('cart')) if request.cookies.get('cart') else []

        # Calculate total cost
        total_cost = sum(product['price'] for product in cart_products)

    return render_template('cart.html', cart_products=cart_products, total_cost=total_cost)

@app.route('/admin')
def admin():
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        new_product = Product(
            name=request.form['name'],
            description=request.form['description'],
            image=request.form['image'],
            amount_available=int(request.form['amount']),
            price=float(request.form['price'])
        )
        db.session.add(new_product)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/update_availability', methods=['POST'])
def update_availability():
    if request.method == 'POST':
        product_id = int(request.form['id'])
        new_availability = int(request.form['availability'])
        product = Product.query.get(product_id)
        if product:
            product.amount_available = new_availability
            db.session.commit()
    return redirect(url_for('admin'))

@app.route('/update_price', methods=['POST'])
def update_price():
    if request.method == 'POST':
        product_id = int(request.form['id'])
        new_price = float(request.form['price'])
        product = Product.query.get(product_id)
        if product:
            product.price = new_price
            db.session.commit()
    return redirect(url_for('admin'))

@app.route('/remove_product/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    if request.method == 'POST':
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
    return redirect(url_for('admin'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form['product_id'])
    product = Product.query.get(product_id)
    if product and product.amount_available > 0:
        product.amount_available -= 1
        db.session.commit()
        cart = json.loads(request.cookies.get('cart')) if request.cookies.get('cart') else []
        cart.append({
            'id': product.id,
            'name': product.name,
            'amount_available': product.amount_available,
            'price': product.price
        })
        response = make_response(render_template('shop_front.html', products=Product.query.all()))
        response.set_cookie('cart', json.dumps(cart), samesite='Lax', max_age=3600) 
        return response
    return redirect(url_for('shop_front'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    product = Product.query.get(product_id)
    if product:
        cart = json.loads(request.cookies.get('cart')) if request.cookies.get('cart') else []
        index_to_remove = next((index for (index, p) in enumerate(cart) if p['id'] == product_id), None)
        if index_to_remove is not None:
            removed_product = cart.pop(index_to_remove)
            corresponding_product = Product.query.get(removed_product['id'])
            if corresponding_product:
                corresponding_product.amount_available += 1
                db.session.commit()
            response = make_response(render_template('cart.html', cart_products=cart))
            response.set_cookie('cart', json.dumps(cart), samesite='Lax', max_age=3600)
    return redirect(url_for('cart'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

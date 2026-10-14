import os
import time
from flask import Flask, jsonify, request
from psycopg import connect
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

def db():
    return connect(os.environ['DATABASE_URL'], connect_timeout=3)

@app.get('/')
def index():
    return jsonify(service='ShopAlto', status='online', routes=['/catalog','/orders','/health','/ready'])

@app.get('/health')
def health():
    return jsonify(status='alive')

@app.get('/ready')
def ready():
    try:
        with db() as conn:
            conn.execute('SELECT 1')
        return jsonify(status='ready')
    except Exception as exc:
        return jsonify(status='unavailable', error=str(exc)), 503

@app.get('/catalog')
def catalog():
    with db() as conn:
        rows = conn.execute('SELECT id,name,price FROM products ORDER BY id').fetchall()
    return jsonify([{'id': r[0], 'name': r[1], 'price': float(r[2])} for r in rows])

@app.post('/orders')
def orders():
    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
        if quantity < 1 or quantity > 100:
            raise ValueError('quantity must be between 1 and 100')
    except (KeyError, TypeError, ValueError):
        return jsonify(error='JSON attendu: product_id entier, quantity entier (1..100)'), 400
    with db() as conn:
        row = conn.execute('SELECT price FROM products WHERE id=%s', (product_id,)).fetchone()
        if not row:
            return jsonify(error='Produit inexistant'), 404
        total = row[0] * quantity
        result = conn.execute('INSERT INTO orders(product_id,quantity,total) VALUES (%s,%s,%s) RETURNING id', (product_id,quantity,total)).fetchone()
        conn.commit()
    return jsonify(order_id=result[0], total=float(total)), 201

@app.get('/orders/count')
def order_count():
    with db() as conn:
        row = conn.execute('SELECT count(*) FROM orders').fetchone()
    return jsonify(count=row[0])

@app.get('/slow')
def slow():
    t = min(float(request.args.get('seconds', '2')), 8.0)
    time.sleep(max(t,0))
    return jsonify(delay_seconds=t)

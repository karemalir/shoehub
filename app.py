from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # إنشاء جدول المنتجات
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                description TEXT,
                image TEXT)''')
    
    # إنشاء جدول السلة
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1)''')
    
    # إضافة منتجات تجريبية إذا لم تكن موجودة
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            (1, 'حذاء رياضي', 120.0, 'حذاء رياضي مريح للجري والتمارين', 'shoe1.jpg'),
            (2, 'حذاء رسمي', 150.0, 'حذاء رسمي أنيق للمناسبات', 'shoe2.jpg'),
            (3, 'صندل صيفي', 80.0, 'صندل مريح للصيف', 'shoe3.jpg'),
            (4, 'حذاء تزلج', 200.0, 'حذاء تزلج محترف', 'shoe4.jpg'),
        ]
        c.executemany("INSERT INTO products (id, name, price, description, image) VALUES (?, ?, ?, ?, ?)", products)
    
    conn.commit()
    conn.close()

# الصفحة الرئيسية: عرض المنتجات
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('index.html', products=products)

# صفحة تفاصيل المنتج
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    
    if product:
        return render_template('product.html', product=product)
    return redirect(url_for('index'))

# إضافة منتج إلى السلة (API)
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'success': False, 'message': 'معرف المنتج مطلوب'}), 400
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # التحقق من وجود المنتج في السلة
    c.execute("SELECT * FROM cart WHERE product_id = ?", (product_id,))
    existing_item = c.fetchone()
    
    if existing_item:
        # تحديث الكمية إذا كان المنتج موجوداً
        new_quantity = existing_item[2] + 1
        c.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, existing_item[0]))
    else:
        # إضافة المنتج إلى السلة
        c.execute("INSERT INTO cart (product_id, quantity) VALUES (?, 1)", (product_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'تمت إضافة المنتج إلى السلة'})

# صفحة السلة
@app.route('/cart')
def cart():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # الحصول على محتويات السلة مع تفاصيل المنتجات
    c.execute('''SELECT products.id, products.name, products.price, products.image, cart.quantity 
                 FROM cart 
                 JOIN products ON cart.product_id = products.id''')
    cart_items = c.fetchall()
    
    # حساب الإجمالي
    total = sum(item[2] * item[4] for item in cart_items)
    
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

# حذف عنصر من السلة
@app.route('/remove-from-cart/<int:item_id>')
def remove_from_cart(item_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cart'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
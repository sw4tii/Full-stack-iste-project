from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from flask_cors import CORS # Run: pip install flask-cors

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password123", # Change this to your MySQL password
        database="clothing_store"
    )

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# --- CUSTOMER ROUTES ---
@app.route("/api/customers", methods=["GET", "POST"])
def manage_customers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == "POST":
        data = request.json
        cursor.execute("INSERT INTO Customer (Name, Phone, Address, Email) VALUES (%s, %s, %s, %s)",
                       (data["name"], data["phone"], data["address"], data["email"]))
        db.commit()
        return jsonify({"message": "Customer added!"})
    
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    return jsonify(customers)

@app.route("/api/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM Customer WHERE CustomerID = %s", (id,))
    db.commit()
    return jsonify({"message": "Customer deleted"})

# --- PRODUCT ROUTES ---
@app.route("/api/products", methods=["GET", "POST"])
def manage_products():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == "POST":
        data = request.json
        cursor.execute("INSERT INTO Product (Name, Price, StockQty, Category) VALUES (%s, %s, %s, %s)",
                       (data["name"], data["price"], data["stock"], data["category"]))
        db.commit()
        return jsonify({"message": "Product added!"})
    
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    return jsonify(products)

# --- ORDER ROUTES ---
@app.route("/api/orders", methods=["GET", "POST"])
def manage_orders():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == "POST":
        data = request.json
        # 1. Create Order
        cursor.execute("INSERT INTO Orders (CustomerID, EmployeeID, OrderDate, Status) VALUES (%s, %s, CURDATE(), 'Pending')",
                       (data["customerId"], data["employeeId"]))
        order_id = cursor.lastrowid
        
        # 2. Create Order Item
        cursor.execute("INSERT INTO Order_Item (OrderID, ProductID, Quantity, UnitPrice) VALUES (%s, %s, %s, %s)",
                       (order_id, data["productId"], data["qty"], data["price"]))
        
        # 3. Create initial Payment record
        cursor.execute("INSERT INTO Payment (OrderID, Amount, Method, PaymentDate) VALUES (%s, %s, 'Pending', CURDATE())",
                       (order_id, float(data["qty"]) * float(data["price"])))
        
        # 4. Update Stock
        cursor.execute("UPDATE Product SET StockQty = StockQty - %s WHERE ProductID = %s", (data["qty"], data["productId"]))
        
        db.commit()
        return jsonify({"message": "Order placed!"})

    query = """
        SELECT o.OrderID, c.Name as CustomerName, p.Name as ProductName, o.Status 
        FROM Orders o 
        JOIN Customer c ON o.CustomerID = c.CustomerID
        JOIN Order_Item oi ON o.OrderID = oi.OrderID
        JOIN Product p ON oi.ProductID = p.ProductID
    """
    cursor.execute(query)
    return jsonify(cursor.fetchall())

@app.route("/api/orders/<int:id>", methods=["PATCH"])
def update_order_status(id):
    status = request.json['status']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE Orders SET Status = %s WHERE OrderID = %s", (status, id))
    db.commit()
    return jsonify({"message": "Status updated"})

# --- EMPLOYEES & PAYMENTS ---
@app.route("/api/employees", methods=["GET", "POST"])
def manage_employees():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        data = request.json
        cursor.execute("INSERT INTO Employee (Name, Role, Phone) VALUES (%s, %s, %s)", (data["name"], data["role"], data["phone"]))
        db.commit()
    cursor.execute("SELECT * FROM Employee")
    return jsonify(cursor.fetchall())

@app.route("/api/payments")
def get_payments():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Payment")
    return jsonify(cursor.fetchall())

@app.route("/api/stats")
def get_stats():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM Customer")
    custs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Orders")
    orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Product")
    prods = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(Amount) FROM Payment")
    rev = cursor.fetchone()[0] or 0
    return jsonify({"customers": custs, "orders": orders, "products": prods, "revenue": float(rev)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
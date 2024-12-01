from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from functools import wraps
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = '1234567890'  # Thay đổi thành khóa bảo mật hơn trong môi trường thực tế

# Kết nối đến MySQL
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='qlbanhangdientu_basic'
    )
    cursor = conn.cursor(dictionary=True)  # Sử dụng dictionary cursor để dễ dàng truy cập cột theo tên
except Error as e:
    print(f"Error connecting to MySQL: {e}")
    conn = None

@app.route("/get_data", methods=['GET'])
def get_data():
    cursor.execute("SELECT * FROM `type_product`")  # Thay bằng bảng của bạn
    rows = cursor.fetchall()
    # Chuyển đổi dữ liệu từ tuple thành danh sách từ điển
    listdanhmuc = [{"id": row['id'], "name": row['nameproduct']} for row in rows]
    return jsonify(listdanhmuc)

@app.route("/")
def index():
    return render_template("test.html")
    
if __name__ == "__main__":
    app.run(debug=True)
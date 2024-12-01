from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from functools import wraps
import mysql.connector
from mysql.connector import Error
import os
import uuid
import datetime
from datetime import timedelta

app = Flask(__name__)
app.secret_key = '1234567890'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

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

IMAGE_FOLDER_type_product = 'static/img/type_product'  # Đảm bảo thư mục này đã tồn tại
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER_type_product
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Hàm kiểm tra định dạng file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorator kiểm tra đăng nhập
def checklogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_inadmin' in session and session.get('logged_inadmin') == True:
            return f(*args, **kwargs)
        else:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('adminlogin'))
    return decorated_function

# Route đăng nhập admin
@app.route('/admin/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if 'logged_inadmin' in session and session.get('logged_inadmin') == True:
        return redirect(url_for('dashboardadmin'))
    
    if request.method == 'POST':
        # Lấy giá trị từ form với `get` để tránh KeyError nếu trường không tồn tại
        username = request.form.get('username')
        password = request.form.get('password')
        # Truy vấn cơ sở dữ liệu để xác thực
        try:
            cursor.execute("SELECT * FROM `account` WHERE `username` = %s AND `password` = %s", (username, password))
            adminAccount = cursor.fetchone()

            if adminAccount:
                # Đặt các thông tin vào session sau khi đăng nhập thành công
                session['logged_inadmin'] = True
                session['fullname'] = adminAccount['fullname']
                session['address'] = adminAccount['address']
                session['id'] = adminAccount['id']
                session['Shop_name'] = adminAccount['Shop_name']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboardadmin'))
            else:
                flash('Incorrect username or password.', 'danger')
        except Error as e:
            flash(f"Database error: {e}", 'danger')
    
    return render_template('admin/login.html')

# Route đăng xuất
@app.route('/admin/logout')
@checklogin  
def logoutadmin():
    session.pop('logged_inadmin', None)
    session.pop('fullname', None)
    session.pop('address', None)
    session.pop('id', None)
    session.pop('Shop_name', None)
    return redirect(url_for('adminlogin'))


# Route trang chủ dành cho admin
@app.route('/admin/dashboard')
@checklogin  # Kiểm tra đăng nhập trước khi truy cập
def dashboardadmin():
    return render_template('admin/dashboard.html')

@app.route("/admin/danhmuc")
@checklogin  
def danhmuc():
    cursor.execute("SELECT * FROM `type_product`")
    listdanhmuc = cursor.fetchall()
    return render_template("admin/danhmuc.html", listdanhmuc=listdanhmuc)

@app.route("/admin/themdanhmuc", methods=['POST'])
@checklogin
def themdanhmuc():
    category_name = request.form.get('new-category-name')
    image_file = request.files['new-category-image']
    
    # Đổi tên file để tránh trùng lặp
    unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
    image_relative_path = f"img/type_product/{unique_filename}"  # Đường dẫn tương đối
    image_absolute_path = os.path.join(app.static_folder, image_relative_path)
    
    # Lưu ảnh vào thư mục
    image_file.save(image_absolute_path)

    # Lấy ngày giờ hiện tại
    create_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Thêm danh mục vào cơ sở dữ liệu
    query = "INSERT INTO type_product (nameproduct, status, Create_date, img) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (category_name, 'true', create_date, unique_filename))
    conn.commit()
    
    return redirect('/admin/danhmuc')

@app.route("/admin/suadanhmuc", methods=['POST'])
@checklogin
def suadanhmuc():
    category_name = request.form.get('category-name') #tên danh mục
    category_id = request.form.get('category-id')  #id cần sửa
    image_file = request.files['category-image'] #ảnh mới
    
    # Đổi tên file để tránh trùng lặp
    unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
    image_relative_path = f"img/type_product/{unique_filename}"  # Đường dẫn tương đối
    image_absolute_path = os.path.join(app.static_folder, image_relative_path)
    
    # Lưu ảnh vào thư mục
    image_file.save(image_absolute_path)

    # Lấy ngày giờ hiện tại
    create_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Thêm danh mục vào cơ sở dữ liệu
    cursor.execute('UPDATE type_product SET nameproduct = %s, img = %s WHERE id = %s', (category_name, unique_filename, category_id))
    conn.commit()
    
    return redirect('/admin/danhmuc')

@app.route("/admin/xoadanhmuc/<int:id>", methods=['GET'])
@checklogin 
def xoadanhmuc(id):
    cursor.execute("DELETE FROM `type_product` WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/danhmuc')

@app.route("/admin/suatrangthai/<int:id>", methods=['GET'])
@checklogin 
def suatrangthai(id):
    status = request.args.get('status')
    if status=='true':
        cursor.execute("UPDATE `type_product` SET `status` = 'false' WHERE `id` = %s", (id,))
    else: cursor.execute("UPDATE `type_product` SET `status` = 'true' WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/danhmuc')

@app.route("/admin/sanpham")
@checklogin  
def sanpham():
    cursor.execute("SELECT * FROM `product`")
    listsanpham = cursor.fetchall()
    cursor.execute("SELECT * FROM `type_product`")
    listdanhmuc = cursor.fetchall()
    return render_template("admin/sanpham.html", listsanpham=listsanpham, listdanhmuc=listdanhmuc)

@app.route("/admin/themsanpham", methods=['POST'])
@checklogin
def themsanpham():
    try:
        loaisanpham = request.form.get('loaisanpham')  # Loại sản phẩm
        tensanpham = request.form.get('tensanpham')  # Tên sản phẩm
        soluong = request.form.get('soluong')  # Số lượng
        dongia = request.form.get('dongia')  # Số lượng
        mota = request.form.get('mota')  # Mô tả
        image_file = request.files.get('new-category-image')  # File ảnh

        # Kiểm tra nếu file không tồn tại
        if not image_file or image_file.filename == '':
            return "Hãy chọn một tệp ảnh!", 400

        # Đổi tên file để tránh trùng lặp
        unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
        image_relative_path = f"img/products/{unique_filename}"  # Đường dẫn tương đối
        image_absolute_path = os.path.join(app.static_folder, image_relative_path)

        # Lưu ảnh vào thư mục
        os.makedirs(os.path.dirname(image_absolute_path), exist_ok=True)  # Tạo thư mục nếu chưa có
        image_file.save(image_absolute_path)

        # Lấy ngày giờ hiện tại
        create_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Thêm sản phẩm vào cơ sở dữ liệu
        query = '''
            INSERT INTO product (type_product, nameproduct, quantity, `describe`, status, img, create_day, sold, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        cursor.execute(query, (loaisanpham, tensanpham, soluong, mota, 'true', unique_filename, create_date, 0, dongia))
        conn.commit()

        return redirect('/admin/sanpham')
    except Exception as e:
        return f"Lỗi: {str(e)}", 500

@app.route("/admin/suasanpham", methods=['POST'])
@checklogin
def suasanpham():
    category_idsp = request.form.get('idsp')  # id sản phẩm
    category_loaisanpham = request.form.get('loaisanpham')  # Loại sản phẩm
    category_name = request.form.get('category-name') # Tên sản phẩm
    category_soluong = request.form.get('soluong') # Số lượng
    category_dongia = request.form.get('dongia') # Đơn giá
    category_mota = request.form.get('mota') # Mô tả
    image_file = request.files['category-image'] #ảnh mới
    
    # Đổi tên file để tránh trùng lặp
    unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
    image_relative_path = f"img/products/{unique_filename}"  # Đường dẫn tương đối
    image_absolute_path = os.path.join(app.static_folder, image_relative_path)
    
    # Lưu ảnh vào thư mục
    image_file.save(image_absolute_path)
    
    # Thêm danh mục vào cơ sở dữ liệu
    query = '''UPDATE product 
               SET type_product = %s, nameproduct = %s, quantity = %s, `describe` = %s , img = %s, price = %s
               WHERE id = %s'''
    cursor.execute(query, (category_loaisanpham, category_name, category_soluong, category_mota, unique_filename, category_idsp, category_dongia))
    conn.commit()
    
    return redirect('/admin/sanpham')

@app.route("/admin/xoasanpham/<int:id>", methods=['GET'])
@checklogin 
def xoasanpham(id):
    cursor.execute("SELECT img FROM `product` WHERE `id` = %s", (id,))
    row = cursor.fetchone()
    img_file = row['img']
    os.remove(os.path.join(app.static_folder, f"img/products/{img_file}"))
    cursor.execute("DELETE FROM `product` WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/sanpham')

@app.route("/admin/suatrangthaisanpham/<int:id>", methods=['GET'])
@checklogin 
def suatrangthaisanpham(id):
    status = request.args.get('status')
    if status=='true':
        cursor.execute("UPDATE `product` SET `status` = 'false' WHERE `id` = %s", (id,))
    else: cursor.execute("UPDATE `product` SET `status` = 'true' WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/danhmuc')

@app.route("/admin/donhang")
@checklogin  
def donhang():
    cursor.execute("SELECT * FROM `bill` WHERE `status` <> 'Add'")
    listdonhang = cursor.fetchall()
    cursor.execute("SELECT * FROM `delivery_address`")
    address_delivery = cursor.fetchall()
    cursor.execute("SELECT * FROM `account_user`")
    account_user = cursor.fetchall()
    cursor.execute("SELECT * FROM `product`")
    listsanpham = cursor.fetchall()
    return render_template("admin/donhang.html", 
                           listdonhang=listdonhang,
                           address_delivery=address_delivery, 
                           account_user=account_user, 
                           listsanpham=listsanpham)

@app.route("/admin/suatrangthaidonhang/<int:id>", methods=['GET'])
@checklogin 
def suatrangthaidonhang(id):
    status = request.args.get('action')
    if status=='Confirmed':
        cursor.execute("UPDATE `bill` SET `status` = 'Confirmed' WHERE `id` = %s", (id,))
    else: cursor.execute("UPDATE `bill` SET `status` = 'Cancelled' WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/donhang')

@app.route("/admin/thanhtoan")
@checklogin  
def thanhtoan():
    cursor.execute("SELECT * FROM `payment_methods`")
    payment_methods = cursor.fetchall()
    return render_template("admin/thanhtoan.html", payment_methods=payment_methods)

@app.route("/admin/cappheppayment_methods/<int:id>", methods=['GET'])
@checklogin 
def cappheppayment_methods(id):
    status = request.args.get('action')
    
    if id==2 and status=='true':
        cursor.execute("UPDATE `payment_methods` SET `status` = 'false' WHERE `id` <> 1", ())
        conn.commit()
        return redirect('/admin/thanhtoan')
    
    if status=='true':
        cursor.execute("UPDATE `payment_methods` SET `status` = 'false' WHERE `id` = %s", (id,))
    else: cursor.execute("UPDATE `payment_methods` SET `status` = 'true' WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/thanhtoan')

@app.route("/admin/themthanhtoan", methods=['POST'])
@checklogin
def themthanhtoan():
    try:
        stk = request.form.get('stk')  # Loại sản phẩm
        ctk = request.form.get('ctk')  # Tên sản phẩm
        tnh = request.form.get('tnh')  # Số lượng
        image_file = request.files.get('imgInput')  # File ảnh

        # Kiểm tra nếu file không tồn tại
        if not image_file or image_file.filename == '':
            return "Hãy chọn một tệp ảnh!", 400

        # Đổi tên file để tránh trùng lặp
        unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
        image_relative_path = f"img/payment_methods/{unique_filename}"  # Đường dẫn tương đối
        image_absolute_path = os.path.join(app.static_folder, image_relative_path)

        # Lưu ảnh vào thư mục
        os.makedirs(os.path.dirname(image_absolute_path), exist_ok=True)  # Tạo thư mục nếu chưa có
        image_file.save(image_absolute_path)

        # Lấy ngày giờ hiện tại
        create_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Thêm sản phẩm vào cơ sở dữ liệu
        query = '''
            INSERT INTO payment_methods (stk, chutaikhoan, tennganhang, create_date, img, glob, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''
        cursor.execute(query, (stk, ctk, tnh, create_date, unique_filename, '', 'true'))
        conn.commit()
        return redirect('/admin/thanhtoan')
    except Exception as e:
        return f"Lỗi: {str(e)}", 500

@app.route("/admin/tintuc")
@checklogin  
def tintuc():
    cursor.execute("SELECT * FROM `news`")
    listtintuc = cursor.fetchall()
    return render_template("admin/tintuc.html", listtintuc=listtintuc)

@app.route("/admin/xoatintuc/<int:id>", methods=['GET'])
@checklogin 
def xoatintuc(id):
    cursor.execute("SELECT img FROM `news` WHERE `id` = %s", (id,))
    row = cursor.fetchone()
    img_file = row['img']
    os.remove(os.path.join(app.static_folder, f"img\\news\\{img_file}"))
    cursor.execute("DELETE FROM `news` WHERE `id` = %s", (id,))
    conn.commit()
    return redirect('/admin/tintuc')

@app.route("/admin/themtintuc", methods=['POST'])
@checklogin
def themtintuc():
    try:
        title = request.form.get('title')  # Loại sản phẩm
        description = request.form.get('description')  
        image_file = request.files.get('image')  # File ảnh

        # Kiểm tra nếu file không tồn tại
        if not image_file or image_file.filename == '':
            return "Hãy chọn một tệp ảnh!", 400

        # Đổi tên file để tránh trùng lặp
        unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
        image_relative_path = f"img/payment_methods/{unique_filename}"  # Đường dẫn tương đối
        image_absolute_path = os.path.join(app.static_folder, image_relative_path)

        # Lưu ảnh vào thư mục
        os.makedirs(os.path.dirname(image_absolute_path), exist_ok=True)  # Tạo thư mục nếu chưa có
        image_file.save(image_absolute_path)

        # Lấy ngày giờ hiện tại
        create_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Thêm sản phẩm vào cơ sở dữ liệu
        query = '''
            INSERT INTO news (title, img, content, created_day)
            VALUES (%s, %s, %s, %s);
        '''
        cursor.execute(query, (title, unique_filename, description, create_date))
        conn.commit()
        return redirect('/admin/tintuc')
    except Exception as e:
        return f"Lỗi: {str(e)}", 500

@app.route("/admin/taikhoancanhan")
@checklogin  
def taikhoancanhan():
    cursor.execute("SELECT * FROM `account`")
    listtaikhoan = cursor.fetchone()
    return render_template("admin/taikhoancanhan.html", listtaikhoan=listtaikhoan)

#check login user
def checkloginuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_inuser' in session and session.get('logged_inuser') == True:
            return f(*args, **kwargs)
        else:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('/login'))
    return decorated_function

# code cho user
@app.route("/")
def trangchu():
    cursor.execute("SELECT * FROM `type_product` WHERE `status` = 'true'")
    listdanhmuc = cursor.fetchall()
    cursor.execute("SELECT * FROM `product` WHERE `status` = 'true'")
    listsanpham = cursor.fetchall()
    return render_template("user/index.html", listdanhmuc=listdanhmuc, listsanpham=listsanpham)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'logged_inuser' in session and session.get('logged_inuser'):
        return redirect("/")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor.execute("SELECT * FROM `account_user` WHERE `username` = %s", (username,))
        log = cursor.fetchone()

        if log and log['password'] == password: 
            session['logged_inuser'] = True
            session['fullname'] = log['fullname']
            session['id'] = log['id']
            cursor.execute("SELECT COUNT(*) AS count FROM bill WHERE id_account=%s and status='Add'", (log['id'],))
            session['count_order'] = cursor.fetchone()['count']
            return redirect("/")
        else:
            return redirect("/login")
    return render_template("user/loginuser.html")

@app.route("/logout")
def logout():
    session.pop('logged_inuser', None)
    session.pop('fullname', None)
    session.pop('id', None)
    session.pop('count_order', None)
    return redirect("/")

@app.route("/register")
def register():
    return render_template("user/registeruser.html")

@app.route("/chitietsanpham/<int:id>", methods=['GET'])
def chitietsanpham(id):
    cursor.execute("SELECT * FROM `type_product` WHERE `status` = 'true'")
    listdanhmuc = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS count FROM bill WHERE id_account=%s and status='Add'", (session['id'],))
    session['count_order'] = cursor.fetchone()['count']
    cursor.execute("SELECT * FROM `product` WHERE `id` = %s", (id,))
    listsanpham = cursor.fetchone()
    return render_template("user/chititetsp.html", listdanhmuc=listdanhmuc, listsanpham=listsanpham)

@app.route("/addToCart", methods=['POST'])
@checkloginuser
def addToCart():
    quantity = request.form.get('quantity')
    id_account = request.form.get('id_account')
    id_sp = request.form.get('id_sp')
    cursor.execute("INSERT INTO bill (id_account, id_product, quantity, status, create_day) VALUES (%s, %s, %s, %s, %s)", (id_account, id_sp, quantity, 'Add', datetime.datetime.now()))
    conn.commit()
    cursor.execute("SELECT COUNT(*) AS count FROM bill WHERE id_account=%s and status='Add'", (session['id'],))
    session['count_order'] = cursor.fetchone()['count']
    return redirect("/")

@app.route("/buyNow", methods=['POST'])
@checkloginuser
def buyNow():
    quantity = request.form.get('sl')
    id_account = request.form.get('id_account')
    id_sp = request.form.get('idsp')
    address = request.form.get('address')  # Lấy địa chỉ giao hàng
    address_detail = request.form.get('address_detail')  # Lấy địa chỉ chi tiết
    
    # Ghép địa chỉ đầy đủ
    full_address = 1
    
    # Lấy thời gian hiện tại
    create_day = datetime.datetime.now()
    
    # Thực hiện thêm dữ liệu vào bảng `bill`
    cursor.execute(
        """
        INSERT INTO bill (id_account, id_product, quantity, status, create_day, address_delivery) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """, 
        (id_account, id_sp, quantity, 'Processing', create_day, full_address)
    )
    conn.commit()
    cursor.execute("SELECT COUNT(*) AS count FROM bill WHERE id_account=%s and status='Add'", (session['id'],))
    session['count_order'] = cursor.fetchone()['count']
    return redirect("/")

@app.route("/giohangxin")
@checkloginuser
def giohangxin():
    cursor.execute("SELECT * FROM bill WHERE status = 'Add'")
    listgiohang = cursor.fetchall()
    cursor.execute("SELECT * FROM `product`")
    listsanpham = cursor.fetchall()
    cursor.execute("SELECT * FROM `delivery_address`")
    address_delivery = cursor.fetchall()
    cursor.execute("SELECT * FROM `account_user`")
    account_user = cursor.fetchall()
    cursor.execute("SELECT * FROM bill WHERE status <> 'Add'")
    listgiohang1 = cursor.fetchall()
    return render_template("user/giohangxin.html", listgiohang=listgiohang, listsanpham=listsanpham, address_delivery=address_delivery, account_user=account_user, listgiohang1=listgiohang1)

@app.route("/buy/<int:id>", methods=['GET'])
@checkloginuser
def buy(id):
    cursor.execute("UPDATE bill SET status = 'Processing' WHERE id = %s", (id,))
    conn.commit()
    return redirect("/giohangxin")

@app.route("/cancel/<int:id>", methods=['GET'])
@checkloginuser
def cancel(id):
    cursor.execute("DELETE FROM bill WHERE id = %s", (id,))
    conn.commit()
    return redirect("/giohangxin")

@app.route("/news")
def news():
    cursor.execute("SELECT * FROM news")
    listtintuc = cursor.fetchall()
    return render_template("user/tintuc.html", listtintuc=listtintuc)

@app.route("/fullproducts")
def fullproducts():
    cursor.execute("SELECT * FROM product")
    listsanpham = cursor.fetchall()
    cursor.execute("SELECT * FROM type_product")
    listdanhmuc = cursor.fetchall()
    return render_template("user/fullproducts.html", listsanpham=listsanpham, listdanhmuc=listdanhmuc)


if __name__ == "__main__":
    app.run(debug=True)

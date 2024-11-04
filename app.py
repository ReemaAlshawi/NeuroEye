from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, send_file
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # استبدلي هذا المفتاح بمفتاح آمن

# قاعدة بيانات وهمية (يمكنك استبدالها بقاعدة بيانات حقيقية أو عملية تحقق خارجية)
users = {
    'Dr. Laith': 'Laith123',
    'Dr. Abdullah': 'Abdullah123',
    'Dr. Ali': 'Ali123'
}

ADMIN_USERNAME = 'shaikha'
ADMIN_PASSWORD = 'shaikha1'

# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('welcome.html')  # عرض صفحة الترحيب بخيارات تسجيل الدخول

# تسجيل دخول المستخدم
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # تحقق من وجود المستخدم وصحة كلمة المرور
        if username in users and users[username] == password:
            session['username'] = username  # حفظ اسم المستخدم في الجلسة
            return redirect(url_for('label'))  # الانتقال إلى صفحة التصنيف
        else:
            return "Invalid username or password."

    return render_template('user_login.html')  # عرض صفحة تسجيل دخول المستخدم

# صفحة التصنيف (تتطلب تسجيل الدخول)
@app.route('/label')
def label():
    if 'username' in session:
        username = session['username']
        return render_template('index.html', username=username)  # عرض صفحة التصنيف
    else:
        return redirect(url_for('user_login'))  # الانتقال إلى تسجيل الدخول إذا لم يتم تسجيل الدخول

# تسجيل دخول المشرف
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # تحقق من بيانات المشرف
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True  # حفظ حالة المشرف في الجلسة
            return redirect(url_for('admin_dashboard'))  # الانتقال إلى لوحة المشرف
        else:
            return "Invalid admin credentials."

    return render_template('admin_login.html')  # عرض صفحة تسجيل دخول المشرف

# لوحة المشرف (تتطلب تسجيل الدخول كمشرف)
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):  # تحقق من تسجيل الدخول كمشرف
        return redirect(url_for('admin_login'))  # الانتقال إلى تسجيل دخول المشرف إذا لم يتم تسجيل الدخول

    csv_file_path = 'images.csv'  # مسار ملف CSV

    total_images = 0
    normal_images = 0
    cataract_images = 0

    # متابعة عدد الصور التي قام كل مستخدم بتصنيفها
    user_labels_normal = {user: 0 for user in users}  
    user_labels_cataract = {user: 0 for user in users}

    # قراءة ملف CSV وحساب التصنيفات
    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                total_images += 1
                if 'normal' in row['imagePath'].lower():
                    normal_images += 1  # عدد الصور الطبيعية
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_normal[user] += 1
                else:
                    cataract_images += 1  # عدد صور الكتاركت
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_cataract[user] += 1

        # حساب النسب
        total_labeled = {user: user_labels_normal[user] + user_labels_cataract[user] for user in users}
        labeled_percentage_normal = {user: (user_labels_normal[user] / normal_images) * 100 if normal_images > 0 else 0 for user in users}
        labeled_percentage_cataract = {user: (user_labels_cataract[user] / cataract_images) * 100 if cataract_images > 0 else 0 for user in users}
        labeled_percentage_total = {user: (total_labeled[user] / total_images) * 100 if total_images > 0 else 0 for user in users}

        # عرض لوحة التحكم مع البيانات
        return render_template(
            'admin_dashboard.html',
            total_images=total_images,
            normal_images=normal_images,
            cataract_images=cataract_images,
            user_labels_normal=user_labels_normal,
            user_labels_cataract=user_labels_cataract,
            total_labeled=total_labeled,
            labeled_percentage_normal=labeled_percentage_normal,
            labeled_percentage_cataract=labeled_percentage_cataract,
            labeled_percentage_total=labeled_percentage_total
        )

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return "Error reading CSV file", 500

# تنزيل ملف CSV
@app.route('/download_csv')
def download_csv():
    return send_from_directory('.', 'images.csv', as_attachment=True)

# تسجيل الخروج للمستخدم
@app.route('/logout')
def logout():
    session.pop('username', None)  # إزالة اسم المستخدم من الجلسة
    return redirect(url_for('user_login'))  # الانتقال إلى تسجيل دخول المستخدم

# تسجيل الخروج للمشرف
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)  # إزالة حالة المشرف من الجلسة
    return redirect(url_for('home'))  # الانتقال إلى الصفحة الرئيسية

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # قراءة المنفذ من المتغير البيئي أو استخدام 5000 كرقم افتراضي
    app.run(host="0.0.0.0", port=port)  # تشغيل التطبيق على 0.0.0.0

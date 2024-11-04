from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Dummy databases (replace with a real database or external authentication)
users = {
    'Dr. Laith': 'Laith123',
    'Dr. Abdullah': 'Abdullah123',
    'Dr. Ali': 'Ali123'
}

ADMIN_USERNAME = 'shaikha'
ADMIN_PASSWORD = 'shaikha1'

# استخدام مسار مطلق للملف
csv_file_path = os.path.join(app.root_path, 'static', 'images.csv')
print("CSV file path:", csv_file_path)  # للتأكد من مسار الملف

# Ensure the CSV file exists on start
def ensure_csv_exists():
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'imagePath', 'label_user1', 'label_user2', 'label_user3'])

# Call the function on start
ensure_csv_exists()

# Home page route to display the welcome page with options for user and admin login
@app.route('/')
def home():
    return render_template('welcome.html')

# User login route
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('label'))
        else:
            return "Invalid username or password."
    return render_template('user_login.html')

# Labeling page (only accessible if logged in as a user)
@app.route('/label')
def label():
    if 'username' in session:
        username = session['username']
        return render_template('index.html', username=username)
    else:
        return redirect(url_for('user_login'))

# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid admin credentials."
    return render_template('admin_login.html')

# Admin dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    total_images, normal_images, cataract_images = 0, 0, 0
    user_labels_normal = {user: 0 for user in users}
    user_labels_cataract = {user: 0 for user in users}

    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                total_images += 1
                if 'normal' in row['imagePath'].lower():
                    normal_images += 1
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_normal[user] += 1
                else:
                    cataract_images += 1
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_cataract[user] += 1

        total_labeled = {user: user_labels_normal[user] + user_labels_cataract[user] for user in users}
        labeled_percentage_normal = {user: (user_labels_normal[user] / normal_images) * 100 if normal_images > 0 else 0 for user in users}
        labeled_percentage_cataract = {user: (user_labels_cataract[user] / cataract_images) * 100 if cataract_images > 0 else 0 for user in users}
        labeled_percentage_total = {user: (total_labeled[user] / total_images) * 100 if total_images > 0 else 0 for user in users}

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

# Route for saving the label in the CSV file
@app.route('/save_label', methods=['POST'])
def save_label():
    if 'username' in session:
        try:
            data = request.json
            image_url = data['imagePath']
            label = data['label']
            username = session.get('username')

            rows = []
            updated = False

            with open(csv_file_path, mode='r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if row['imagePath'] == image_url:
                        row[f'label_{username}'] = label
                        updated = True
                    rows.append(row)

            if updated:
                with open(csv_file_path, mode='w', newline='') as file:
                    fieldnames = ['id', 'imagePath', 'label_user1', 'label_user2', 'label_user3']
                    csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                    csv_writer.writeheader()
                    csv_writer.writerows(rows)

            return jsonify({'status': 'Label updated successfully'})
        except Exception as e:
            print(f"Error occurred: {e}")
            return jsonify({'status': 'Error occurred', 'message': str(e)}), 500
    else:
        return redirect(url_for('user_login'))

# Download CSV file route
@app.route('/download_csv')
def download_csv():
    return send_from_directory('static', 'images.csv', as_attachment=True)  # تعديل المسار ليشير إلى static

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

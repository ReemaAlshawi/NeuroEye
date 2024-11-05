from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import csv
import os
from waitress import serve


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Dummy user and admin credentials
users = {
    'Dr. Laith': 'Laith123',
    'Dr. Abdullah': 'Abdullah123',
    'Dr. Ali': 'Ali123'
}

ADMIN_USERNAME = 'shaikha'
ADMIN_PASSWORD = 'shaikha1'

csv_file_path = 'images.csv'  # Path to the CSV file

# Home page route to display the welcome page with options for user and admin login
@app.route('/')
def home():
    return render_template('welcome.html')  # Show welcome page with login options

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

# Labeling page for logged-in users
@app.route('/label')
def label():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
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

# Admin dashboard route (accessible only to admin)
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

        # Calculate label percentages for each user
        total_labeled = {user: user_labels_normal[user] + user_labels_cataract[user] for user in users}
        labeled_percentage_normal = {user: (user_labels_normal[user] / normal_images) * 100 if normal_images > 0 else 0 for user in users}
        labeled_percentage_cataract = {user: (user_labels_cataract[user] / cataract_images) * 100 if cataract_images > 0 else 0 for user in users}
        labeled_percentage_total = {user: (total_labeled[user] / total_images) * 100 if total_images > 0 else 0 for user in users}

        return render_template('admin_dashboard.html',
                               total_images=total_images,
                               normal_images=normal_images,
                               cataract_images=cataract_images,
                               user_labels_normal=user_labels_normal,
                               user_labels_cataract=user_labels_cataract,
                               total_labeled=total_labeled,
                               labeled_percentage_normal=labeled_percentage_normal,
                               labeled_percentage_cataract=labeled_percentage_cataract,
                               labeled_percentage_total=labeled_percentage_total)

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return "Error reading CSV file", 500

# Get images for the logged-in user to label
@app.route('/get_images')
def get_images():
    image_urls = []
    username = session.get('username')
    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            label_column = f'label_{username}'
            for row in csv_reader:
                if row[label_column] == 'Null':
                    image_urls.append(row['imagePath'])
        return jsonify(image_urls)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return jsonify([]), 500


# Save the label in the CSV file
@app.route('/save_label', methods=['POST'])
def save_label():
    if 'username' in session:
        try:
            data = request.json
            image_url = data['imagePath']
            label = data['label']
            username = session.get('username')
            rows = []

            with open(csv_file_path, mode='r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if row['imagePath'] == image_url:
                        row[f'label_{username}'] = label
                    rows.append(row)

            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['id', 'imagePath'] + [f'label_{user}' for user in users]
                csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(rows)

            return jsonify({'status': 'Label updated successfully'})

        except Exception as e:
            print(f"Error occurred: {e}")
            return jsonify({'status': 'Error occurred', 'message': str(e)}), 500
    else:
        return redirect(url_for('user_login'))

# Thank you page route
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# Logout route for regular users
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('user_login'))

# Logout route for admin users
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

# Download CSV file route
@app.route('/download_csv')
def download_csv():
    return send_from_directory('.', 'images.csv', as_attachment=True)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import csv

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

        # Check if the user exists and the password matches
        if username in users and users[username] == password:
            session['username'] = username  # Save the username in session
            return redirect(url_for('label'))  # Redirect to the labeling page
        else:
            return "Invalid username or password."

    return render_template('user_login.html')  # Render the user login page

# Labeling page (only accessible if logged in as a user)
@app.route('/label')
def label():
    if 'username' in session:
        username = session['username']
        return render_template('index.html', username=username)  # Show labeling page
    else:
        return redirect(url_for('user_login'))  # Redirect to user login if not logged in

# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True  # Save admin status in session
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
        else:
            return "Invalid admin credentials."

    return render_template('admin_login.html')  # Render the admin login page

# Admin dashboard route (only accessible if logged in as admin)
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):  # Check if admin is logged in
        return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in

    csv_file_path = 'images.csv'  # Path to the CSV file

    total_images = 0
    normal_images = 0
    cataract_images = 0

    # Track how many images each user has labeled
    user_labels_normal = {user: 0 for user in users}  
    user_labels_cataract = {user: 0 for user in users}

    # Read the CSV file and count labels
    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                total_images += 1
                if 'normal' in row['imagePath'].lower():
                    normal_images += 1  # Count normal images
                    # Count labels for normal images
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_normal[user] += 1
                else:
                    cataract_images += 1  # Count cataract images
                    # Count labels for cataract images
                    for user in users:
                        if row[f'label_{user}'] != 'Null':
                            user_labels_cataract[user] += 1

        # Calculate percentages
        total_labeled = {user: user_labels_normal[user] + user_labels_cataract[user] for user in users}
        labeled_percentage_normal = {user: (user_labels_normal[user] / normal_images) * 100 if normal_images > 0 else 0 for user in users}
        labeled_percentage_cataract = {user: (user_labels_cataract[user] / cataract_images) * 100 if cataract_images > 0 else 0 for user in users}
        labeled_percentage_total = {user: (total_labeled[user] / total_images) * 100 if total_images > 0 else 0 for user in users}

        # Render the dashboard with the data
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


# Route to get images for the labeling process (user-specific logic)
@app.route('/get_images', methods=['GET'])
def get_images():
    image_urls = []
    username = session.get('username')  # Get the current logged-in user
    csv_file_path = 'images.csv'  # Path to the CSV file

    # Read the CSV file and get image paths for images not labeled by the current user
    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            label_column = f'label_{username}'  # Determine which column corresponds to the logged-in user

            for row in csv_reader:
                if row[label_column] == 'Null':  # Check if the image has not been labeled by the user
                    image_urls.append(row['imagePath'])  # Add image path to list

        # Return image paths as JSON
        return jsonify(image_urls)

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return jsonify([]), 500

# Custom route to serve images from the Dataset folder
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('Dataset', filename)

# Route for saving the label in the CSV file (example logic)
@app.route('/save_label', methods=['POST'])
def save_label():
    if 'username' in session:
        try:
            data = request.json
            image_url = data['imagePath']
            label = data['label']
            username = session.get('username')  # Get the logged-in user's name

            csv_file_path = 'images.csv'
            rows = []

            # Read and update the CSV
            with open(csv_file_path, mode='r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if row['imagePath'] == image_url:
                        row[f'label_{username}'] = label  # Update the corresponding label
                    rows.append(row)

            # Write the updated rows back to the CSV
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

# Thank you page route
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# User logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from session
    return redirect(url_for('user_login'))  # Redirect back to user login page

# Admin logout route
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)  # Remove admin status from session
    return redirect(url_for('home'))  # Redirect back to the home (welcome) page


if __name__ == '__main__':
    app.run(debug=True)

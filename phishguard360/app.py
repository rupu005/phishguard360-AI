from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from functools import wraps
import datetime
import re
import io
import os

app = Flask(__name__)
app.secret_key = "phishguard_secret_key_2024"

# --------------------------------------------------
# 🗄️ DATABASE SETUP
# --------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phishguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --------------------------------------------------
# 📋 DATABASE MODELS
# --------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_user = db.Column(db.String(100), nullable=False)
    email_text = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.now)

# --------------------------------------------------
# 🔐 LOGIN REQUIRED DECORATOR
# --------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# 📝 SIGNUP ROUTE
# --------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            error = "Passwords match nahi kar rahe!"

        elif len(password) < 4:
            error = "Password kam se kam 4 characters ka hona chahiye!"

        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = "Yeh email already registered hai!"
            else:
                new_user = User(name=name, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                success = "Account ban gaya! Ab login karo."

    return render_template('signup.html', error=error, success=success)

# --------------------------------------------------
# 🔐 LOGIN ROUTE
# --------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user'] = user.email
            session['name'] = user.name
            return redirect('/')
        else:
            error = "Invalid email or password!"

    return render_template('login.html', error=error)

# --------------------------------------------------
# 🔐 LOGOUT ROUTE
# --------------------------------------------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('name', None)
    return redirect('/login')

# --------------------------------------------------
# ✅ SESSION CHECK
# --------------------------------------------------
@app.route('/check_session')
def check_session():
    if 'user' in session:
        return jsonify({'logged_in': True})
    return jsonify({'logged_in': False})

# --------------------------------------------------
# 🏠 HOME ROUTE
# --------------------------------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --------------------------------------------------
# 📊 DASHBOARD ROUTE
# --------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_email = session['user']

    history = History.query.filter_by(
        email_user=user_email
    ).order_by(History.date.desc()).all()

    total = len(history)
    phishing = sum(1 for h in history if 'Phishing' in h.result)
    safe = total - phishing

    stats = {
        'total': total,
        'phishing': phishing,
        'safe': safe
    }

    return render_template('dashboard.html',
                           stats=stats,
                           history=history[:10])

# --------------------------------------------------
# 👤 PROFILE ROUTE
# --------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(email=session['user']).first()
    history = History.query.filter_by(email_user=session['user']).all()

    total = len(history)
    phishing = sum(1 for h in history if 'Phishing' in h.result)
    safe = total - phishing

    stats = {'total': total, 'phishing': phishing, 'safe': safe}

    error = request.args.get('error')
    success = request.args.get('success')

    return render_template('profile.html',
                           user=user,
                           stats=stats,
                           error=error,
                           success=success)

# --------------------------------------------------
# ✏️ PROFILE UPDATE ROUTE
# --------------------------------------------------
@app.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    user = User.query.filter_by(email=session['user']).first()

    new_name = request.form['name']
    new_email = request.form['email']

    if new_email != user.email:
        existing = User.query.filter_by(email=new_email).first()
        if existing:
            return redirect('/profile?error=Yeh email already use ho rahi hai!')

    user.name = new_name
    user.email = new_email
    db.session.commit()

    session['name'] = new_name
    session['user'] = new_email

    return redirect('/profile?success=Profile update ho gaya!')

# --------------------------------------------------
# 🔒 CHANGE PASSWORD ROUTE
# --------------------------------------------------
@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    user = User.query.filter_by(email=session['user']).first()

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if user.password != current_password:
        return redirect('/profile?error=Current password galat hai!')

    if new_password != confirm_password:
        return redirect('/profile?error=New passwords match nahi kar rahe!')

    if len(new_password) < 4:
        return redirect('/profile?error=Password kam se kam 4 characters ka hona chahiye!')

    user.password = new_password
    db.session.commit()

    return redirect('/profile?success=Password change ho gaya!')
# --------------------------------------------------
# ⚙️ ADMIN REQUIRED DECORATOR
# --------------------------------------------------
ADMIN_EMAIL = "admin@gmail.com"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        if session['user'] != ADMIN_EMAIL:
            return redirect('/?error=Access denied!')
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# ⚙️ ADMIN PANEL ROUTE
# --------------------------------------------------
@app.route('/admin')
@admin_required
def admin():
    users = User.query.all()

    # Har user ke liye email count
    users_data = []
    for user in users:
        count = History.query.filter_by(
            email_user=user.email
        ).count()
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'email_count': count
        })

    all_history = History.query.order_by(
        History.date.desc()
    ).all()

    total_emails = History.query.count()
    total_phishing = sum(
        1 for h in all_history if 'Phishing' in h.result
    )

    stats = {
        'total_users': len(users),
        'total_emails': total_emails,
        'total_phishing': total_phishing
    }

    success = request.args.get('success')
    error = request.args.get('error')

    return render_template('admin.html',
                           users=users_data,
                           history=all_history[:20],
                           stats=stats,
                           success=success,
                           error=error)

# --------------------------------------------------
# 🗑️ ADMIN DELETE USER ROUTE
# --------------------------------------------------
@app.route('/admin/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return redirect('/admin?error=User nahi mila!')

    if user.email == ADMIN_EMAIL:
        return redirect('/admin?error=Admin ko delete nahi kar sakte!')

    # User ki history bhi delete karo
    History.query.filter_by(email_user=user.email).delete()
    db.session.delete(user)
    db.session.commit()

    return redirect('/admin?success=User delete ho gaya!')

# --------------------------------------------------
# 🔍 ANALYZE EMAIL ROUTE
# --------------------------------------------------
@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.json
    email_text = data.get('email', '')
    result = analyze_email(email_text)

    new_history = History(
        email_user=session['user'],
        email_text=email_text,
        result=result
    )
    db.session.add(new_history)
    db.session.commit()

    return jsonify({'result': result})

# --------------------------------------------------
# 🧠 ANALYZE EMAIL FUNCTION
# --------------------------------------------------
def analyze_email(text):
    score = 0
    reasons = []

    urgent_words = ['urgent', 'immediately', 'verify', 'suspend',
                    'click here', 'confirm', 'account', 'password',
                    'bank', 'win', 'prize', 'congratulations']
    for word in urgent_words:
        if word.lower() in text.lower():
            score += 1
            reasons.append(f'Suspicious word found: "{word}"')

    if re.search(r'http[s]?://', text):
        score += 1
        reasons.append("Contains URL link")

    if re.search(r'http[s]?://\d+\.\d+\.\d+\.\d+', text):
        score += 2
        reasons.append("Link contains IP address (very suspicious!)")

    if re.search(r'http[s]?://[^\s]*@', text):
        score += 2
        reasons.append("Link contains @ symbol (phishing trick!)")

    if re.search(r'@(gmail|yahoo|hotmail|outlook)\.(com|net)', text):
        score += 1
        reasons.append("Suspicious email domain found")

    if score >= 3:
        return "⚠️ Phishing Detected!\n\nReasons:\n- " + "\n- ".join(reasons)
    else:
        return "✅ Email Seems Safe.\n\nChecks Passed:\n- " + "\n- ".join(reasons) if reasons else "✅ Email Seems Safe.\n\nNo suspicious content found."

# --------------------------------------------------
# 📄 PDF EXPORT ROUTE
# --------------------------------------------------
@app.route('/export', methods=['POST'])
@login_required
def export_pdf():
    data = request.json
    email_text = data.get('email', '')
    result = data.get('result', '')

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "PhishGuard 360 - Phishing Email Report", ln=True, align='C')

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Analyzed by: {session.get('name', 'Unknown')}", ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Analysis Result:", ln=True)
    pdf.set_font("Arial", "", 12)
    for line in result.split('\n'):
        pdf.cell(0, 8, line, ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Email Content Analyzed:", ln=True)
    pdf.set_font("Arial", "", 11)
    for line in email_text.split('\n'):
        pdf.multi_cell(0, 8, line)

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return send_file(
        io.BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='phishguard_report.pdf'
    )

# --------------------------------------------------
# 🚀 RUN APP
# --------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email='admin@gmail.com').first():
            admin = User(name='Admin', email='admin@gmail.com', password='1234')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin account created!")

    app.run(debug=True)
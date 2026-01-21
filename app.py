from flask import Flask, render_template_string, render_template, request, flash, redirect, url_for, session, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, ValidationError
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tajnykey')
app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///formdata.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False  # odhlášení po zavření prohlížeče (session cookie)
db = SQLAlchemy(app)

# Preload Jinja macros and expose as global `ui` for templates
with app.app_context():
    try:
        ui_module = app.jinja_env.get_template('macros/macros.html').make_module({})
        app.jinja_env.globals['ui'] = ui_module
    except Exception:
        # If macros are missing during early import, continue; templates may import directly
        pass

class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class MyForm(FlaskForm):
    name = StringField('Jméno', validators=[DataRequired(message="Jméno je povinné")])
    email = StringField('Email', validators=[DataRequired(message="Email je povinný"), Email(message="Neplatný email")])
    gender = SelectField('Pohlaví', choices=[('muž', 'Muž'), ('žena', 'Žena')], validators=[DataRequired(message="Pohlaví je povinné")])
    message = TextAreaField('Zpráva', validators=[DataRequired(message="Zpráva je povinná")])
    submit = SubmitField('Odeslat')

class LoginForm(FlaskForm):
    username = StringField('Uživatelské jméno', validators=[DataRequired(message="Uživatelské jméno je povinné")])
    password = PasswordField('Heslo', validators=[DataRequired(message="Heslo je povinné")])
    submit = SubmitField('Přihlásit')

class RegisterForm(FlaskForm):
    username = StringField('Uživatelské jméno', validators=[DataRequired(message="Uživatelské jméno je povinné")])
    email = StringField('Email', validators=[DataRequired(message="Email je povinný"), Email(message="Neplatný email")])
    gender = SelectField('Pohlaví', choices=[('muž', 'Muž'), ('žena', 'Žena')], validators=[DataRequired(message="Pohlaví je povinné")])
    password = PasswordField('Heslo', validators=[DataRequired(message="Heslo je povinné")])
    submit = SubmitField('Registrovat')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Uživatelské jméno je již použito')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email je již použit')

class MessageForm(FlaskForm):
    message = TextAreaField('Zpráva', validators=[DataRequired(message="Zpráva je povinná")])
    submit = SubmitField('Odeslat')

class SearchForm(FlaskForm):
    q = StringField('Hledat', validators=[DataRequired(message="Zadejte uživatelské jméno")])
    submit = SubmitField('Hledat')

TEMPLATE = '''
<!doctype html>
<html lang="cs">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Validovaný formulář</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {
                min-height: 100vh;
                background: linear-gradient(135deg, #eef2f7 0%, #f8fbff 100%);
            }
            .navbar { backdrop-filter: saturate(180%) blur(10px); background: rgba(255,255,255,.8); }
            .card { border: none; border-radius: 16px; box-shadow: 0 12px 30px rgba(0,0,0,.08); }
            .form-label { font-weight: 600; }
            .brand { font-weight: 700; }
            .char-counter { font-size: .85rem; color: #6c757d; }
        </style>
    </head>
    <body>
                <nav class="navbar navbar-light sticky-top border-bottom">
                        <div class="container d-flex align-items-center justify-content-between">
                                <a href="{{ url_for('index') }}" class="navbar-brand mb-0 h1 brand text-decoration-none"><i class="bi bi-chat-right-text me-2"></i>FORM</a>
                                <div class="d-flex">
                                        {% if session.get('admin') %}
                                            <a href="{{ url_for('admin') }}" class="btn btn-outline-primary btn-sm me-2"><i class="bi bi-shield-lock me-1"></i>Admin</a>
                                            <a href="{{ url_for('logout') }}" class="btn btn-outline-secondary btn-sm"><i class="bi bi-box-arrow-right me-1"></i>Odhlásit</a>
                                        {% else %}
                                            <a href="{{ url_for('login_admin') }}" class="btn btn-primary btn-sm"><i class="bi bi-box-arrow-in-right me-1"></i>Přihlásit</a>
                                        {% endif %}
                                </div>
                        </div>
                </nav>

        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-12 col-md-8 col-lg-6">
                    <div class="card">
                        <div class="card-body p-4">
                            <h1 class="h4 mb-4 text-center">Zpráva</h1>

                            <div class="position-relative" aria-live="polite" aria-atomic="true">
                                <div class="toast-container position-static">
                                    {% with messages = get_flashed_messages() %}
                                        {% if messages %}
                                            <div class="toast show align-items-center text-bg-success border-0 mb-3" role="status">
                                                <div class="d-flex">
                                                    <div class="toast-body">
                                                        <i class="bi bi-check-circle me-2"></i>{{ messages[0] }}
                                                    </div>
                                                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                                                </div>
                                            </div>
                                        {% endif %}
                                    {% endwith %}
                                </div>
                            </div>

                            <form method="POST" novalidate id="contactForm">
                                {{ form.hidden_tag() }}

                                <div class="mb-3">
                                    <label class="form-label">{{ form.name.label.text }}</label>
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="bi bi-person"></i></span>
                                        {{ form.name(class_='form-control' + (' is-invalid' if form.name.errors else ''), placeholder='Vaše jméno') }}
                                        {% if form.name.errors %}
                                            <div class="invalid-feedback">
                                                {{ form.name.errors[0] }}
                                            </div>
                                        {% endif %}
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">{{ form.email.label.text }}</label>
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                                        {{ form.email(class_='form-control' + (' is-invalid' if form.email.errors else ''), placeholder='vas@email.cz') }}
                                        {% if form.email.errors %}
                                            <div class="invalid-feedback">
                                                {{ form.email.errors[0] }}
                                            </div>
                                        {% endif %}
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">{{ form.gender.label.text }}</label>
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="bi bi-gender-ambiguous"></i></span>
                                        {{ form.gender(class_='form-select' + (' is-invalid' if form.gender.errors else '')) }}
                                        {% if form.gender.errors %}
                                            <div class="invalid-feedback">
                                                {{ form.gender.errors[0] }}
                                            </div>
                                        {% endif %}
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">{{ form.message.label.text }}</label>
                                    {{ form.message(class_='form-control' + (' is-invalid' if form.message.errors else ''), rows=5, placeholder='Vaše zpráva...') }}
                                    <div class="d-flex justify-content-end mt-1">
                                        <small class="char-counter" id="charCounter">0 znaků</small>
                                    </div>
                                    {% if form.message.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.message.errors[0] }}
                                        </div>
                                    {% endif %}
                                </div>

                                <div class="d-grid">
                                    <button class="btn btn-primary btn-lg" id="submitBtn" type="submit">
                                        <span class="spinner-border spinner-border-sm me-2 d-none" role="status" aria-hidden="true" id="btnSpinner"></span>
                                        {{ form.submit.label.text }}
                                    </button>
                                </div>
                            </form>

                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Počítadlo znaků pro textarea
            const ta = document.getElementById('message');
            const counter = document.getElementById('charCounter');
            if (ta && counter) {
                const update = () => {
                    const len = ta.value.length;
                    counter.textContent = `${len} znaků`;
                };
                ta.addEventListener('input', update);
                update();
            }

            // Disable tlačítka při odesílání + spinner
            const form = document.getElementById('contactForm');
            const btn = document.getElementById('submitBtn');
            const spinner = document.getElementById('btnSpinner');
            if (form && btn && spinner) {
                form.addEventListener('submit', () => {
                    btn.disabled = true;
                    spinner.classList.remove('d-none');
                });
            }
        </script>
    </body>
    </html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('user'):
        form = MessageForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=session['user']).first()
            if not user:
                flash('Uživatel nenalezen', 'danger')
                return redirect(url_for('logout'))
            new_entry = FormData(
                name=user.username,
                email=user.email,
                gender=user.gender,
                message=form.message.data
            )
            db.session.add(new_entry)
            db.session.commit()
            flash('Zpráva úspěšně odeslána', 'success')
            return redirect(url_for('index'))
        return render_template('sites/index.html', form=form)
    else:
        form = MyForm()
        if form.validate_on_submit():
            new_entry = FormData(
                name=form.name.data,
                email=form.email.data,
                gender=form.gender.data,
                message=form.message.data
            )
            db.session.add(new_entry)
            db.session.commit()
            flash('Formulář úspěšně odeslán', 'success')
            return redirect(url_for('index'))
        return render_template('sites/index.html', form=form)

# Login template moved to templates/auth/login_admin.html

# Admin list template
ADMIN_TEMPLATE = '''
<!doctype html>
<html lang="cs">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Admin - zprávy</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
            <nav class="navbar navbar-light bg-light border-bottom">
                <div class="container d-flex justify-content-between align-items-center">
                    <div>
                        <a class="navbar-brand text-decoration-none" href="{{ url_for('index') }}">← Formulář</a>
                    </div>
                    <div>
                        <a class="btn btn-outline-secondary btn-sm" href="{{ url_for('logout') }}">Odhlásit</a>
                    </div>
                </div>
            </nav>

        <div class="container py-4">
            <h1 class="h4 mb-3">Odeslané zprávy</h1>
            {% if items %}
                <div class="table-responsive">
                    <table class="table table-striped align-middle">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Jméno</th>
                                <th>Email</th>
                                <th>Pohlaví</th>
                                <th>Zpráva</th>
                                <th>Akce</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for it in items %}
                                <tr>
                                    <td>{{ loop.index }}</td>
                                    <td>{{ it.name }}</td>
                                    <td>{{ it.email }}</td>
                                    <td>{{ it.gender }}</td>
                                    <td class="text-truncate" style="max-width: 360px;">{{ it.message }}</td>
                                    <td>
                                        <form method="POST" action="{{ url_for('delete_entry', entry_id=it.id) }}" onsubmit="return confirm('Smazat záznam #' + {{ it.id }} + '?');">
                                            <button type="submit" class="btn btn-sm btn-danger">Smazat</button>
                                        </form>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="alert alert-info">Zatím žádné záznamy.</div>
            {% endif %}
        </div>
    </body>
    </html>
'''

def require_admin():
    if not session.get('admin'):
        return False
    return True

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == 'admin' and password == 'admin':
            session['admin'] = True
            # Session cookie zůstane jen do zavření prohlížeče (SESSION_PERMANENT=False)
            return redirect(url_for('admin'))
        flash('Neplatné přihlašovací údaje', 'danger')
    return render_template('auth/login_admin.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not require_admin():
        return redirect(url_for('login_admin'))
    items = FormData.query.order_by(FormData.id.asc()).all()
    return render_template('sites/admin.html', items=items)

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    if not require_admin():
        return redirect(url_for('login_admin'))
    item = FormData.query.get_or_404(entry_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/messages', methods=['GET'])
def messages():
    if not session.get('user'):
        return redirect(url_for('login'))
    form = SearchForm(request.args)
    me = User.query.filter_by(username=session['user']).first()
    results = []
    # Build conversations list (users you've messaged with or who messaged you)
    contacts = []
    if me:
        msgs = Message.query.filter(or_(Message.sender_id == me.id, Message.receiver_id == me.id)).order_by(Message.created_at.desc()).all()
        latest_msg_map = {}
        for m in msgs:
            other_id = m.receiver_id if m.sender_id == me.id else m.sender_id
            if other_id not in latest_msg_map:
                latest_msg_map[other_id] = m
        if latest_msg_map:
            users = User.query.filter(User.id.in_(list(latest_msg_map.keys()))).all()
            contacts = sorted(
                (
                    {"user": u, "preview": latest_msg_map[u.id].content, "time": latest_msg_map[u.id].created_at, "from_me": latest_msg_map[u.id].sender_id == me.id}
                    for u in users
                ),
                key=lambda c: c["time"],
                reverse=True,
            )
    if 'q' in request.args and form.validate():
        q = form.q.data.strip()
        if q:
            results = User.query.filter(User.username.like(f"%{q}%"), User.username != session['user']).order_by(User.username.asc()).all()
    return render_template('sites/messages.html', search=form, results=results, contacts=contacts, thread_user=None, messages=[], me_id=(me.id if me else None))

@app.route('/messages/<username>', methods=['GET', 'POST'])
def messages_thread(username):
    if not session.get('user'):
        return redirect(url_for('login'))
    me = User.query.filter_by(username=session['user']).first()
    other = User.query.filter_by(username=username).first()
    if not other or not me or other.username == me.username:
        flash('Uživatel nenalezen', 'danger')
        return redirect(url_for('messages'))

    send_form = MessageForm()
    if send_form.validate_on_submit():
        msg = Message(sender_id=me.id, receiver_id=other.id, content=send_form.message.data.strip())
        if msg.content:
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('messages_thread', username=other.username))

    # Load conversation (both directions)
    msgs = Message.query.filter(
        or_(
            and_(Message.sender_id == me.id, Message.receiver_id == other.id),
            and_(Message.sender_id == other.id, Message.receiver_id == me.id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Search form on the left (optional query) and conversations list
    search_form = SearchForm(request.args)
    results = []
    if 'q' in request.args and search_form.validate():
        q = search_form.q.data.strip()
        if q:
            results = User.query.filter(User.username.like(f"%{q}%"), User.username != session['user']).order_by(User.username.asc()).all()
    contacts = []
    msgs_all = Message.query.filter(or_(Message.sender_id == me.id, Message.receiver_id == me.id)).order_by(Message.created_at.desc()).all()
    latest_msg_map = {}
    for m in msgs_all:
        other_id = m.receiver_id if m.sender_id == me.id else m.sender_id
        if other_id not in latest_msg_map:
            latest_msg_map[other_id] = m
    if latest_msg_map:
        users = User.query.filter(User.id.in_(list(latest_msg_map.keys()))).all()
        contacts = sorted(
            (
                {"user": u, "preview": latest_msg_map[u.id].content, "time": latest_msg_map[u.id].created_at, "from_me": latest_msg_map[u.id].sender_id == me.id}
                for u in users
            ),
            key=lambda c: c["time"],
            reverse=True,
        )

    return render_template('sites/messages.html', search=search_form, results=results, contacts=contacts, thread_user=other, messages=msgs, send_form=send_form, me_id=me.id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['user'] = user.username
            flash('Přihlášení úspěšné', 'success')
            return redirect(url_for('index'))
        flash('Neplatné přihlašovací údaje', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            gender=form.gender.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registrace úspěšná, přihlaste se', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

with app.app_context():
    # Auto-migrace: doplnění chybějících sloupců u stávající tabulky
    db.create_all()
    try:
        res = db.session.execute(text("PRAGMA table_info(form_data)"))
        cols = {row[1] for row in res}  # row[1] = column name
        if 'gender' not in cols:
            db.session.execute(text("ALTER TABLE form_data ADD COLUMN gender VARCHAR(10) NOT NULL DEFAULT 'muž'"))
        if 'message' not in cols:
            db.session.execute(text("ALTER TABLE form_data ADD COLUMN message TEXT NOT NULL DEFAULT ''"))
        # Ensure User table has required columns if created previously without them
        res_user = db.session.execute(text("PRAGMA table_info(user)"))
        user_cols = {row[1] for row in res_user}
        if 'email' not in user_cols:
            db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(128) NOT NULL DEFAULT ''"))
        if 'gender' not in user_cols:
            db.session.execute(text("ALTER TABLE user ADD COLUMN gender VARCHAR(10) NOT NULL DEFAULT 'muž'"))
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

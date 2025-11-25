from flask import Flask, render_template_string, request, flash, redirect, url_for, session, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tajnykey')
app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False  # odhlášení po zavření prohlížeče (session cookie)
db = SQLAlchemy(app)

class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)

class MyForm(FlaskForm):
    name = StringField('Jméno', validators=[DataRequired(message="Jméno je povinné")])
    email = StringField('Email', validators=[DataRequired(message="Email je povinný"), Email(message="Neplatný email")])
    gender = SelectField('Pohlaví', choices=[('muž', 'Muž'), ('žena', 'Žena')], validators=[DataRequired(message="Pohlaví je povinné")])
    message = TextAreaField('Zpráva', validators=[DataRequired(message="Zpráva je povinná")])
    submit = SubmitField('Odeslat')

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
                                            <a href="{{ url_for('login') }}" class="btn btn-primary btn-sm"><i class="bi bi-box-arrow-in-right me-1"></i>Přihlásit</a>
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
    form = MyForm()
    if form.validate_on_submit():
        # Uložení do databáze
        new_entry = FormData(
            name=form.name.data,
            email=form.email.data,
            gender=form.gender.data,
            message=form.message.data
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Formulář úspěšně odeslán')
        # PRG pattern: po úspěchu přesměrovat na GET, aby se formulář vyprázdnil
        return redirect(url_for('index'))
    return render_template_string(TEMPLATE, form=form)

# Login template
LOGIN_TEMPLATE = '''
<!doctype html>
<html lang="cs">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Přihlášení</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="card shadow-sm">
                        <div class="card-body">
                            <h1 class="h4 mb-4 text-center">Přihlášení administrátora</h1>
                            {% with messages = get_flashed_messages() %}
                                {% if messages %}
                                    <div class="alert alert-danger">{{ messages[0] }}</div>
                                {% endif %}
                            {% endwith %}
                              <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Uživatelské jméno</label>
                                  <input type="text" class="form-control" name="username" placeholder="Uživatelské jméno" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Heslo</label>
                                  <input type="password" class="form-control" name="password" placeholder="Heslo" required>
                                </div>
                                <div class="d-grid">
                                    <button class="btn btn-primary" type="submit">Přihlásit</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
'''

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

@app.route('/login', methods=['GET', 'POST'])
def login():
        if request.method == 'POST':
                username = request.form.get('username', '')
                password = request.form.get('password', '')
                if username == 'admin' and password == 'admin':
                        session['admin'] = True
                        # Session cookie zůstane jen do zavření prohlížeče (SESSION_PERMANENT=False)
                        return redirect(url_for('admin'))
                flash('Neplatné přihlašovací údaje')
        return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
        session.pop('admin', None)
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not require_admin():
        return redirect(url_for('login'))
    items = FormData.query.order_by(FormData.id.asc()).all()
    return render_template_string(ADMIN_TEMPLATE, items=items)

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
        if not require_admin():
                return redirect(url_for('login'))
        item = FormData.query.get_or_404(entry_id)
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('admin'))

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
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

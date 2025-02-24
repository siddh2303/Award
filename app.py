
# Existing imports and configurations

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Category, Nomination
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, SubmitField

from wtforms.validators import DataRequired, Email, Length
from datetime import datetime

from functools import wraps


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\164817\\Downloads\\Project Work\\Award\\awardDB.db'
app.config['SECRET_KEY'] = '09g8g6fg54hb3j4v34'
db.init_app(app)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    gid = StringField('GID', validators=[DataRequired(), Length(min=6, max=6, message="GID must be exactly 6 digits")])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    type = StringField('Type of Category', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Create Category')

class NominationForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    nominee_name = StringField('Name of Nominee', validators=[DataRequired()])
    nominee_global_id = StringField('Global ID of Nominee', validators=[DataRequired()])
    nominee_email = StringField('Email of Nominee', validators=[DataRequired(), Email()])
    nominated_by_name = StringField('Nominated by Name', validators=[DataRequired()])
    nominated_by_global_id = StringField('Nominated by Global ID', validators=[DataRequired()])
    nominated_by_email = StringField('Nominated by Email', validators=[DataRequired(), Email()])
    comments = TextAreaField('Citations (if any)')
    status = SelectField('Status', choices=[('In-progress', 'In-progress'), 
                                            ('Submitted', 'Submitted'),
                                            ('Rejected', 'Rejected'), 
                                            ('Send-back', 'Send-back')])
    submit = SubmitField('Submit Nomination')
    
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request

def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        role = request.form['role']  # 'User' or 'Admin' roles
        gid = request.form['gid']

        if role not in ['User', 'Admin']:
            flash('Invalid role specified', 'danger')
            return redirect(url_for('register'))
        
        if not gid.isdigit() or len(gid) != 6:
            flash('GID must be a 6-digit number', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, password=password, email=email, role=role,gid=gid)
        db.session.add(user)
        db.session.commit()
        flash(f'{role} registered successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['gid']=user.gid
            session['role'] = user.role
            session['username'] = username
            session['email']=user.email
            session['logged_in'] = True

            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'User':
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('logged_in', None)
    return redirect(url_for('login'))



@app.route('/edit_nomination/<int:nomination_id>', methods=['GET', 'POST'])
def edit_nomination(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    if request.method == 'POST':
        nomination.nominee_name = request.form['nominee_name']
        nomination.nominee_global_id = request.form['nominee_global_id']
        nomination.nominee_email = request.form['nominee_email']
        nomination.category_id = request.form['category_id']
        nomination.comments = request.form['comments']
        nomination.status='Submitted'
        db.session.commit()
        flash('Nomination updated successfully', 'success')
        return redirect(url_for('user_dashboard'))
    categories = Category.query.all()
    return render_template('edit_nomination.html', nomination=nomination, categories=categories)


@app.route('/admin')
@login_required

def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    users=User.query.all()
    categories = Category.query.all()
    return render_template('admin_dashboard.html', categories=categories,users=users)

@app.route('/user')
@login_required

def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'User':
        return redirect(url_for('login'))
    categories = Category.query.all()
    user = User.query.filter_by(gid=session['gid']).first()
    print(user)
    nominations = Nomination.query.filter_by(nominated_by_email=session['email']).all()
    print(nominations)
    return render_template('user_dashboard.html', categories=categories, nominations=nominations, user=user)
@app.route('/update_access/<int:user_id>', methods=['POST'])
def update_access(user_id):
    user = User.query.get_or_404(user_id)
    new_access_level = request.form['access_level']

    valid_access_levels = ['full_access', 'view_only', 'reviewer']

    if new_access_level not in valid_access_levels:
        flash('Invalid access level selected.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user.access_level = new_access_level

    db.session.commit()
    
    flash(f'Access level for user {user.username} updated to {new_access_level}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/category', methods=['GET', 'POST'])
@login_required

def category():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m')
        type = request.form['type']
        new_category = Category(name=name, start_date=start_date, end_date=end_date, type=type)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('category.html')

@app.route('/nominations/new', methods=['GET', 'POST'])
@login_required

def new_nomination():
    form = NominationForm()
    form.category_id.choices = [(category.id, category.name) for category in Category.query.all()]
    form.nominated_by_name.data = session['username']
    form.nominated_by_global_id.data = session['gid']
    form.nominated_by_email.data = session['email']
    if form.validate_on_submit():
        nomination = Nomination(
            category_id=form.category_id.data, 
            nominee_name=form.nominee_name.data, 
            nominee_global_id=form.nominee_global_id.data, 
            nominee_email=form.nominee_email.data, 
            nominated_by_name=form.nominated_by_name.data, 
            nominated_by_global_id=form.nominated_by_global_id.data, 
            nominated_by_email=form.nominated_by_email.data, 
            comments=form.comments.data, 
            status='Submitted'

        )
        db.session.add(nomination)
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    return render_template('new_nomination.html', form=form)

@app.route('/update_nomination/<int:nomination_id>', methods=['POST'])
@login_required

def update_nomination_status(nomination_id):
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    
    nomination = Nomination.query.get_or_404(nomination_id)
    action = request.form.get('action')

    if action == 'approve':
        nomination.status = 'Approved'
        flash('Nomination approved', 'success')
    elif action == 'reject':
        nomination.status = 'Rejected'
        flash('Nomination rejected', 'danger')
    elif action == 'send_back':
        nomination.status = 'Send-Back'
        flash('Nomination sent back for changes', 'warning')

    db.session.commit()
    return redirect(url_for('view_nominees'))

@app.route('/view_nominees')
@login_required

def view_nominees():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    nominees = Nomination.query.all()
    return render_template('view_nominees.html', nominees=nominees)

if __name__ == '__main__':
    app.run(debug=True)

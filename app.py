
# Existing imports and configurations

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Category, Nomination, QuarterlyAward, AnnuallyAward
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
    if session.get('access_level') != 'full_access':
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        role = 'User'
        gid = request.form['gid']
        access_level = request.form['access_level']
        
        if not gid.isdigit() or len(gid) != 6:
            flash('GID must be a 6-digit number', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, password=password, email=email, role=role,gid=gid,access_level=access_level)
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
            session['access_level']=user.access_level
            session['username'] = username
            session['email']=user.email
            session['logged_in'] = True
            if session['access_level'] == 'full_access':
                return redirect(url_for('admin_dashboard'))
            elif session['access_level'] != 'full_access':
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

@app.route('/view_categories')
@login_required

def view_categories():
    categories = Category.query.filter_by(status=1).all()
    return render_template('view_categories.html', categories=categories)

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
    if 'user_id' not in session or session['access_level'] != 'full_access':
        return redirect(url_for('login'))
    users=User.query.all()
    categories = Category.query.all()
    return render_template('admin_dashboard.html', categories=categories,users=users)

@app.route('/nomination_dashboard')
def nomination_dashboard():
    return render_template('nomination_dashboard.html')

@app.route('/category_dashboard')
def category_dashboard():
    return render_template('category_dashboard.html')


@app.route('/user')
@login_required

def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'User':
        return redirect(url_for('login'))
    categories = Category.query.all()
    user = User.query.filter_by(gid=session['gid']).first()
    nominations = Nomination.query.filter_by(nominated_by_email=session['email']).all()
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
    if 'user_id' not in session or session.get('access_level') != 'full_access':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m')
        status=1
        new_category = Category(name=name, start_date=start_date, end_date=end_date, status=status)
        db.session.add(new_category)
        db.session.commit()
        diff_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


        if diff_months == 3:
            awards = [
                "Core Value - Customer First",
                "Core Value - Disciplined Execution",
                "Core Value - Embrace Impossible Challenges",
                "Core Value - Continuous Learning",
                "Core Value - Serving Society",
                "Best Project"
            ]
            for award_name in awards:
                award = QuarterlyAward(name=award_name, category_id=category.id)
                db.session.add(award)

        elif diff_months == 12:
            awards = [
                "Exemplary Leadership",
                "Business Champion",
                "eI Rocks",
                "Best Function/Non-Engineering Team member",
                "Best Team",
                "Power Trainees",
                "Jack of the box Award",
                "Hercules Award",
                "Dronacharya Award",
                "CSR Award"
            ]
            for award_name in awards:
                award = AnnuallyAward(name=award_name, category_id=category.id)
                db.session.add(award)
        flash('Category added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('category.html')


@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['name']
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']

        try:
            category.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            category.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            diff_months = (category.end_date.year - category.start_date.year) * 12 + category.end_date.month+1 - category.start_date.month
            if diff_months == 3:
                awards = [
                    "Core Value - Customer First",
                    "Core Value - Disciplined Execution",
                    "Core Value - Embrace Impossible Challenges",
                    "Core Value - Continuous Learning",
                    "Core Value - Serving Society",
                    "Best Project"
                ]
                for award_name in awards:
                    award = QuarterlyAward(name=award_name, category_id=category.id)
                    db.session.add(award)

            elif diff_months == 12:
                awards = [
                    "Exemplary Leadership",
                    "Business Champion",
                    "eI Rocks",
                    "Best Function/Non-Engineering Team member",
                    "Best Team",
                    "Power Trainees",
                    "Jack of the box Award",
                    "Hercules Award",
                    "Dronacharya Award",
                    "CSR Award"
                ]
                for award_name in awards:
                    award = AnnuallyAward(name=award_name, category_id=category.id)
                    db.session.add(award)
            db.session.commit()
            flash('Category updated successfully', 'success')
            return redirect(url_for('view_categories'))
        except ValueError as e:
            flash(f'Invalid date format: {e}', 'error')
            return render_template('edit_category.html', category=category)
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')

    return render_template('edit_category.html', category=category)

@app.route('/category/delete/<int:category_id>', methods=['GET','POST'])
def delete_category(category_id):

    category = Category.query.get_or_404(category_id)
    try:
        category.status = 0

        db.session.commit()
        flash('Category marked as deleted successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error marking category as deleted: {str(e)}', 'error')

    return redirect(url_for('view_categories'))


@app.route('/nominations/new', methods=['GET', 'POST'])
@login_required

def new_nomination():
    if 'user_id' not in session or session.get('access_level') != 'full_access':
        return redirect(url_for('login'))
    form = NominationForm()
    form.category_id.choices = [(category.id, f"{category.name} ({category.start_date.strftime('%d-%B-%Y')} - {category.end_date.strftime('%d-%B-%Y')})") for category in Category.query.filter_by(status=1).all()]
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
            status='Submitted',
            award_name= request.form.get('award')

        )
        db.session.add(nomination)
        category = Category.query.get_or_404(form.category_id.data)
        if category:
            category.start_date = datetime.strptime(str(category.start_date), "%Y-%m-%d %H:%M:%S").date()
            category.end_date = datetime.strptime(str(category.end_date), "%Y-%m-%d %H:%M:%S").date()
            diff_months = (category.end_date.year - category.start_date.year) * 12 + category.end_date.month+1 - category.start_date.month
            if diff_months == 3:
                award = QuarterlyAward.query.filter_by(name=request.form.get('award'), category_id=form.category_id.data).first()
            elif diff_months == 12:
                award = AnnuallyAward.query.filter_by(name=request.form.get('award'), category_id=form.category_id.data).first()

            if award:
                award.is_available = False

                db.session.add(award)
        db.session.commit()
        return redirect(url_for('nomination_dashboard'))
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
    if 'user_id' not in session or session.get('access_level') != 'full_access':
        return redirect(url_for('login'))
    nominees = Nomination.query.all()
    user = User.query.filter_by(gid=session['gid']).first()
    return render_template('view_nominees.html', nominees=nominees, user= user)

@app.route('/get_awards/<int:category_id>', methods=['GET'])
def get_awards(category_id):
    try:
        # Query both QuarterlyAward and AnnuallyAward where is_available is True

        quarterly_awards = QuarterlyAward.query.filter_by(category_id=category_id, is_available=True).all()
        annually_awards = AnnuallyAward.query.filter_by(category_id=category_id, is_available=True).all()
        
        # Combine the results and prepare the response

        awards = [
            {'id': award.id, 'name': award.name} 
            for award in quarterly_awards + annually_awards

        ]
        
        return jsonify(awards)
    except Exception as e:
        # Handle exceptions and return an error message

        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)

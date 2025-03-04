from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Category, Nomination, QuarterlyAward, AnnuallyAward, TeamMember, UserRole, Role
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, SubmitField

from wtforms.validators import DataRequired, Email, Length
from datetime import datetime, timedelta
import sqlite3
from functools import wraps


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\164817\\Downloads\\Project Work\\Award 2\\awardDB.db'
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
    status = StringField('Status',default='In-progress' , validators=[DataRequired()])
    submit = SubmitField('Submit Nomination')
    team_member_id = SelectField('Team Member', coerce=int, validators=[DataRequired()])
    
   
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def not_full_access(f):
    @wraps(f)
    def dec_func(*args,**kwargs):
        if 'full_access' not in session['access_level'] :
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec_func

def check_assign_access(f):
    @wraps(f)
    def dec_function(*args,**kwargs):
        if 'assign_access' in session['access_level'] or 'full_access' in session['access_level']:
            pass
        else:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec_function

def check_manage_user(f):
    @wraps(f)
    def deco_function(*args,**kwargs):
        if 'manage_user' in session['access_level'] or 'full_access' in session['access_level']:
            pass
        else:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return deco_function

def approver_access(f):
    @wraps(f)
    def deco_func(*args,**kwargs):
        if 'reviewer' in session['access_level'] or 'full_access' in session['access_level']:
            pass
        else:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return deco_func


@app.before_request
def create_tables():
    db.create_all()
    categories = Category.query.all()
    for category in categories:
        category.update_status()
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
@check_manage_user
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        role = 'User'
        gid = request.form['gid']
        
        if not gid.isdigit() or len(gid) != 6:
            flash('GID must be a 6-digit number', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, password=password, email=email, role=role,gid=gid)
        db.session.add(user)
        db.session.commit()
        new_user=User.query.filter_by(username=username).first()
        new_user_role =UserRole(user_id=new_user.id,role_id=3,name='edit_only')
        db.session.add(new_user_role)
        db.session.commit()
        flash(f'{role} registered successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gid = request.form['gid']
        password = request.form['password']
        if gid == 'admin':
            user = User.query.filter_by(username=gid).first()
        else:
            user = User.query.filter_by(gid=gid).first()
       
        if user and check_password_hash(user.password, password):
            role_names = db.session.query(UserRole.name).filter(UserRole.user_id == user.id).all()
            role_names_list = [role.name for role in role_names]
            session['user_id'] = user.id
            session['gid']=user.gid
            session['role'] = user.role
            session['access_level']=role_names_list
            session['username'] = user.username
            session['email']=user.email
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('logged_in', None)
    session.pop('gid',None)
    session.pop('access_level',None)
    session.pop('username',None)
    session.pop('email',None)
    return redirect(url_for('login'))

@app.route('/nomination_duration')
@login_required
def nomination_duration():
    if 'full_access' in session['access_level']:
        categories = Category.query.all()
    else:
        categories = Category.query.filter_by(status=1).all()
    
    return render_template('nomination_duration.html', categories=categories,timedelta=timedelta)





@app.route('/edit_nomination/<int:nomination_id>', methods=['GET', 'POST'])
@login_required
def edit_nomination(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    if request.method == 'POST':
        new_award_name = request.form['award_id']
        team_member_name = request.form['team_member_name']

        # Update nomination details without altering award availability

        nomination.nominee_name = request.form['nominee_name']
        nomination.nominee_global_id = request.form['nominee_global_id']
        nomination.nominee_email = request.form['nominee_email']
        nomination.comments = request.form['comments']
        nomination.award_name = new_award_name

        nomination.status = 'Submitted'
        nomination.team_member_name = team_member_name

        db.session.commit()
        flash('Nomination updated successfully', 'success')
        return redirect(url_for('view_nominees'))

    categories = Category.query.all()
    team_members = TeamMember.query.all()

    # Fetch all awards related to the nomination's category_id

    quarterly_awards = QuarterlyAward.query.filter_by(category_id=nomination.category_id).all()
    annually_awards = AnnuallyAward.query.filter_by(category_id=nomination.category_id).all()
    awards = quarterly_awards + annually_awards


    return render_template('edit_nomination.html', nomination=nomination, categories=categories, team_members=team_members, awards=awards)


@app.route('/user_access')
@check_assign_access
@login_required

def user_access():
    users= User.query.all()
    return render_template('user_access.html', users=users)

@app.route('/dashboard')
@login_required
def admin_dashboard():
    users=User.query.all()
    categories = Category.query.all()
    return render_template('admin_dashboard.html', categories=categories,users=users)




@app.route('/update_access', methods=['POST'])


def update_access():
    user_id = request.form.get('user_id')
    full_access = 'full_access' in request.form

    nomination = 'nomination' in request.form

    reviewer = 'reviewer' in request.form

    manage_user = 'manage_user' in request.form

    assign_access = 'assign_access' in request.form


    # Handle full_access

    if full_access:
        role_name = 'full_access'
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
            db.session.commit()
        user_role = UserRole.query.filter_by(user_id=user_id, role_id=role.id).first()
        if user_role:
            user_role.role_id = role.id

            user_role.name = role_name

        else:
            user_role = UserRole(user_id=user_id, role_id=role.id, name=role_name)
            db.session.add(user_role)
        UserRole.query.filter(UserRole.user_id == user_id, UserRole.name != role_name).delete(synchronize_session='fetch')
        db.session.commit()
    else:
        nomination_management_roles = []
        if nomination or reviewer:
            if reviewer:
                nomination_management_roles.append('reviewer')
            if nomination:
                nomination_management_roles.append('edit_only')

            for role_name in nomination_management_roles:
                existing_role = UserRole.query.filter_by(user_id=user_id, name=role_name).first()
                if existing_role is None:
                    role = Role.query.filter_by(name=role_name).first()
                    if not role:
                        role = Role(name=role_name)
                        db.session.add(role)
                        db.session.commit()
                    UserRole.query.filter(UserRole.user_id == user_id, UserRole.name.in_(['full_access', 'edit_only', 'reviewer'])).delete(synchronize_session='fetch')        
                    user_role = UserRole(user_id=user_id, role_id=role.id, name=role_name)
                    db.session.add(user_role)
                else:
                    pass

            db.session.commit()

        user_management_roles = []
        if manage_user:
            user_management_roles.append('manage_user')
        if assign_access:
            user_management_roles.append('assign_access')
        
        for role_name in ['manage_user', 'assign_access']:
            if role_name not in user_management_roles:
                UserRole.query.filter(UserRole.user_id == user_id, UserRole.name == role_name).delete(synchronize_session='fetch')
            else:
                existing_role = UserRole.query.filter_by(user_id=user_id, name=role_name).first()
                if existing_role is None:
                    role = Role.query.filter_by(name=role_name).first()
                    if not role:
                        role = Role(name=role_name)
                        db.session.add(role)
                        db.session.commit()
                    user_role = UserRole(user_id=user_id, role_id=role.id, name=role_name)
                    db.session.add(user_role)
                UserRole.query.filter(UserRole.user_id == user_id, UserRole.name == 'full_access').delete(synchronize_session='fetch')
        
        db.session.commit()

    # Condition to handle no roles selected for nomination or reviewer

    if not (nomination or reviewer or full_access):
        UserRole.query.filter(UserRole.user_id == user_id, UserRole.name.in_(['edit_only', 'reviewer'])).delete(synchronize_session='fetch')
        
        role = Role.query.filter_by(name='edit_only').first()
        if not role:
            role = Role(name='edit_only')
            db.session.add(role)
            db.session.commit()
        
        user_role = UserRole(user_id=user_id, role_id=role.id, name='edit_only')
        db.session.add(user_role)
        db.session.commit()

    return redirect(url_for('user_access'))

@app.route('/category', methods=['GET', 'POST'])
@not_full_access
@login_required
def category():
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        status=1
        new_end_date_str = request.form['new_end_date']
        new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()
        extension_days = (new_end_date - end_date.date()).days
        new_category = Category(name=name, start_date=start_date, end_date=end_date, status=status,extension_days=extension_days)
        db.session.add(new_category)
        db.session.commit()
        diff_months = (end_date.year - start_date.year) * 12 + end_date.month+1 - start_date.month
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
                award = QuarterlyAward(name=award_name, category_id=new_category.id)
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
                award = AnnuallyAward(name=award_name, category_id=new_category.id)
                db.session.add(award)
        db.session.commit()
        flash('Category added successfully', 'success')
        return redirect(url_for('nomination_duration'))
    return render_template('category.html')


@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@not_full_access
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    extension_days = int(category.extension_days) if category.extension_days is not None else 0
    new_date = (category.end_date + timedelta(days=extension_days)).strftime('%Y-%m-%d')
    if request.method == 'POST':
        category.name = request.form['name']
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        new_end_date_str = request.form['new_end_date']

        try:
            category.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            category.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            new_end_date_str = request.form['new_end_date']
            new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()
            category.extension_days = (new_end_date - category.end_date).days
            if (category.end_date + timedelta(days=category.extension_days)) > datetime.utcnow().date():
                category.status = 1
            db.session.commit()
            flash('Category updated successfully', 'success')
            return redirect(url_for('nomination_duration'))
        except ValueError as e:
            flash(f'Invalid date format: {e}', 'error')
            return render_template('edit_category.html', category=category, new_date=new_date)
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')

    return render_template('edit_category.html', category=category,new_date=new_date)

@app.route('/category/delete/<int:category_id>', methods=['GET','POST'])
@not_full_access
@login_required
def delete_category(category_id):

    category = Category.query.get_or_404(category_id)
    try:
        category.status = 0

        db.session.commit()
        flash('Category marked as deleted successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error marking category as deleted: {str(e)}', 'error')

    return redirect(url_for('nomination_duration'))


@app.route('/nominations/new', methods=['GET', 'POST'])
@login_required
def new_nomination():
    categories =  Category.query.filter_by(status=1).all()
    default_category_id = categories[0].id if categories else None
    team_members = TeamMember.query.all()
    form = NominationForm()
    form.category_id.choices = [(category.id, f"{category.name} ({category.start_date.strftime('%d-%B-%Y')} - {category.end_date.strftime('%d-%B-%Y')})") for category in categories]
    form.team_member_id.choices = [(member.id, member.name) for member in team_members]
    form.nominated_by_name.data = session['username']
    form.nominated_by_global_id.data = session['gid']
    form.nominated_by_email.data = session['email']
    quarterly_awards = QuarterlyAward.query.filter_by(category_id=default_category_id).all()
    annually_awards = AnnuallyAward.query.filter_by(category_id=default_category_id).all()
    awards = quarterly_awards + annually_awards


    if form.validate_on_submit():
        team_member = TeamMember.query.get(form.team_member_id.data)
        team_member_name = team_member.name if team_member else None

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
            award_name=request.form.get('award'),
            team_member_name=team_member_name,
        )
        flash('Nomination added successfully', 'success')
        db.session.add(nomination)
        db.session.commit()
        return redirect(url_for('view_nominees'))
    return render_template('new_nomination.html', form=form, team_members=team_members, categories=categories, awards=awards)

@app.route('/update_nomination/<int:nomination_id>', methods=['POST'])
@approver_access
@login_required
def update_nomination_status(nomination_id):
    
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
    user = User.query.filter_by(gid=session['gid']).first()
    role_names = db.session.query(UserRole.name).filter(UserRole.user_id == user.id).all()
    role_names_list = [role.name for role in role_names]
    if 'full_access' in role_names_list or 'reviewer' in role_names_list:
        nominees = Nomination.query.all()
    elif 'edit_only' in role_names_list:
        nominees = Nomination.query.filter_by(nominated_by_email=session['email']).all()
    else:
        nominees = []

    return render_template('view_nominees.html', nominees=nominees, user=user,role_names_list=role_names_list)



@app.route('/add_team_member', methods=['GET', 'POST'])
@login_required
@not_full_access
def add_team_member():
    if request.method == 'POST':
        name = request.form.get('name')
        gid = request.form.get('gid')
        email = request.form.get('email')
        
        if name and gid and email:
            new_member = TeamMember(name=name, gid=gid, email=email)
            db.session.add(new_member)
            db.session.commit()
            return redirect(url_for('view_team_members'))

    return render_template('add_team_member.html')



@app.route('/view_team_members')
@not_full_access
@login_required
def view_team_members():
    team_members = TeamMember.query.all()
    return render_template('view_team_members.html', team_members=team_members)


@app.route('/get_awards/<int:category_id>', methods=['GET'])
def get_awards(category_id):
    try:
        quarterly_awards = QuarterlyAward.query.filter_by(category_id=category_id).all()
        annually_awards = AnnuallyAward.query.filter_by(category_id=category_id).all()
        awards = [
            {'id': award.id, 'name': award.name} 
            for award in quarterly_awards + annually_awards
        ]        
        return jsonify(awards)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
       
if __name__ == '__main__':
    app.run(debug=True)

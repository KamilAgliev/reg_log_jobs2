import datetime

from flask import Flask, render_template, request, make_response, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, \
    current_user
from flask_wtf import FlaskForm
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect
from wtforms import PasswordField, BooleanField, SubmitField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import jobs_api
from data.category import HazardCategory
from data import db_session
from data.departments import Departments
from data.jobs import Jobs
from data.users import User
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['SECRET_KEY'] = 'my_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        s = db_session.create_session()
        user = s.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/page")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@login_manager.user_loader
def load_user(user_id):
    s = db_session.create_session()
    return s.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route('/page')
def page():
    s = db_session.create_session()
    jobs = s.query(Jobs).all()
    return render_template('page.html', title='myPage', jobs=jobs)


class RegisterForm(FlaskForm):
    email = EmailField('Login / email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat password',
                                   validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Submit')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        s = db_session.create_session()
        if s.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            password=form.password.data)
        user.set_password(form.password.data)
        s.add(user)
        s.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


class JobsForm(FlaskForm):
    team_leader = StringField('team_leader', validators=[DataRequired()])
    job = StringField('Описание работы', validators=[DataRequired()])
    work_size = StringField('Размер работы(в часах)',
                            validators=[DataRequired()])
    collaborators = StringField('Участники', validators=[DataRequired()])
    start_date = StringField('Время начала работы', validators=[DataRequired()])
    end_date = StringField('Время конца работы', validators=[DataRequired()])
    is_finished = BooleanField('Работа закончена?')
    categories = StringField('Категория работы', validators=[DataRequired()])
    submit = SubmitField('Отправить')


@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    form = JobsForm()
    if request.method == 'POST' and form.validate_on_submit():
        s = db_session.create_session()
        job = Jobs()
        job.team_leader = form.team_leader.data
        job.user = s.query(User).filter(User.id == job.team_leader).first()
        job.job = form.job.data
        job.work_size = form.work_size.data
        job.collaborators = form.collaborators.data
        job.start_date = form.start_date.data
        job.end_date = form.end_date.data
        job.is_finished = form.is_finished.data
        job.creator = current_user.id
        categories = HazardCategory(
            name=form.categories.data
        )
        job.categories.append(categories)
        s.add(job)
        s.commit()
        return redirect('/page')
    return render_template('add_job.html', title='Добавление работы',
                           form=form)


@app.route('/job/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    form = JobsForm()
    if request.method == "GET":
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id).first()
        if job:
            form.job.data = job.job
            form.team_leader.data = job.team_leader
            form.work_size.data = job.work_size
            form.collaborators.data = job.collaborators
            form.start_date.data = job.start_date
            form.end_date.data = job.end_date
            form.is_finished.data = job.is_finished
            cats = ""
            for i in job.categories:
                cats += str(i.id) + ","
            form.categories.data = cats[:-1]
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id,
                                         ((Jobs.creator == current_user.id) | (
                                                 current_user.id == 1))).first()
        if job:
            creatorr = job.creator
            session.delete(job)
            job = Jobs()
            job.team_leader = form.team_leader.data
            job.job = form.job.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.start_date = form.start_date.data
            job.end_date = form.end_date.data
            job.is_finished = form.is_finished.data
            job.creator = creatorr
            for i in job.categories:
                job.categories.remove(HazardCategory(name=i.name))
            categories = HazardCategory(
                name=form.categories.data
            )
            job.categories.append(categories)
            session.add(job)
            session.commit()
            return redirect('/page')
        else:
            abort(404)
    return render_template('edit_job.html', title='Редактирование работы',
                           form=form)


@app.route('/job_delete/<int:id>', methods=['GET', 'POST'])
def job_delete(id):
    s = db_session.create_session()
    job = s.query(Jobs).filter(Jobs.id == id,
                               ((Jobs.creator == current_user.id) | (
                                       current_user.id == 1))).first()
    if job:
        s.delete(job)
        s.commit()
    else:
        abort(404)
    return redirect('/page')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


class DepartmentForm(FlaskForm):
    chief = StringField('Главный по депортаменту', validators=[DataRequired()])
    title = StringField('Описание депортамента', validators=[DataRequired()])
    members = StringField('участники департамента', validators=[DataRequired()])
    email = StringField('email департамента', validators=[DataRequired()])
    submit = SubmitField('Отправить')


@app.route('/departments', methods=['GET', 'POST'])
def show_departments():
    s = db_session.create_session()
    departments = s.query(Departments).all()
    return render_template('show_departments.html', title='departments',
                           departments=departments)


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    form = DepartmentForm()
    if request.method == 'POST' and form.validate_on_submit():
        s = db_session.create_session()
        dep = Departments()
        dep.chief = form.chief.data
        dep.title = form.title.data
        dep.members = form.members.data
        dep.email = form.email.data
        s.add(dep)
        s.commit()
        return redirect('/departments')
    return render_template('add_department.html',
                           title='Добавление департамента',
                           form=form)


@app.route('/departments/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    form = DepartmentForm()
    if request.method == "GET":
        session = db_session.create_session()
        department = session.query(Departments).filter(
            Departments.id == id).first()
        if department and (
                current_user.id == 1 or department.chief == current_user.id):
            form.title.data = department.title
            form.chief.data = department.chief
            form.members.data = department.members
            form.email.data = department.email
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        department = session.query(Departments).filter(
            Departments.id == id).first()
        if department:
            session.delete(department)
            department.chief = form.chief.data
            department.title = form.title.data
            department.members = form.members.data
            department.email = form.email.data
            session.add(department)
            session.commit()
            return redirect('/departments')
        else:
            abort(404)
    return render_template('edit_departments.html',
                           title='Редактирование департамента', form=form)


@app.route('/departments_delete/<int:id>')
def departments_delete(id):
    s = db_session.create_session()
    department = s.query(Departments).filter(Departments.id == id).first()
    if department:
        s.delete(department)
        s.commit()
    else:
        print('not')
        abort(404)
    return redirect('/departments')


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


parser_user = reqparse.RequestParser()
parser_user.add_argument('email', required=True)
parser_user.add_argument('name', required=True)
parser_user.add_argument('surname', required=True)
parser_user.add_argument('password', required=True)
parser_user.add_argument('id', required=True, type=int)


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('id', 'name', 'surname', 'email'))})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'name', 'surname', 'email')) for item in users]})

    def post(self):
        args = parser_user.parse_args()
        session = db_session.create_session()
        existing = session.query(User).filter(User.id == args['id']).first()
        if existing:
            return jsonify({'response': 'user with this id is already exists'})
        user = User(
            id=args['id'],
            name=args['name'],
            surname=args['surname'],
            email=args['email']
        )
        user.set_password(args['password'])
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})


def abort_if_job_not_found(job_id):
    session = db_session.create_session()
    job = session.query(Jobs).get(job_id)
    if not job:
        abort(404, message=f"Job {job_id} not found")


parser_job = reqparse.RequestParser()
parser_job.add_argument('team_leader', required=True)
parser_job.add_argument('job', required=True)
parser_job.add_argument('work_size', required=True)
parser_job.add_argument('collaborators', required=True)
parser_job.add_argument('start_date', required=True)
parser_job.add_argument('end_date', required=True)
parser_job.add_argument('is_finished', required=True, type=bool)
parser_job.add_argument('id', required=True, type=int)
parser_job.add_argument('creator', required=True)


class JobsResource(Resource):
    def get(self, job_id):
        abort_if_job_not_found(job_id)
        session = db_session.create_session()
        job = session.query(Jobs).get(job_id)
        return jsonify({'job': job.to_dict(
            only=('id', 'job', 'team_leader', 'work_size', 'start_date',
                  'end_date', 'is_finished'))})

    def delete(self, job_id):
        abort_if_job_not_found(job_id)
        session = db_session.create_session()
        job = session.query(Jobs).get(job_id)
        session.delete(job)
        session.commit()
        return jsonify({'success': 'OK'})


class JobsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        jobs = session.query(Jobs).all()
        return jsonify({'jobs': [item.to_dict(
            only=('id', 'job', 'team_leader', 'work_size', 'start_date',
                  'end_date', 'is_finished')) for item in jobs]})

    def post(self):
        args = parser_job.parse_args()
        session = db_session.create_session()
        existing = session.query(Jobs).filter(Jobs.id == args['id']).first()
        if existing:
            return jsonify({'response': 'job with this id is already exists'})
        job = Jobs(
            id=args['id'],
            job=args['job'],
            team_leader=args['team_leader'],
            work_size=args['work_size'],
            collaborators=args['collaborators'],
            start_date=args['start_date'],
            end_date=args['end_date'],
            is_finished=args['is_finished'],
            creator=args['creator'],
        )
        session.add(job)
        session.commit()
        return jsonify({'success': 'OK'})


if __name__ == "__main__":
    db_session.global_init('db/baza.sqlite')
    api.add_resource(UserListResource, '/api/v2/users')
    api.add_resource(UserResource, '/api/v2/users/<int:user_id>')
    api.add_resource(JobsResource, '/api/v2/jobs/<int:job_id>')
    api.add_resource(JobsListResource, '/api/v2/jobs')
    app.run()

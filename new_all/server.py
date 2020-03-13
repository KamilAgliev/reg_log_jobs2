import datetime

from flask import Flask, render_template, request
from flask_login import LoginManager, login_user, login_required, logout_user, \
    current_user
from flask_wtf import FlaskForm
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect
from wtforms import PasswordField, BooleanField, SubmitField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from data import db_session
from data.category import Category
from data.departments import Departments
from data.jobs import Jobs
from data.users import User

app = Flask(__name__)
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
@login_required
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
        login_user(user)
        return redirect("/page")
    return render_template('register.html', title='Регистрация', form=form)


class JobsForm(FlaskForm):
    team_leader = StringField('team_leader', validators=[DataRequired()])
    job = StringField('Описание работы', validators=[DataRequired()])
    work_size = StringField('Размер работы(в часах)',
                            validators=[DataRequired()])
    collaborators = StringField('Участники', validators=[DataRequired()])
    start_date = StringField('Время начала работы', validators=[DataRequired()])
    end_date = StringField('Время конца работы', validators=[DataRequired()])
    category = StringField('Категория работы', validators=[DataRequired()])
    is_finished = BooleanField('Работа закончена?')
    submit = SubmitField('Отправить')


@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    form = JobsForm()
    if request.method == 'POST' and form.validate_on_submit():
        s = db_session.create_session()
        job = Jobs()
        job.team_leader = form.team_leader.data
        job.job = form.job.data
        job.work_size = form.work_size.data
        job.collaborators = form.collaborators.data
        job.start_date = form.start_date.data
        job.end_date = form.end_date.data
        job.is_finished = form.is_finished.data
        job.creator = current_user.id
        category = Category(
            name=form.category.data
        )
        job.categories.append(category)
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
        if job and (current_user.id == job.creator or current_user.id == 1):
            form.job.data = job.job
            form.team_leader.data = job.team_leader
            form.work_size.data = job.work_size
            form.collaborators.data = job.collaborators
            form.start_date.data = job.start_date
            form.end_date.data = job.end_date
            form.is_finished.data = job.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id).first()
        if job:
            session.delete(job)
            job = Jobs()
            job.team_leader = form.team_leader.data
            job.job = form.job.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.start_date = form.start_date.data
            job.end_date = form.end_date.data
            job.is_finished = form.is_finished.data
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
    job = s.query(Jobs).filter(Jobs.id == id).first()
    if job:
        s.delete(job)
        s.commit()
    else:
        abort(404)
    return redirect('/page')


@app.route('/departments', methods=['GET', 'POST'])
def show_departments():
    s = db_session.create_session()
    departments = s.query(Departments).all()
    return render_template('show_departments.html', title='departments',
                           departments=departments)


class DepartmentForm(FlaskForm):
    chief = StringField('Главный по депортаменту', validators=[DataRequired()])
    title = StringField('Описание депортамента', validators=[DataRequired()])
    members = StringField('участники департамента', validators=[DataRequired()])
    email = StringField('email департамента', validators=[DataRequired()])
    submit = SubmitField('Отправить')


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
        abort(404)
    return redirect('/departments')


if __name__ == "__main__":
    db_session.global_init('db/baza.sqlite')
    se = db_session.create_session()
    job = se.query(Jobs).first()
    app.run()

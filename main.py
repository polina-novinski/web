from flask import Flask, render_template, redirect, url_for
from flask import abort
from data import db_session
from data.users import User
from data.news import News
from register_form import RegisterForm
from flask_login import LoginManager, LoginManager, login_user, login_required, logout_user, current_user
from login_form import LoginForm
from add_news import NewsForm
from map import get_map
#import requests
from requests import request


import base64
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/blogs.db")
login_manager = LoginManager()
login_manager.init_app(app)
map_file = 'static/img/temp.jpg'

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/blog")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News(
            title=form.title.data,
            content=form.content.data,
            is_private=form.is_private.data,
            geopos=form.geopos.data
        )
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/blog')
    return render_template('news.html', title='Добавление новости',
                           form=form)

@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/blog')

@app.route('/show_geo/<int:id>', methods=['GET', 'POST'])
@login_required
def show_geo(id):
    db_sess = db_session.create_session()
    geo = db_sess.query(News.geopos).filter(News.id == id).first()
    map = get_map(geo)
    with open(map_file, 'wb') as file:
        file.write(map)
        return f'''<img src="{map_file}" alt="не нашлась">'''
        #return f'''<img src="{map_file} alt="""/>'''


@app.route('/news_like/<int:id>', methods=['GET', 'POST'])
@login_required
def like(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id
                                      ).first()
    if news:
        news.likes += 1
        form.likes.data = news.likes
        db_sess.commit()
    else:
        abort(404)
    return redirect('/blog')

@app.route('/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
            form.geopos.data = news.geopos
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            #news.geopos = form.geopos.data
            db_sess.commit()
            return redirect('/blog')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )

@app.route("/")
def index():
    return render_template('index.html', title='Главная')
                           #content='<img src="static/img/av.jpg" alt="">')


@app.route("/blog")
def news_page():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    ##
    map_list =[]
    #for new in news:
        #if new.geopos:
            #1 по имени получаем координаты
            #2 по координатам получаем карту
            #3
            #pass

    ##
    return render_template("blog.html", news=news)


#@app.route('/n')
#def image():
    #return f'''<img src="{url_for('static', filename='img/av.jpg')}"
          # alt="здесь должна была быть картинка, но не нашлась">'''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

app.run(port=8080, host='127.0.0.1')
# def main():
#     db_session.global_init("db/blogs.db")
#     app.run()

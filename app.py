#coding=utf-8
import settings
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from flask import Flask,render_template,request,flash,redirect,url_for
import os
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import get_debug_queries
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,UserMixin,login_user,login_required, logout_user,current_user
WIN=sys.platform.startswith('win')
if WIN:
    prefix='sqlite:///'
else:
    prefix="sqlite:////"
app = Flask(__name__)
app.secret_key = 'dev'
app.config['SQLALCHEMY_DATABASE_URI']=prefix+os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['DATABASE_QUERY_TIMEOUT']=0.00001
app.config['SQLALCHEMY_RECORD_QUERIES']=True
formatter=logging.Formatter(
"[%(asctime)s]{%(pathname)s:%(lineno)d}%(levelname)s -%(message)s"
)
handler=RotatingFileHandler('slow_query.log',maxBytes=10000,backupCount=10)
handler.setLevel(logging.WARN)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
db=SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user
class User(db.Model,UserMixin):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    username=db.Column(db.String(20))
    password_hash=db.Column(db.String(128))
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)
    def validate_password(self,password):
        return check_password_hash(self.password_hash,password)
class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份
class Leave_message(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20),unique=True)
    message=db.Column(db.Text)
    create_time=db.Column(db.DateTime)
@app.context_processor
def inject_user():
    user=User.query.first()
    return dict(user=user)
@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')
@app.route('/message', methods=['GET', 'POST'])
def message():
    messageall=Leave_message.query.all()
    if request.method == 'POST':
        Username = request.form['Username']
        Message = request.form['Message']

        if not Username or not Message:
            flash('Invalid input.')
            return redirect(url_for('Message'))
        m=(Leave_message(name=Username,message=Message,create_time=datetime.now()))
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('message'))
    return render_template('message.html',messageall=messageall)

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向到主页
        title=request.form.get('title')
        year=request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash("Invalid input")
            return redirect(url_for('index'))
        movie=Movie(title=title , year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created')
        return redirect(url_for('index'))
    movies=Movie.query.all()
    return render_template('index.html',movies=movies)
@app.route('/hello/<username>')
def hello(username):  # put application's code here
    return 'Hello World!%s'% username
@app.route('/movie/edit/<int:movie_id>',methods=['GET','POST'])
@login_required
def edit(movie_id):
    movie=Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title=request.form['title']
        year=request.form['year']
        if not title or not year or len(year)>4 or len(title) > 60:
            flash('Invalid Input')
            return redirect(url_for('edit',movie_id=movie_id))
        movie.title=title
        movie.year=year
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html',movie=movie)
@app.route('/add',methods=['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        title=request.form['title']
        year=request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid Input')
            return redirect(url_for('edit',movie_id=movie_id))
        m=Movie(title=title,year=year)
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')
@app.route('/movie/delete/<int:movie_id>',methods=['GET','POST'])
@login_required
def delete(movie_id):
    movie=Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('index'))
import click
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')
@app.errorhandler(404)
def page_not_found(e):
    user=User.query.first()
    return render_template('404.html',user=user),404
@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= app.config['DATABASE_QUERY_TIMEOUT']:
            app.logger.warn(
                ('Context:{}\nSLOW QUERY:{}\nParameters:{}\n'
                 'Duration:{}\n').format(query.context,query.statement,query.parameters,query.duration)
            )
    return response
if __name__ == '__main__':
    app.secret_key = 'kasdjh@7834jsdfwse45'
    app.run(DEBUG=True,host='0.0.0.0')

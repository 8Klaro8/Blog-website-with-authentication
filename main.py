import hashlib
import random
import urllib.parse
from hashlib import md5

import requests
from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import sqlite3
from functools import wraps
from sqlalchemy import Table, Column, Integer, ForeignKey, engine
from sqlalchemy.ext.declarative import declarative_base



app = Flask(__name__)
app.config['SECRET_KEY'] = 'something'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

## Initializing Gravatar
# TODO make happen own default gravatar pic
default_image = 'https://proaktivdirekt.com/adaptive/article_md/upload/images/magazine/kemeny-sajt.jpg'
encoded_image = default_image.encode()
print(encoded_image)
email_address = 'valami@gmail.com'
converted_email = email_address.lower().strip()
encoded_email = converted_email.encode(encoding='UTF-8',errors='strict')
hashed_email = md5(encoded_email)

list_of_options = ['mp', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash']
rand_option = random.choice(list_of_options)
basic_image_request = f'https://www.gravatar.com/avatar/{hashed_email}?s=300&d={rand_option}'


'''Creating admin_only decorator'''
# TODO spend more time to udnerstand wrapping
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(403, description="Not authorized")
        elif current_user.id == 1:
            print('authorized admin')
        return f(*args, **kwargs)
    return decorated_function

##CONFIGURE TABLES
'''Creating declerative base for parent-childrent relationship - One-To-Many'''
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    prof_pic = db.Column(db.String)

    posts = relationship("BlogPost", back_populates="author")
    comment = relationship('Comments', back_populates='author_of_comment')

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author = relationship('Users', back_populates='posts')
    '''Links the users.id to this child item'''
    author_id = Column(Integer, ForeignKey('users.id'))

    comment = relationship('Comments', back_populates='blog_comment')

class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_of_comment = relationship('Users', back_populates='comment')
    user_id = Column(Integer, ForeignKey('users.id'))

    blog_id = Column(Integer, ForeignKey('blog_posts.id'))
    blog_comment = relationship('BlogPost', back_populates='comment')

    '''It has been saved in show_post method as the current_user.name'''
    commenter = db.Column(db.Text)
    profile_pic = db.Column(db.String)


db.create_all()
'''Creating a blog example for test purposes'''
# first_blog = BlogPost(title='My sweet',
#                       subtitle='First section',
#                       date='01.01.2303',
#                       body='efeíeggrggegeggwgrwg. fegwsgrgsrgrygds. fwrgwrgrwgrgrhthtegsgnbtehorkgogfewfef.'
#                            'efeíeggrggegeggwgrwg. fegwsgrgsrgrygds. fwrgwrgrwgrgrhthtegsgnbtehorkgogfewfef.'
#                            'efeíeggrggegeggwgrwg. fegwsgrgsrgrygds. fwrgwrgrwgrgrhthtegsgnbtehorkgogfewfef.',
#                       img_url='https://ca-times.brightspotcdn.com/dims4/default/940e7a7/2147483647/strip/true/'
#                               'crop/480x252+0+54/resize/1200x630!/quality/90/?url=https%3A%2F%2Fi.ytimg.com%2F'
#                               'vi%2F04v-SdKeEpE%2Fhqdefault.jpg')
# db.session.add(first_blog)
# db.session.commit()


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    users = Users.query.all()
    for post in posts:
        for user in users:
            if post.id == user.id:
                current_author = user.name
                # TODO specify the author based on who wrote the post
                return render_template("index.html", all_posts=posts, author=current_author)
    return render_template('index.html', all_posts=posts)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    all_uer = Users.query.all()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        for user in all_uer:
            if user.email == email:
                flash('This email is registered. Try to login instead.', 'error')
                return redirect(url_for('register'))

        '''Hash and salt password'''
        hash_salt_password = generate_password_hash(password=password,
                               method='pbkdf2:sha256',
                               salt_length=8)


        profff_pic = create_pic_request(email)
        new_user = Users(name=name,
                         email=email,
                         password=hash_salt_password,
                         prof_pic=profff_pic)
        db.session.add(new_user)
        db.session.commit()
        # TODO solve it when someone registers then lead them to login page with a different message
        posts = BlogPost.query.all()
        comes_from_register = 'sth'
        login_user(new_user)
        return  render_template('index.html', all_posts=posts, comes_from_register=comes_from_register)
    return render_template("register.html",
                           form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    username = form.username.data
    password = form.password.data
    if form.validate_on_submit():
        '''check if credentials are good'''
        all_user = Users.query.all()
        for user in all_user:
            if user.email == username:
                if check_password_hash(user.password, password):
                    login_user(user)
                    comes_from_login = 'sth'
                    return render_template('index.html', comes_from_login=comes_from_login)
                else:
                    flash('Password is incorrect.')
                    return redirect(url_for('login'))
        flash('Email does not exists', 'error')
        return redirect(url_for('login'))
    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    print('user logged out')
    comes_from_logout = 'sth'
    return render_template('index.html', comes_from_logout=comes_from_logout)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    '''Gets the appropriate post by id'''
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    if request.method == 'POST':
        '''If the user typed nothing it gives an error message'''
        if len(comment_form.body.data) < 1:
            flash("You didn't write any message yet", 'error')
        else:
            if current_user.is_authenticated:

                '''Below I assign the current users name to the commenter field inside of Comments
                so that the commenter names will be saved to each comment.
                The sae thing I did with profile_pic. I created a Column in Comments class, named it profile_pic
                and the previously saved item inside Users --> prof_pic, I append it.'''
                new_comment = Comments(text=comment_form.body.data,
                                       commenter=current_user.name,
                                       blog_id=post_id,
                                       profile_pic=current_user.prof_pic)
                db.session.add(new_comment)
                db.session.commit()

                '''Resets the ckeditor field after submitting a comment --> '''
                comment_form.body.data = ''
            else:
                flash('Unable to comment without log in', 'error')
                return redirect(url_for('show_post', post_id=post_id))

    '''Get all comment and pass it to post.html so I can render it inside post.html
    Inside post.html I compare post_id and the current comments blog_id and if there
     is a match then post.html rneders the correct comments'''
    # TODO Use flask relationship to make the relationships happen between user, blog and comment
    all_comment = Comments.query.all()
    return render_template("post.html",
                           post=requested_post,
                           comment_form=comment_form,
                           all_comment=all_comment,
                           post_id=post_id)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/new-post", methods=['POST','GET'])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        # TODO check if its a good idea to assign current users name to author_id
        new_post = BlogPost(title=form.title.data,
                            subtitle=form.subtitle.data,
                            date=date.today().strftime("%B %d, %Y"),
                            body=form.body.data,
                            img_url=form.img_url.data,
                            author_id=current_user.name)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(title=post.title,
                               subtitle=post.subtitle,
                               img_url=post.img_url,
                               author=post.author,
                               body=post.body)
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)

@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

##Functions
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

def get_authors_name(post_id):
    '''Checking the author by comparing the saved id inside of
        the Users class vs the users id, created with relationship.
        Then I pass it thru to the index.html to display the authors name'''
    post = BlogPost.query.get(post_id)
    all_users = Users.query.all()
    for user in all_users:
        if user.id == post.id:
            return user.name


def create_pic_request(email):
    list_of_options = ['mp', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash']
    rand_option = random.choice(list_of_options)
    converted_email = email.lower().strip()
    encoded_email = converted_email.encode(encoding='UTF-8', errors='strict')
    hashed_email = md5(encoded_email)
    basic_image_request = f'https://www.gravatar.com/avatar/{hashed_email}?s=300&d={rand_option}'
    return basic_image_request



if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)

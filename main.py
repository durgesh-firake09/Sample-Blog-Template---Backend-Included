# Sample Blog Template with backend works
# Please Configure all parameters in config.json

from datetime import datetime
from flask import Flask, render_template, request, session, redirect
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
import json
import math



local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create a database in mysql
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(13), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    tagline = db.Column(db.String(30), nullable=False)
    img = db.Column(db.String(100), nullable=True)
    slug = db.Column(db.String(15), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)


@app.route('/')
def home():
    # Pagination Logic
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[((page - 1) * int(params['no_of_posts'])) : ((page - 1) * int(params['no_of_posts']) + int(params['no_of_posts']))]

    # First
    if page == 1:
        prev = '#'
        next = "/?page=" + str(page + 1)
    # End
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    # Middle
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params,posts =posts,prev=prev, next = next)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add entries to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')

        # Add entry to database
        entry = Contact(name=name, email=email, phone=phone,
                        msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        try:
            mail.send_message('New Message From Blog from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=f"{msg}\n\nFrom\n{name}\n{phone}\n{email}",

                          )
        except Exception as e:
            pass
    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html', params=params, post = post)

@app.route('/dashboard', methods = ['GET','POST'])
def admin():
    if ('user' in session) and (session['user'] == params['admin-username']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params= params, posts = posts)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if (username == params['admin-username']) and (password == params['admin-password']):
            # set session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts = posts)
   
    return render_template('admin.html',params = params)

@app.route('/edit/<string:sno>', methods = ['GET','POST'])
def edit(sno):
    if ('user' in session) and (session['user'] == params['admin-username']):
        if request.method == 'POST':
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img = request.form.get('img')
            date = datetime.now()

            if sno == '0':
                post = Posts(title = title, tagline =tagline, img = img, slug = slug, content = content,  date = date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno = sno).first()
        return render_template('edit.html', params = params, post = post, sno = sno)

@app.route('/delete/<string:sno>', methods = ['GET','POST'])
def delete(sno):
    if ('user' in session) and (session['user'] == params['admin-username']):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


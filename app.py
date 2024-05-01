import re
from search import Search
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from login import LoginForm
from config import Config
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import sqlalchemy as sa 

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
es = Search()

from models import User

@app.route('/login', methods=['GET', 'POST'])
def login():
    query = sa.select(User)
    users = db.session.scalars(query).all()
    for u in users:
        print(u.id, u.username)
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))           # Make it User.username during error!
        if user is None or not user.check_password(form.password.data):
            return redirect('/login')
        login_user(user, remember=form.remember_me.data)
        return redirect('/')
    return render_template('login.html', title='Sign In', form= form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

@app.get('/')
def index():
    if not current_user.is_authenticated:
        return redirect('/login')
    return render_template('index.html')

@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    print(query)
    results = es.search(
        query={
            'match': {
                'name': {
                    'query': query
                }
            }
        }
    )
    for hit in results['hits']['hits']:
            # Access the _source field of each hit
            source = hit['_source']
            # Extract the additional_urls field if it exists
            additional_urls = source.get('additional_urls', [])
            # Print the additional_urls
            print("Additional URLs:", additional_urls)

    return render_template('index.html', results=results['hits']['hits'],
                           query=query, from_=0,
                           total=results['hits']['total']['value'])



@app.get('/document/<id>')
def get_document(id):
    return 'Document not found'

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created '
        f'in {response["took"]} milliseconds.')


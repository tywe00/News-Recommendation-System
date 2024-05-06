import re
from search import Search
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from login import LoginForm
from config import Config
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from preference import NewsPreferenceForm
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

@app.route('/preference', methods=['GET', 'POST'])
def choose_news_type():
    form = NewsPreferenceForm()
    if form.validate_on_submit():
        preferences = form.preferences.data
        es.insert_user_preference(current_user.id, preferences)
        # Query Elasticsearch with user preferences
        # results = search_news(preferences)
        return render_template('index.html')
    return render_template('preference.html', form=form)

@app.route('/my_profile', methods=['GET', 'POST'])
def about_me():
    user_preferences = es.get_user_preference(current_user.id)
    topics = []
    if user_preferences:
        try:
            topics = user_preferences['_source']['preferences']
        except KeyError:
            pass

    relevant_articles = es.get_relevant_articles(current_user.id)
    processed_articles = []
    if relevant_articles:
        try:
            articles = relevant_articles['_source']['preferences']
            for result in articles:
                _, title, url = result.split(',')
                processed_articles.append({
                    'title': title,
                    'url': url
                })
        except KeyError:
            pass

    return render_template('profile.html', topics=topics, processed_articles=processed_articles)

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

@app.route('/handle_selected_results', methods=['POST'])
def handle_selected_results():
    selected_results = request.form.getlist('selected_results')
    ''' processed_results = []
    for result in selected_results:
        id_, title, url = result.split(',')
        processed_results.append({
            'id': id_,
            'title': title,
            'url': url
        }) '''
    es.insert_relevant_articles(current_user.id, selected_results)
    #print("HERE ARE SELECTED ARTICLES")
    #print(len(selected_results))
    return render_template('index.html')

@app.get('/document/<id>')
def get_document(id):
    return 'Document not found'

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created '
        f'in {response["took"]} milliseconds.')


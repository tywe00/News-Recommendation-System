import re
from search import Search
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from login import LoginForm
from config import Config
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from preference import ClearNewsPreferenceForm, ClearRelevantArticlesForm, NewsPreferenceForm
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
    clearNewsPreference = ClearNewsPreferenceForm()
    ClearRelevantArticles = ClearRelevantArticlesForm()

    user_preferences = es.get_user_preference(current_user.id)
    topics = []
    if user_preferences:
        try:
            topics = user_preferences['_source']['preferences']
        except KeyError:
            pass

    relevant_article = es.get_relevant_article(current_user.id)
    processed_articles = []
    if relevant_article:
        try:
            articles = relevant_article['_source']['preferences']
            for result in articles:
                _, title, url, _ = result.split('=()=')
                processed_articles.append({
                    'title': title,
                    'url': url
                })
        except KeyError:
            pass

    if clearNewsPreference.validate_on_submit():
        es.remove_user_preference(current_user.id)
        user_preferences = es.get_user_preference(current_user.id)
        topics = []
        if user_preferences:
            try:
                topics = user_preferences['_source']['preferences']
            except KeyError:
                pass

    if ClearRelevantArticles.validate_on_submit():
        es.remove_relevant_article(current_user.id)
        relevant_article = es.get_relevant_article(current_user.id)
        processed_articles = []
        if relevant_article:
            try:
                articles = relevant_article['_source']['preferences']
                for result in articles:
                    _, title, url, _ = result.split('=()=')
                    processed_articles.append({
                        'title': title,
                        'url': url
                    })
            except KeyError:
                pass

    return render_template('profile.html', topics=topics, processed_articles=processed_articles, clearNewsPreference=clearNewsPreference, ClearRelevantArticles=ClearRelevantArticles)

@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    relevant_article = es.get_relevant_article(current_user.id)
    processed_articles = []
    
    if relevant_article:
        try:
            articles = relevant_article['_source']['preferences']
            for result in articles:
                id, _, _, index = result.split('=()=')
                processed_articles.append({
                    '_index': index,
                    '_id': id
                })
        except KeyError:
            pass
    must = [ { "multi_match": {
        "query": query,
        "fields": [
            "title^3",
            "body_content",
        ],
        "fuzziness": "AUTO",
        "boost": 2,
    } } ]
    if len(processed_articles) > 0 :
        should = ({ "more_like_this": {
            "fields": ["title", "body_content"],
            "like": processed_articles,
            "min_term_freq": 2,
            "max_query_terms": 25,
            "boost": 0.5
        }})
        results = es.search(
            query={ 
                "bool": {
                    "must": must, 
                    "should": should 
                } 
            }
        )
        return render_results(query, results)
    else:
        results = es.search(
            query={ 
                "bool": {
                    "must": must, 
                } 
            }
        )
        return render_results(query, results)

def render_results(query, results):
    final_results = []
    for section in ['business_articles', 'entertainment_articles', 'science_articles', 'sports_articles', 'technology_news', 'world_articles']:
        if section in results and results[section] is not None:
            if(results[section]['hits']['hits']):
                for hit in results[section]['hits']['hits']:
                        # Access the _source field of each hit
                        source = hit['_source']
                        # Extract the additional_urls field if it exists
                        additional_urls = source.get('additional_urls', [])
                        final_results.append(hit)
    sorted_list = sorted(final_results, key=lambda x: x['_score'] , reverse=True)
    return render_template('index.html', results=sorted_list,
                           query=query, from_=0,
                           total=len(final_results))

@app.route('/handle_selected_results', methods=['POST'])
def handle_selected_results():
    selected_results = request.form.getlist('selected_results')
    es.insert_relevant_article(current_user.id, selected_results)
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


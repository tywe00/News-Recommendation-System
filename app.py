import re
from search import Search

from flask import Flask, render_template, request

app = Flask(__name__)
es = Search()


@app.get('/')
def index():
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

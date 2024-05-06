import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

load_dotenv()


class Search:
    def __init__(self):
        #self.es = Elasticsearch('http://localhost:9200')
        # self.es = Elasticsearch(cloud_id=os.environ['ELASTIC_CLOUD_ID'],
        #                         api_key=os.environ['ELASTIC_API_KEY'])
        # self.es = Elasticsearch("https://19acd04ebc714e58a60ccf6e3867c367.uksouth.azure.elastic-cloud.com/",
        #                         api_key=os.environ['ELASTIC_API_KEY'])
        
        self.es = Elasticsearch(
            "https://19acd04ebc714e58a60ccf6e3867c367.uksouth.azure.elastic-cloud.com/",
            api_key="ZjBmWkJZOEJheUpRT1cweEhJTnI6QkdRNlg5MU1UZHFPVjg3TC1lekZUUQ=="
        )
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        doc_count = self.es.count(index="search-news-articles")['count']
        print("Number of documents indexed:", doc_count)
        pprint(client_info.body)

    def search(self, **query_args):
        print(query_args)
        print(self.es.search(index="search-news-articles", **query_args))
        search_term = query_args.get('query', {}).get('match', {}).get('name', None).get('query', None)
        print("Search term:", search_term)
        response = self.es.search(index="search-news-articles", q=search_term)

        # Iterate over the hits in the response
        # for hit in response['hits']['hits']:
        #     # Access the _source field of each hit
        #     source = hit['_source']
        #     # Extract the additional_urls field if it exists
        #     additional_urls = source.get('additional_urls', [])
        #     # Print the additional_urls
        #     print("Additional URLs:", additional_urls)

        return response

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents')

    def insert_document(self, document):
        return self.es.index(index='my_documents', body=document)
    
    def insert_user_preference(self, user_id, new_preferences):
        try:
            # Get the existing document
            existing_doc = self.es.get(index='user_preference', id=user_id)
            existing_preferences = existing_doc.get('_source', {}).get('preferences', [])
        except NotFoundError:
            # If the document doesn't exist, initialize with an empty list
            existing_preferences = []

        # Merge the existing preferences with the new preferences
        merged_preferences = list(set(existing_preferences + new_preferences))

        # Update the document with the merged preferences
        body = {'doc': {'preferences': merged_preferences}}
        return self.es.update(index='user_preference', id=user_id, body=body)

    
    def get_user_preference(self, user_id):
        try:
            response = self.es.get(index='user_preference', id=user_id)
            return response
        except NotFoundError:
            # Handle the case when the document is not found
            return None
        
    def insert_relevant_articles(self, user_id, new_preferences):
        # Retrieve the existing document
        try:
            existing_doc = self.es.get(index='relevant_articles', id=user_id)
            existing_preferences = existing_doc.get('_source', {}).get('preferences', [])
        except NotFoundError:
            existing_preferences = []

        # Merge the existing preferences with the new ones
        merged_preferences = list(set(existing_preferences + new_preferences))

        # Update the document with the merged preferences
        return self.es.update(
            index='relevant_articles',
            id=user_id,
            body={'doc': {'preferences': merged_preferences}}
        )

    
    def get_relevant_articles(self, user_id):
        try:
            response = self.es.get(index='relevant_articles', id=user_id)
            return response
        except NotFoundError:
            return None
    
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
        return self.es.bulk(operations=operations)
    
    def reindex(self):
        self.create_index()
        with open('data.json', 'rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)
    
  



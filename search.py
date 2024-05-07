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
        
        # self.es = Elasticsearch(
        #     "https://19acd04ebc714e58a60ccf6e3867c367.uksouth.azure.elastic-cloud.com/",
        #     api_key="ZjBmWkJZOEJheUpRT1cweEhJTnI6QkdRNlg5MU1UZHFPVjg3TC1lekZUUQ=="
        # )

        self.es = Elasticsearch(
            "https://8f6b0d33849648b080a3dbc31e48b286.uksouth.azure.elastic-cloud.com:443",
            api_key="YzJrLVU0OEJYWHFzMmR5WEtreEE6NGtXdkQ3SU1US1cycy1hOW5oajJTUQ=="
        )

        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        doc_count = self.es.count(index="search-business-articles")['count'] + self.es.count(index="search-science-articles")['count'] + self.es.count(index="search-sports-articles")['count'] + self.es.count(index="search-technology-news")['count']+ self.es.count(index="search-world-articles")['count']
        print("Number of documents indexed:", doc_count)
        pprint(client_info.body)

    def search(self, **query_args):
        # print(query_args)
        # print(self.es.search(index="search-business-articles", **query_args))
        search_term = query_args.get('query', {}).get('match', {}).get('name', None).get('query', None)
        print("Search term:", search_term)
        #response = self.es.search(index="search-business-articles", q=search_term)
        # Perform individual searches
        response1 = self.es.search(index="search-business-articles", q=search_term)
        response2 = self.es.search(index="search-entertainment-articles", q=search_term)
        response3 = self.es.search(index="search-science-articles", q=search_term)
        response4 = self.es.search(index="search-sports-articles", q=search_term)
        response5 = self.es.search(index="search-technology-news", q=search_term)
        response6 = self.es.search(index="search-world-articles", q=search_term)

        # Combine the responses
        combined_response = {
            "business_articles": response1,
            "entertainment_articles": response2,
            "science_articles": response3,
            "sports_articles": response4,
            "technology_news": response5,
            "world_articles": response6
        }

        return combined_response

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
        body = {'doc': {'id': user_id,'preferences': merged_preferences}}
        return self.es.update(index='user_preference', id=user_id, body=body)

    def get_user_preference(self, user_id):
        try:
            response = self.es.get(index='user_preference', id=user_id)
            return response
        except NotFoundError:
            # Handle the case when the document is not found
            return None
        
    def remove_user_preference(self, user_id):
        try:
            # Get the existing document
            existing_doc = self.es.get(index='user_preference', id=user_id)
            
        except NotFoundError:
            # If the document doesn't exist, initialize with an empty list
            existing_preferences = []
       
        # Update the document with the merged preferences
        body = {'doc': {'preferences': []}}
        return self.es.update(index='user_preference', id=user_id, body=body)


            
        
    def insert_relevant_article(self, user_id, new_preferences):
        try:
            # Retrieve the existing document
            existing_doc = self.es.get(index='relevant_article', id=user_id)
            existing_preferences = existing_doc.get('_source', {}).get('preferences', [])
        except NotFoundError:
            # Handle the case where the document doesn't exist
            existing_preferences = []

        # Merge the existing preferences with the new ones
        merged_preferences = list(set(existing_preferences + new_preferences))

        # Update the document with the merged preferences
        return self.es.index(
            index='relevant_article',
            id=user_id,
            body={'preferences': merged_preferences}
        )
    
    def get_relevant_article(self, user_id):
        try:
            response = self.es.get(index='relevant_article', id=user_id)
            return response
        except NotFoundError:
            return None
        
        
    def remove_relevant_article(self, user_id):
        print("remove arttciclessssss")
        try:
            # Get the existing document
            existing_doc = self.es.get(index='relevant_article', id=user_id)
            
        except NotFoundError:
            # If the document doesn't exist, initialize with an empty list
            existing_preferences = []
       
        # Update the document with the merged preferences
        body = {'doc': {'preferences': []}}
        return self.es.update(index='relevant_article', id=user_id, body=body)
    
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
    
  



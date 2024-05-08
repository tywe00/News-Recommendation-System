import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from flask_login import  current_user
load_dotenv()


class Search:
    def __init__(self):
        self.es = Elasticsearch(
            "https://8f6b0d33849648b080a3dbc31e48b286.uksouth.azure.elastic-cloud.com:443",
            api_key="YzJrLVU0OEJYWHFzMmR5WEtreEE6NGtXdkQ3SU1US1cycy1hOW5oajJTUQ=="
        )

        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        doc_count = self.es.count(index="search-business-articles")['count'] + self.es.count(index="search-science-articles")['count'] + self.es.count(index="search-sports-articles")['count'] + self.es.count(index="search-technology-news")['count']+ self.es.count(index="search-world-articles")['count']
        print("Number of documents indexed:", doc_count)
        pprint(client_info.body)
    
    def search_request(self, index_name, **query_args):
        # sub_searches is not currently supported in the client, so we send
        # search requests as raw requests
        if "from_" in query_args:
            query_args["from"] = query_args["from_"]
            del query_args["from_"]
        return self.es.perform_request(
            "GET",
            f"/{index_name}/_search",
            body=json.dumps(query_args),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def search(self, **query_args):
        es = Search()
        user_preferences = es.get_user_preference(current_user.id)
        topics = None
        if user_preferences:
            try:
                topics = user_preferences['_source']['preferences']
            except KeyError:
                pass
        response1 = None
        response2 = None
        response3 = None
        response4 = None
        response5 = None
        response6 = None

        if(topics == []):
            response1 = self.search_request("search-business-articles", **query_args)
            response2 = self.search_request("search-entertainment-articles", **query_args)
            response3 = self.search_request("search-science-articles", **query_args)
            response4 = self.search_request("search-sports-articles", **query_args)
            response5 = self.search_request("search-technology-news", **query_args)
            response6 = self.search_request("search-world-articles", **query_args)
        else:
            if('Business' in topics):
                response1 = self.search_request("search-business-articles", **query_args)
            if('Entertainment' in topics):
                response2 = self.search_request("search-entertainment-articles", **query_args)
            if('Science' in topics):
                response3 = self.search_request("search-science-articles", **query_args)
            if('Sports' in topics):
                response4 = self.search_request("search-sports-articles", **query_args)
            if('Technology' in topics):
                response5 = self.search_request("search-technology-news", **query_args)
            if('World' in topics):
                response6 = self.search_request("search-world-articles", **query_args)

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
        try:
            # Merge the existing preferences with the new preferences
            merged_preferences = list(set(existing_preferences + new_preferences))

            # Update the document with the merged preferences
            body = {'doc': {'preferences': merged_preferences}}
            return self.es.update(index='user_preference', id=user_id, body=body)
        except NotFoundError:
            # If the document does not exist, create it
            body = {'preferences': merged_preferences}
            return self.es.create(index='user_preference', id=user_id, body=body)

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
    
  



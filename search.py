import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

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
        search_term = query_args.get('query', {}).get('match', {}).get('name', None).get('query', None)
        response = self.es.search(index="search-news-articles", q=search_term)
        return response

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents')

    def insert_document(self, document):
        return self.es.index(index='my_documents', body=document)
    
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
    
  



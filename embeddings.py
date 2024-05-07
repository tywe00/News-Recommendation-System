from elasticsearch import Elasticsearch, helpers
import numpy as np
from sentence_transformers import SentenceTransformer
from pprint import pprint

# Initialize Elasticsearch client
es = Elasticsearch(
    "https://19acd04ebc714e58a60ccf6e3867c367.uksouth.azure.elastic-cloud.com/",
    api_key="ZjBmWkJZOEJheUpRT1cweEhJTnI6QkdRNlg5MU1UZHFPVjg3TC1lekZUUQ=="
)
client_info = es.info()
print('Connected to Elasticsearch!')
doc_count = es.count(index="search-test-articles")['count']
print("Number of documents indexed:", doc_count)
pprint(client_info.body)

# Initialize sentence transformer model for calculating embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Retrieve all documents from the existing index
existing_index = 'search-test-articles'
query = {'query': {'match_all': {}}}
print("Preparing to fetch whole index!")
documents = helpers.scan(es, query=query, index=existing_index)
print("Fetched the whole index!")

print("Calculate embeddings and update documents")
actions = []
for doc in documents:
    content = ' '.join([doc['_source']['title'], doc['_source']['body_content']])
    # print("Content is: " + str(content))
    embedding = model.encode(content)
    # print("Embedding is : " + str(embedding))
    action = {
        "_op_type": "update",
        "_index": existing_index,
        "_id": doc["_id"],
        "doc": {
            "embedding": embedding.tolist()
        }
    }
    actions.append(action)

# Update the mapping of the existing index
embedding_mapping = {
    "properties": {
        "embedding": {
            "type": "dense_vector",
            "dims": len(embedding)  # Specify the dimensionality of the embeddings
        }
    }
}
es.indices.put_mapping(index=existing_index, body=embedding_mapping)

print("Bulk update the documents in the existing index")
helpers.bulk(es, actions, refresh=True)

print("Finished updating the index with embeddings!")

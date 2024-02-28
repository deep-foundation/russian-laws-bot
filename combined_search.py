# import click
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
import json
# import time
import re

es = Elasticsearch(['localhost:9200'])

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

space = ' '
dot = '.'
newline = '\n'
whitespace_regex = re.compile(r"[ \t]+")
split_regex = re.compile(r"\r?\n|\:|\;|\,|\.|\?|\!|\(|\)| против | об | за | о | при | без | не | по | под | понимается | на | с | к | в | или | и | для | либо | -[ ]?")
model_string_limit = 128 + 12 # it should work with more symbols than 128 (because of tokenization)

def split_string(string):
    string = whitespace_regex.sub(space, string).lower()
    # sentences = string.split(dot)
    # print(string)
    sentences = split_regex.split(string)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    # print(sentences)

    for sentence in sentences:
        if len(sentence) >= model_string_limit:
            print(sentence)
            raise ValueError(f"Sentence is longer than {model_string_limit}.")

    return sentences

def index_strings(index_name, strings):
    text_embeddings = model.encode(strings)

    for i, string in enumerate(strings):
        # print(string)
        text_embedding = text_embeddings[i]
        body = {'text': string, 'text_vector': text_embedding}
        res = es.index(index=index_name, body=body)
        print(f"Indexed '{string}' with id '{res['_id']}'.")

def index_string(index_name, string):
    sentences = split_string(string)
    index_strings(index_name, sentences)

documents = []
sentence_documents = {}

# preload documents for search
with open("articles-filtered-and-truncated.json", 'r', encoding='utf-8') as file:
    documents = json.load(file)

def index_prepared_string(string):
    sentences = split_string(string)
    index_strings(index_name, sentences)

def prepare_document_strings(string, document_id):
    sentences = split_string(string)
    for sentence in sentences:
        if sentence in sentence_documents:
            document_ids = sentence_documents[sentence]
            if document_id not in document_ids:
                document_ids.append(document_id)
                # sentence_documents[sentence] = document_ids
        else:
            sentence_documents[sentence] = [document_id]

def prepare_all_document_strings():
    for i, document in enumerate(documents):
        prepare_document_strings(document, i)

def index_prepared_strings(index_name):
    strings = []
    items = list(enumerate(sentence_documents.items()))
    for i, (string, document_ids) in items:
        strings.append(string)
    text_embeddings = model.encode(strings)
    for i, (string, document_ids) in items:
        text_embedding = text_embeddings[i]
        body = {'text': string, 'text_vector': text_embedding, 'document_ids': sentence_documents[string]}
        res = es.index(index=index_name, body=body)
        print(f"Indexed '{string}' with id '{res['_id']}'.")

def search_string(index_name, query):
    query_embedding = model.encode([query.strip().lower()])[0]

    body = {
        'query': {
            'script_score': {
                "query": {
                    "bool": {
                        "must": {
                            "match_all": { 'boost': 0 }
                        },
                        "should": [
                            { 
                                "match": { 
                                    "text": query
                                }
                            },
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "operator": "and"
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query
                                    }
                                }
                            }
                        ],
                    }
                },
                'script': {
                    # "source": "doc['text_vector'].size() == 0 ? 0 : cosineSimilarity(params.query_embedding, 'text_vector') + 1.0"
                    'source': "_score * 0.05 + cosineSimilarity(params.query_embedding, 'text_vector') + 1.0",
                    'params': {'query_embedding': query_embedding}
                }
            }
        }
    }
    try:
        res = es.search(index=index_name, body=body)
        return res
    except Exception as e:
        print(type(e))
        print(json.dumps(e.args, indent=4))

# def search_string(index_name, query):
#     query_embedding = model.encode([query.lower()])[0]

#     body = {
#         'query': {
#             'script_score': {
#                 "query": {
#                     "bool": {
#                         "must": {
#                             "match_all": { 'boost': 0 }
#                         },
#                         "should": [
#                             { 
#                                 "match": { 
#                                     "text": query
#                                 }
#                             },
#                             {
#                                 "match": {
#                                     "content": {
#                                         "query": query,
#                                         "operator": "and"
#                                     }
#                                 }
#                             },
#                             {
#                                 "match_phrase": {
#                                     "content": {
#                                         "query": query
#                                     }
#                                 }
#                             }
#                         ],
#                     }
#                 },
#                 'script': {
#                     # "source": "doc['text_vector'].size() == 0 ? 0 : cosineSimilarity(params.query_embedding, 'text_vector') + 1.0"
#                     'source': "_score * 0.05 + cosineSimilarity(params.query_embedding, 'text_vector') + 1.0",
#                     'params': {'query_embedding': query_embedding}
#                 }
#             }
#         }
#     }

#     try:
#         res = es.search(index=index_name, body=body)
#         click.echo("Search results:")
#         for doc in res['hits']['hits']:
#             document_ids = doc['_source']['document_ids']
#             articles = []
#             for document_id in document_ids:
#                 article_text = documents[document_id]
#                 article = article_text.strip().partition(newline)[0]
#                 articles.append(article)
#             click.echo(f"'{doc['_id']}' {doc['_score']}: \n{doc['_source']['text']}\n{articles}")
#     except Exception as e:
#         print(type(e))
#         print(json.dumps(e.args, indent=4))

def create_index(name):
    body = {
        "settings": {},
        "mappings": { "properties": { "text_vector": { "type": "dense_vector", "dims": 384 } } }
    }
    es.indices.create(index=name, body=body)

# @click.group()
# def cli():
#     pass

# @click.command()
# def create():
#     create_index('text_index')
#     click.echo(f"Index {index} is created with settings {json.dumps(body, indent=4)}")

# @click.command()
# @click.option('--string', 'string', prompt=True)
# def index(string):
#     """Index a string in Elasticsearch."""
#     index_string('text_index', string)

# @click.command(name='index_documents')
# @click.option('--path', 'path', prompt=True)
# def index_documents(path):
#     start_time = time.time()

#     with open(path, 'r', encoding='utf-8') as file:
#         documents = json.load(file)
    
#     for i, document in enumerate(documents):
#         prepare_document_strings(document, i)
    
#     index_prepared_strings('text_index')

#     document_embedding_time = time.time() - start_time
#     print(f"Documents indexed in {document_embedding_time} seconds.")

# @click.command()
# @click.option('--query', 'query', prompt=True)
# def search(query):
#     """Find strings semantically similar to the search query in Elasticsearch."""

#     start_time = time.time()
#     search_string('text_index', query)
#     seatch_time = time.time() - start_time
#     print(f"Searched in {seatch_time} seconds.")


# cli.add_command(create)
# cli.add_command(index)
# cli.add_command(index_documents)
# cli.add_command(search)



# if __name__ == "__main__":
#     cli()
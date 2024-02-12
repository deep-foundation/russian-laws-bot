[![Gitpod](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/konard/elastic-search)

# elastic-search

Model used in vector_search: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

A script in Python that loads strings to Elasticsearch Docker container and then allow user to search from CLI. Make sure Docker and python are installed on your machine.

## Install and start the Elasticsearch Docker container

```bash
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.13.1
```

## Install dependencies

```bash
pip install click 'elasticsearch<7.14.0'
pip install -U sentence-transformers
```

## Create index

```bash
python combined_search.py create
```

## Index specific string

```bash
python combined_search.py index --string "dog"
```

## Index documents array from json

```bash
python combined_search.py index_documents --path "articles-filtered-and-truncated.json"
```

## Search specific string

```bash
python combined_search.py search --query "dog"
```

## Clear elastic search index

```bash
curl -X DELETE 'http://localhost:9200/_all'
```

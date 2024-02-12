#!/bin/bash
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.13.1
pip install click 'elasticsearch<7.14.0'
pip install -U sentence-transformers
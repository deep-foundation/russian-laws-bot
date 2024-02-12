#!/bin/bash
python combined_search.py create
python combined_search.py index --string "dog"
python combined_search.py search --query "dog"
curl -X DELETE 'http://localhost:9200/_all'
echo ""

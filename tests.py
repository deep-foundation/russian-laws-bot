import unittest
import ast, json
# from my_module import add, multiply
from combined_search import create_index, search_string, documents, newline, prepare_all_document_strings, index_prepared_strings

def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

class TestMyModule(unittest.TestCase):

    def test_11(self):
        result = search_string('text_index', 'Водитель, находясь в командировке в городе Тбилиси, похитил значительное количество овощей и фруктов с целью последующей её продажи в городе Риге. При проверке автомобиля на одном из постов ГИБДД Воронежской области похищенное было обнаружено и изъято.')

        print('----------')
        all_articles = []
        for doc in result['hits']['hits']:
            document_ids = doc['_source']['document_ids']
            articles = []
            for document_id in document_ids:
                article_text = documents[document_id]
                article = article_text.strip().partition(newline)[0]
                articles.append(article)
                if not article in all_articles:  
                    all_articles.append(article)
            # print(f"'{doc['_id']}' {doc['_score']}: \n{doc['_source']['text']}\n{articles}")
        for article in all_articles:
            print(article)
        print('----------')

        # print(json.dumps(result['hits']['hits'][0], indent=4))

        # print(result.hits)

        # self.assertEqual(add(3, 4), 7)
        # self.assertEqual(add(-1, 1), 0)

    def test_12(self):
        result = search_string('text_index', 'По предварительному сговору между собой И., А., К. и Г. с целью хищения материальных ценностей проникли в вагон грузового поезда, где и были обнаружены рабочими станции. А. и Г., боясь задержания скрылись, а И. и К. в присутствии рабочих открыто похитили несколько мужских костюмов на сумму')
        
        print('----------')
        all_articles = []
        for doc in result['hits']['hits']:
            document_ids = doc['_source']['document_ids']
            articles = []
            for document_id in document_ids:
                article_text = documents[document_id]
                article = article_text.strip().partition(newline)[0]
                articles.append(article)
                if not article in all_articles:  
                    all_articles.append(article)
            # print(f"'{doc['_id']}' {doc['_score']}: \n{doc['_source']['text']}\n{articles}")
        for article in all_articles:
            print(article)
        print('----------')

    # def test_multiply(self):
    #     self.assertEqual(multiply(3, 4), 12)
    #     self.assertEqual(multiply(-1, 1), -1)

if __name__ == '__main__':
    unittest.main()
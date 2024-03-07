import unittest
import ast, json
from combined_search import create_index, search_string, documents, newline, prepare_all_document_strings, index_prepared_strings

def get_articles_from_search(search_query):
    result = search_string('text_index', search_query)
    all_articles = []
    for doc in result['hits']['hits']:
        document_ids = doc['_source']['document_ids']
        for document_id in document_ids:
            article_text = documents[document_id]
            article = article_text.strip().partition(newline)[0]
            if not article in all_articles:  
                all_articles.append(article)
    return all_articles

class TestMyModule(unittest.TestCase):

    def assert_contains_number(self, articles, number):
        contains_number = any(number in article for article in articles)
        self.assertTrue(contains_number, f"None of the articles contain the number {number}.")

    def test_11(self):
        search_query = 'Водитель, находясь в командировке в городе Тбилиси, похитил значительное количество овощей и фруктов с целью последующей её продажи в городе Риге. При проверке автомобиля на одном из постов ГИБДД Воронежской области похищенное было обнаружено и изъято.'
        all_articles = get_articles_from_search(search_query)
        print('----------')
        for article in all_articles:
            print(article)
        print('----------')

        self.assert_contains_number(all_articles, '158')

    def test_12(self):
        search_query = 'По предварительному сговору между собой И., А., К. и Г. с целью хищения материальных ценностей проникли в вагон грузового поезда, где и были обнаружены рабочими станции. А. и Г., боясь задержания скрылись, а И. и К. в присутствии рабочих открыто похитили несколько мужских костюмов на сумму'
        all_articles = get_articles_from_search(search_query)
        print('----------')
        for article in all_articles:
            print(article)
        print('----------')

        self.assert_contains_number(all_articles, '158')

if __name__ == '__main__':
    unittest.main()
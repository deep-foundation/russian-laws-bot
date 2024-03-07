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
    # print('----------')
    # for article in all_articles:
    #     print(article)
    # print('----------')
    return all_articles

class TestMyModule(unittest.TestCase):

    def assert_contains_all_numbers(self, articles, numbers):
        for number in numbers:
            with self.subTest(number=number):
                contains_number = any(number in article for article in articles)
                self.assertTrue(contains_number, f"Article {number} not found in any of the search results.")

    def test_11(self):
        search_query = 'Водитель, находясь в командировке в городе Тбилиси, похитил значительное количество овощей и фруктов с целью последующей её продажи в городе Риге. При проверке автомобиля на одном из постов ГИБДД Воронежской области похищенное было обнаружено и изъято.'
        expected_numbers = ['158']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_12(self):
        search_query = 'По предварительному сговору между собой И., А., К. и Г. с целью хищения материальных ценностей проникли в вагон грузового поезда, где и были обнаружены рабочими станции. А. и Г., боясь задержания скрылись, а И. и К. в присутствии рабочих открыто похитили несколько мужских костюмов на сумму 15 тысяч рублей.'
        expected_numbers = ['30', '158']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_13(self):
        search_query = 'Гражданин Д. летом с целью не допустить посторонних лиц в свой огород, оцепил грядку с луком проволокой и подключил её к электричеству напряжением 220 вольт. 13 июля подросток С. подошел к проволоке, которая в это время была под напряжением, коснулся её рукой и был смертельно травмирован электротоком..'
        expected_numbers = ['109']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_14(self):
        search_query = 'Н. поздно вечером возвращался домой с вечеринки. Улица была пустынна, и Н. стал опасаться нападения. Вдруг он услышал, что сзади кто-то окрикнул его и спросил, нет ли у него закурить. Решив, что подвергся нападению, Н., остановился и вытащил нож. Когда прохожий подошёл к Н. и полез в карман, как выяснилось в последствии за папиросами, Н. ни слова не говоря, ударил прошедшего гражданина ножом в левую половину груди, причинив ему смертельное ранение.'
        expected_numbers = ['108']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_15(self):
        search_query = 'Бывший работник отдела кадров областной больницы, не имея медицинского образования, стал оказывать платную медицинскую помощь на дому. Он ставил диагнозы, выписывал рецепты (печать для рецептов была изготовлена им самим), лечил отварами из трав, пользуясь справочной медицинской литературой и советами знакомых врачей. Состояние ни одного из пациентов не ухудшилось, а некоторые почувствовали улучшение.'
        expected_numbers = ['171', '233']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)
    
    def test_16(self):
        search_query = 'К., увидев лежащего возле торговой палатки пьяного, сделал вид, что помогает ему подняться, а сам в это время обыскал его карманы и вытащил кошелек с деньгами. Наблюдавший за действиями К. продавец торговой палатки заметил на руке пьяного часы, подошел к нему и в присутствии К. завладел ими.'
        expected_numbers = ['158']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_17(self):
        search_query = 'Р., вооруженный пистолетом, проник ночью в чужой огород с целью похищения картошки. Застигнутый на месте преступления хозяином сада, подкравшимся к нему на расстояние нескольких метров, Р., чтобы избежать задержания, произвел два выстрела в сторону хозяина сада, одним из которых ранил его в живот, причинив тяжкий вред здоровью.'
        expected_numbers = ['158', '111']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_18(self):
        search_query = 'Студент-вечерник возвращался домой, к нему на пустынной улице подошли двое его знакомых. Они попросили у него закурить и, получив отказ, избили студента. Тот побежал звать на помощь своих друзей. Через полчаса они нашли обидчиков и нанесли им телесные повреждения средней тяжести.'
        expected_numbers = ['112']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_19(self):
        search_query = 'Ц., достигший пятнадцатилетнего возраста, в группе лиц по предварительному сговору совершил побои (преступление, предусмотренное ст. 116 УК РФ), убийство (преступление предусмотренное ст. 105 ч. 1 УК РФ), мошенничество (преступление предусмотренное ст. 159 УК РФ), разбой (преступление предусмотренное ст. 162 УК РФ), кражу (преступление предусмотренное ст. 158 УК РФ). По всем ли преступлениям Ц. подлежит уголовной ответственности?'
        expected_numbers = ['20', '116', '159', '105', '158', '162']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

    def test_20(self):
        search_query = 'Пятнадцатилетний Э. совершил двойное убийство при отягчающих обстоятельствах. Какой максимально возможный срок наказания в виде лишения свободы может быть назначен несовершеннолетнему?'
        expected_numbers = ['88']
        articles = get_articles_from_search(search_query)
        self.assert_contains_all_numbers(articles, expected_numbers)

if __name__ == '__main__':
    unittest.main()
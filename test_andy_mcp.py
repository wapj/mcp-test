from unittest import TestCase

from andy_mcp import get_kbo_rank, get_hot_deal_info, search_google_news, find_restaurants_near_pangyo


class Test(TestCase):
    def test_get_kbo_rank(self):
        result = get_kbo_rank()
        print(type(result))
        print(result)

    def test_get_hot_deal_info(self):
        result = get_hot_deal_info()
        print(result)

    def test_search_google_news(self):
        print(search_google_news())


    def test_find_restaurants_near_pangyo(self):
        print(find_restaurants_near_pangyo("비빔밥"))

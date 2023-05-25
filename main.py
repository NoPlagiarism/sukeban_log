import json
import random
import time
import os

import httpx
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm


class SukParser:
    @staticmethod
    def get_url_to_pageable_by_num(num: int):
        if num == 1:
            return "https://log.sukeban.moe/"
        return f"https://log.sukeban.moe/page/{str(num)}/"

    @classmethod
    def get_links_list_by_len_iter(cls, total: int, min: int = 1):
        for n in range(min, total+1):
            yield cls.get_url_to_pageable_by_num(n)

    @staticmethod
    def get_data_from_pageable_row_postbox_soup(soup: Tag):
        return dict(id=int(soup.attrs['id'].split('-')[-1]),
                    link=soup.find('a').attrs.get('href'),
                    datetime=soup.find("time").attrs['datetime'],
                    categories=[x[len('category-'):] for x in soup.attrs['class'] if x.startswith('category-')])

    @staticmethod
    def get_data_from_nav_links_soup(soup: Tag):
        res = dict()
        if (prev_tag := soup.find("a", class_='prev')) is not None:
            res['prev'] = prev_tag.attrs.get('href')
        if (next_tag := soup.find("a", class_='next')) is not None:
            res['next'] = next_tag.attrs.get('href')
        res['current_page'] = int(soup.find('span', class_='current').text)
        res['max_page'] = max([int(x.text) for x in soup.find_all(class_='page-numbers') if x.text.isdigit()])
        return res

    @classmethod
    def get_all_from_pageable(cls, soup: BeautifulSoup):
        try:
            articles = soup.find_all("article", class_="post")
            articles_data = list(map(cls.get_data_from_pageable_row_postbox_soup, articles))
            nav_data = cls.get_data_from_nav_links_soup(soup.find('div', class_='nav-links'))
            return dict(articles=articles_data, nav=nav_data)
        except:
            return None
        breakpoint()


class SukMain:
    def __init__(self):
        self.sukparser = SukParser()

    def get_soup_by_url(self, url):
        page_raw = httpx.get(url)
        page_soup = BeautifulSoup(page_raw.content, 'lxml')
        return page_soup

    def get_page_links(self):
        soup = self.get_soup_by_url('https://log.sukeban.moe/')
        data = self.sukparser.get_all_from_pageable(soup)
        return tuple(self.sukparser.get_links_list_by_len_iter(data['nav']['max_page']))

    def get_all_articles_sync_while(self):
        articles = list()
        url = self.sukparser.get_url_to_pageable_by_num(1)
        while data := self.sukparser.get_all_from_pageable(self.get_soup_by_url(url)):
            articles.extend(data['articles'])
            # time.sleep(random.randint(1, 5))
        return articles

    def get_all_articles_sync_for(self):
        articles = list()
        for url in tqdm(self.get_page_links()):
            data = self.sukparser.get_all_from_pageable(self.get_soup_by_url(url))
            articles.extend(data['articles'])
            time.sleep(random.randint(1, 5))
        articles.sort(key=lambda x: x['id'], reverse=True)
        return articles


class SukNotify:
    @staticmethod
    def notify_article(article):
        pass

    @classmethod
    def notify_articles(cls, diff_articles):
        for x in diff_articles:
            cls.notify_article(x)


def main():
    suk = SukMain()
    articles = suk.get_all_articles_sync_for()
    # if os.path.exists("articles.json"):
    #     with open("articles.json", encoding="utf-8", mode="r") as f:
    #         old_articles = json.load(f)
    #     diff = list(set(articles) - set(old_articles))
    #     notif = SukNotify()
    #     notif.notify_articles(diff)
    with open("articles.json", encoding="utf-8", mode="w+") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()

import os
import yaml

import time
import random
from selenium import webdriver as wd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests



class ScrapeXueqiuHome:
    def __init__(self):
        self.url = 'https://xueqiu.com'

    @staticmethod
    def get_scrolled_source(url, scroll_times:int=10, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        driver = wd.Chrome(options=chrome_options)

        driver.get(url)

        driver.implicitly_wait(1)
        js = 'return action=document.body.scrollHeight'
        height = driver.execute_script(js)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(5)

        t1 = int(time.time())

        status = True

        num = 0
        cnt = 0
        equal_num = 0

        while status and cnt < scroll_times:
            t2 = int(time.time())
            if t2 - t1 < 30:
                cnt += 1
                n_height = driver.execute_script(js)
                equal_num = 0
                if n_height > height:
                    height = n_height
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(random.randint(1, 3))
                    t1 = int(time.time())
                elif n_height == height:
                    equal_num += 1
                    if equal_num > 5:
                        break
                    
                    try:
                        goon_btn = driver.find_element(By.LINK_TEXT, '加载更多')
                        goon_btn.click()
                        driver.implicitly_wait(0.5)
                    except:
                        continue
                
                if cnt % 10 == 0:
                    print('已经滚动了{}次'.format(cnt))

            elif num < 3:
                num += 1
                time.sleep(3)
            else:
                print('滚动条已经处在页面最下方！')
                status = False
                driver.execute_script('window.scrollTo(0, 0)')
                break

        return driver.page_source
    
    def get_article_list(self, page_source, up_limit=None):
        soup = BeautifulSoup(page_source, 'lxml')
        articles = soup.find_all('div', {'class': 'AnonymousHome_home__timeline__item_3vU'})

        article_list = []

        for content in articles[:up_limit]:
            article = {}
            article['title'] = content.h3.text
            article['outline'] = content.p.text
            article['detail_link'] = self.url + content.a.get('href')
            
            article_list.append(article)
        
        return article_list
    
    @staticmethod
    def get_article(s_web, headers, save_path):
        response = requests.get(s_web, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        article_detail = soup.find('div', {'class': 'article__bd__detail'})
        
        with open(save_path, 'a', encoding='utf-8') as f:
            
            ps = article_detail.find_all('p')
            for p in ps:
                # print(p.text)
                f.write(p.text)
                f.write('\r')
            
            f.write('\r')

    def scrape(self, time_str, scroll_times=10, details=False):
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        page_source = self.get_scrolled_source(self.url, scroll_times)
        article_list = self.get_article_list(page_source)

        save_dir_path = 'data/xueqiu_home/'
        outlines_save_path = os.path.join(save_dir_path, f'outlines_{time_str}.yaml')
        yaml.dump(article_list, open(outlines_save_path, 'w', encoding='utf-8'), allow_unicode=True)

        if details:
            details_save_path = os.path.join(save_dir_path, f'details_{time_str}.txt')
            for a_info in article_list:
                link = a_info['detail_link']
                self.get_article(link, headers, details_save_path)
                time.sleep(random.randint(1, 3))

        return outlines_save_path

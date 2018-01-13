import json
import logging
import re
import threading
from pathlib import Path
from urllib.request import urlopen

import os

from bs4 import BeautifulSoup

from src.imeiinfo.PhoneDetailsWorker import PhoneDetailsWorker

logger = logging.getLogger(__name__)


class ImeiInfoCrawler:

    def __init__(self):
        self.__base_url = 'http://www.imei.info/'
        self.__phonedatabase_base_url = 'http://www.imei.info/phonedatabase'

        self.__basic_detail = {}
        self.__parameters_detail = {}

    def crawl(self):
        links_file = Path('imei-info-links')
        if links_file.is_file():
            logging.info('links file exists, reading phone links from file')
            with open('imei-info-links') as f:
                phone_links = f.read().splitlines()
        else:
            phone_links = self.__get_all_phone_links()
            write_thread = threading.Thread(target=self.__write_phone_links(phone_links))
            write_thread.start()

        size = len(phone_links) // 2
        splitted_phone_links = [phone_links[x:x+size] for x in range(0, len(phone_links), size)]

        for index, ph_links in enumerate(splitted_phone_links):
            PhoneDetailsWorker(ph_links, index.__str__()).start()

    def __get_all_phone_links(self):
        phone_links = []

        brands = self.__get_brand_links()

        logging.info('Got ' + len(brands).__str__() + ' brands.')

        for key in brands:
            phone_links.extend(self.__get_phone_links(brands[key], []))

        logging.info('Got ' + len(phone_links).__str__() + ' phone links.')

        return phone_links

    def __get_brand_links(self):

        data = {}

        maker_page = urlopen(self.__phonedatabase_base_url + '/')
        soup = BeautifulSoup(maker_page, 'html.parser')
        phone_list_div = soup.find('div', class_='link-group')
        href_list = phone_list_div.find_all('a')

        for href in href_list:
            brand = href.contents[0]
            link = href['href']
            data[brand] = link

        return data

    def __get_phone_links(self, brand_link, links, page_no=None):
        """
        Recursively get all phone links for a brand link.
        :param brand_link:
        :param links:
        :param page_no: page number link, if brand_link contains multiple pages of phones
        :return: list containing all phone links for a brand.
        """

        if page_no is None:
            model_page_url = self.__base_url + brand_link
        else:
            model_page_url = self.__base_url + brand_link + page_no

        logging.info("Getting phone links from " + model_page_url)

        models_page = urlopen(model_page_url)
        soup = BeautifulSoup(models_page, 'html.parser')
        models = soup.find('div', id='lista')

        for model in models.findAll('a', class_='phone'):
            links.append(model['href'])

        pagers = soup.find_all('ul', class_='pager')

        if len(pagers) == 0:
            return links

        next_button_href = pagers[1].find_all('a', string='Next')

        if len(next_button_href) == 0 or next_button_href[0] is None:
            return links
        else:
            return self.__get_phone_links(brand_link, links, next_button_href[0]['href'])

    def __write_phone_links(self, phone_links):
        file = open('imei-info-links', 'w')
        for link in phone_links:
            file.write("%s\n" % link)

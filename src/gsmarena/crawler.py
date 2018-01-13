import json
import threading
from urllib.request import urlopen

import os
from bs4 import BeautifulSoup
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class Crawler:

    def __init__(self):
        self.__base_url = 'https://www.gsmarena.com/'
        self.__maker_page_url = 'https://www.gsmarena.com/makers.php3'

    def crawl(self):
        brands = {}
        phone_links = []

        links_file = Path('links')
        if links_file.is_file():
            logging.info('links file exists, reading phone links from file')
            with open('links') as f:
                phone_links = f.read().splitlines()
        else:
            phone_links = self.__get_all_phone_links()
            write_thread = threading.Thread(target=self.__write_phone_links(phone_links))
            write_thread.start()

        self.__write_phone_details(phone_links)

    def __get_all_phone_links(self):
        """
        Write the phone links in 'links' file for each brand.
        :return: the phone links list
        """
        phone_links = []

        brands = self.__get_brand_links()

        logging.info('Got ' + len(brands).__str__() + ' brands.')

        for key in brands:
            phone_links.extend(self.__get_phone_links(brands[key], []))

        logging.info('Got ' + len(phone_links).__str__() + ' phone links.')

        logging.info('Done.')

        return phone_links

    def __get_brand_links(self):
        """
        Get the brand links.
        :return: a dictionary containing the brand name and brand link
        """

        data = {}

        maker_page = urlopen(self.__maker_page_url)
        soup = BeautifulSoup(maker_page, 'html.parser')
        div_table = soup.find('div', class_='st-text')
        table = div_table.find('table')
        
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            for col in cols:
                href = col.find('a', href=True)
                brand = href.contents[0]
                link = href['href']
                data[brand] = link
        return data

    def __get_phone_links(self, brand_link, links):
        """
        Recursively get all phone links for a brand link.
        :param brand_link:
        :param links:
        :return: list containing all phone links for a brand.
        """
        logging.info("Getting phone links from " + brand_link)

        model_page_url = self.__base_url + brand_link
        models_page = urlopen(model_page_url)
        soup = BeautifulSoup(models_page, 'html.parser')
        models = soup.find('div', class_='makers')

        for model in models.findAll('li'):
            links.append(model.find('a', href=True)['href'])

        next_button = soup.find('a', class_='pages-next')

        if next_button is None:
            return links

        if 'disabled' in next_button['class']:
            return links
        else:
            return self.__get_phone_links(next_button['href'], links)

    def __write_phone_details(self, phone_links):
        logging.info('Writing phone details.')

        for link in phone_links:
            file_name = link.split('.')

            file_path = 'phone/' + file_name[0]
            file_path = file_path.replace('*', '_')

            if os.path.exists(file_path):
                continue

            phone_detail = self.__get_phone_details(link)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file = open(file_path, 'w')

            file.write(json.dumps(phone_detail))

        logging.info('Done.')

    def __get_phone_details(self, phone_link):
        phone_details = {}

        phone_page_url = self.__base_url + phone_link
        phone_page = urlopen(phone_page_url)
        soup = BeautifulSoup(phone_page, 'html5lib')

        name = soup.find('h1', class_='specs-phone-name-title').text
        phone_details['Name'] = name

        specs_list = soup.find('div', attrs={'id':'specs-list'})
        specs_list_tables = specs_list.find_all('table')

        for specs_list_table in specs_list_tables:
            rows = specs_list_table.find_all('tr')
            attribute = rows[0].find('th').string

            phone_details[attribute] = []

            for i in range(1, len(rows)):
                cols = rows[i].find_all('td')
                for col in cols:
                    phone_details[attribute].append(col.text)

        return phone_details

    def __write_phone_links(self, phone_links):
        file = open('links', 'w')
        for link in phone_links:
            file.write("%s\n" % link)

import json
import logging
import re
import threading
from urllib.error import HTTPError
from urllib.request import urlopen

import os

import sys
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PhoneDetailsWorker(threading.Thread):

    def __init__(self, phone_links, thread_name):
        super().__init__(name=thread_name)

        self.__phone_links = phone_links

        self.__base_url = 'http://www.imei.info/'
        self.__phone_details_folder = 'phone/imei-info/'

    def run(self):
        self.__write_phone_details()

    def __write_phone_details(self):
        logging.info('Writing phone details.')

        for link in self.__phone_links:
            file_name = link.split('/')
            file_path = self.__phone_details_folder + file_name[2]
            file_path = file_path.replace('*', '_')
            if os.path.exists(file_path):
                continue

            phone_detail = None

            for i in range(1, 10):
                try:
                    phone_detail = self.__get_phone_details(link)
                except HTTPError as e:
                    logging.error(e)
                    continue
                else:
                    break

            if phone_detail is None:
                sys.exit('Could not get phone detail for ' + link)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file = open(file_path, 'w')
            file.write(json.dumps(phone_detail))

        logging.info('Done.')

    def __get_phone_details(self, phone_link):

        logging.info('Getting phone details from ' + phone_link)

        phone_details = {}

        phone_page_url = self.__base_url + phone_link
        phone_page = urlopen(phone_page_url)
        soup = BeautifulSoup(phone_page, 'html.parser')

        self.__basic_detail = {}
        self.__parameters_detail = {}

        basic_detail_thread = threading.Thread(target=self.__get_basic_details, args=(soup,), name='basic'+self.getName())
        parameters_detail_thread = threading.Thread(target=self.__get_parameters_details, args=(soup,), name='params'+self.getName())

        basic_detail_thread.start()
        parameters_detail_thread.start()

        basic_detail_thread.join()
        parameters_detail_thread.join()

        phone_details['basic'] = self.__basic_detail
        phone_details['parameters'] = self.__parameters_detail

        return phone_details

    def __get_basic_details(self, soup):

        basic_information_div = soup.find('div', attrs={'id': 'basic'})
        basic_table = basic_information_div.find('table', class_='table')

        rows = basic_table.find_all('tr')
        for i in range(1, len(rows)):
            cols = rows[i].find_all('td')

            value = cols[1].text

            checkboxes = cols[1].find_all('img')
            if len(checkboxes) > 0:
                value += ' ' + self.__extract_text_from_img(checkboxes[0])

            self.__basic_detail[cols[0].text] = re.sub('\s+', ' ', value)

    def __get_parameters_details(self, soup):

        parameters_information_div = soup.find('div', attrs={'id': 'parameters'})
        parameters_tables = parameters_information_div.find_all('table')

        for parameter_table in parameters_tables:
            rows = parameter_table.find_all('tr')

            for i in range(1, len(rows)):
                cols = rows[i].find_all('td')

                value = cols[1].text

                checkboxes = cols[1].find_all('img')
                if len(checkboxes) > 0:
                    value += ' ' + self.__extract_text_from_img(checkboxes[0])

                self.__parameters_detail[cols[0].text] = re.sub('\s+', ' ', value)

    def __extract_text_from_img(self, img):
        checkbox_value = img.get('alt', '')
        if 'YES' in checkbox_value:
            return 'YES'
        elif 'NO' in checkbox_value:
            return 'NO'
        else:
            return ''

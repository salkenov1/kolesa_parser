import csv
import os
import threading
import multiprocessing

from re import sub
from time import sleep

from ..parser import Parser
from .schemas import KolesaData
from conf import create_logger

from typing import List, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = create_logger('kolesa')

class KolesaParser(Parser):

    def __init__(self, car_brand: str) -> None:
        super().__init__()
        self.company_name = 'kolesa'
        self.car_brand = car_brand
        self.dir_path = f'data/{self.company_name}'
        self.data_path = f"{self.dir_path}/{car_brand}.csv"

        if not os.path.exists(self.dir_path):
            os.mkdir(self.dir_path)

        options = Options()
        options.headless = True
        self.webdriver = webdriver.Chrome(options=options)
        self.webdriver.set_page_load_timeout(10)
        
        self.timeout = 5
        self.base_url = "https://kolesa.kz/"
        self.car_pages_selector = ".pager>ul>li:last-child"
        self.car_list_selector = "div.a-list"
        self.car_list_item_selector = "div.a-list__item"
        self.car_list_item_url_selector = "div.a-card__info a.a-card__link"
        self.offer_spec_selector = "div.offer__sidebar-info"

    def waitfor(self, selector: str)->None:
        WebDriverWait(self.webdriver, self.timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, selector)
            )
        )

    def stop_loading(self)->None:
        self.webdriver.execute_script("window.stop();")

    def find(self, selector: str)->Union[WebElement, None]:
        return self.webdriver.find_element(By.CSS_SELECTOR, selector)
    
    def find_all(self, selector: str)->List[WebElement]:
        return self.webdriver.find_elements(By.CSS_SELECTOR, selector)

    def find_offers_pages(self)->int:
        try:
            pages = self.find(self.car_pages_selector)
            return int(pages.text)
        except NoSuchElementException:
            logger.warning(f"Only 1 page for {self.car_brand}")
            return 1
    
    def find_all_offers(self)->List[WebElement]:
        return self.find_all(self.car_list_item_url_selector)


    def get(self, url: str, selector: str = None)->None:
        if url.startswith('/'):
            url = url[1:]
        
        if not url.startswith(self.base_url):
            url = self.base_url + url 
        
        logger.debug(f"Open {url=}")
        self.webdriver.get(url)

        if selector:
            self.waitfor(selector)
        
        logger.debug(f"Loaded {url=}")
    
    def get_car_list(self, page: int = None)->None:
        url = ''
        if not page:
            url = f"cars/{self.car_brand}"
        else:
            url = f"cars/{self.car_brand}?page={page}"
        
        while True:
            try:
                self.get(url, self.car_list_item_url_selector)
            except TimeoutException:
                logger.warning(f"Too long {url=}")
                self.stop_loading()
            
            try:
                offers = self.find_all_offers()
                if len(offers) > 0:
                    break
            except NoSuchElementException:
                logger.warning("Could not find offers")
                break
    
    def get_offer(self, url: str)->None:
        while True:
            try:
                self.get(url, self.offer_spec_selector)
            except TimeoutException:
                logger.warning(f"Too long {url=}")
                self.stop_loading()

            specs = self.find_all(self.offer_spec_selector)
            if specs:
                break


    @staticmethod
    def get_car_info(url: str, car_brand: str, barrier: threading.Barrier)->None:
        logger.info(f"Start scraping {car_brand} [{url}]")
        offer_parser = KolesaParser(car_brand)

        offer_parser.get_offer(url)
        logger.info(f"{car_brand} [{url}] opened")

        data = {
            'company': offer_parser.company_name,
            'url': url,
        }
        try:
            data['brand'] = offer_parser.find("[itemprop=brand]").text
        except NoSuchElementException:
            data['brand'] = ''

        try:
            data['name'] = offer_parser.find("[itemprop=name]").text
        except NoSuchElementException:
            data['name'] = ''
        
        try:
            data['year'] = int(sub("-?[^\d\.]",'',offer_parser.find("span.year").text))
        except NoSuchElementException:
            data['year'] = ''
        
        try:
            data['price'] = int(sub("-?[^\d\.]",'',offer_parser.find("div.offer__price").text))
        except NoSuchElementException:
            data['price'] = ''
        
        try:
            data['description'] = offer_parser.find("div.offer__description>.text").text.replace('\n', ' | ').replace(',', ' _ ')
        except NoSuchElementException:
            data['description'] = ''

        car_specs = offer_parser.find_all('dl')
        logger.debug(f"Total: car_specs={len(car_specs)}")
        for cs in car_specs:
            try:
                field, val = cs.text.split('\n')
                data[field] = val
            except Exception:
                continue

        if os.path.exists(offer_parser.data_path):
            with open(offer_parser.data_path, 'a') as f:
                data = KolesaData(**data)
                fields_name = list(data.dict().keys())

                writer = csv.DictWriter(f, fieldnames=fields_name)
                writer.writerow(data.dict())
        else:
            with open(offer_parser.data_path, 'w') as f:
                data = KolesaData(**data)
                fields_name = list(data.dict().keys())

                writer = csv.DictWriter(f, fieldnames=fields_name)
                writer.writeheader()
                writer.writerow(data.dict())
        

        logger.info(f"End scraping {car_brand} [{url}]")
        del offer_parser
        barrier.wait()


    def __del__(self):
        self.webdriver.close()


def start_sraping(car_brand: str):
    logger.info(f"Create Kolesa parser for brand {car_brand}")
    kolesa = KolesaParser(car_brand)

    logger.info(f"Get offers for {car_brand}")
    kolesa.get_car_list()

    pages = kolesa.find_offers_pages()
    logger.info(f"Total {pages} pages for brand {car_brand}")


    WORKERS = 5
    logger.debug(f"Total: {WORKERS=}")

    page = 1
    while True:
        logger.info(f"Start scraping {car_brand} on page {page}")
        
        offers = kolesa.find_all_offers()
        logger.info(f"Scraping {len(offers)} offers")

        pack = 0
        while len(offers) > 0:

            threads: List[threading.Thread] = []
            total_threads = WORKERS

            _offers= offers[:WORKERS]
            if len(_offers) != WORKERS:
                total_threads = len(offers)

            logger.info(f"Start scraping offers [{pack+1}:{pack+total_threads}]")
            pack += total_threads
            
            offers = offers[total_threads:]
            logger.debug(f"_offers={len(_offers)} offers={len(offers)}")

            barrier = threading.Barrier(total_threads)
            logger.debug(f"Create Barrier with {total_threads=}")
            
            for offer in _offers:
                offer_url = offer.get_attribute('href')

                t = threading.Thread(
                    name=f"{car_brand} [{offer_url}]",
                    target=KolesaParser.get_car_info, 
                    args=(offer_url, car_brand, barrier), 
                    kwargs={}
                )
                t.start()

                threads.append(t)
            else:
                for t in threads:
                    t.join()
                        
        sleep(90)
        page += 1
        if page > pages:
            break

        kolesa.get_car_list(page)
        pages = kolesa.find_offers_pages()

    del kolesa
    logger.info(f"Delete Kolesa parser for brand {car_brand}")
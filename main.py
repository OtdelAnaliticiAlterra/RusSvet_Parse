import aiohttp
import asyncio
from selectolax.parser import HTMLParser
import time
import pandas as pd
import openpyxl
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.headless = True

from dotenv import load_dotenv, find_dotenv
from telegram_bot_logger import TgLogger
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(find_dotenv())

CHATS_IDS = '\\\\TG-Storage01\\Аналитический отдел\\Проекты\\Python\\chats_ids.csv'

logger = TgLogger(
    name='Парсинг_Сатурн',
    token=os.environ.get('LOGGER_BOT_TOKEN'),
    chats_ids_filename=CHATS_IDS,
)

async def get_response(session, url, retries=3):
    """Получение ответа от сервера с обработкой ошибок"""
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=50) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientTimeout, aiohttp.ClientError) as e:
            print(f"Network error occurred: {e}. Attempt {attempt + 1} of {retries}. Retrying...")
            await asyncio.sleep(2)
        except asyncio.TimeoutError:
            print(f"Timeout error occurred for URL: {url}. Attempt {attempt + 1} of {retries}. Retrying...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"An unexpected error occurred while requesting {url}: {e}")
            break
    return None

driver = webdriver.Chrome(options=options)

driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    'userAgent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"})


driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
    'headers': {

    "Referer": "https://rs24.ru/",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ru,en;q=0.9"}

})




async def parse_categories():
    """Парсинг категорий товаров"""
    catdat = []
    cat_links = []
    driver.get("https://rs24.ru/search.htm?c=5")
    time.sleep(3)
    response_text = driver.page_source
    if response_text is not None:
        parser = HTMLParser(response_text)

        sfacet = parser.css("div.subcat-facet")
        sfacet = sfacet[2::3]
        for el in sfacet:
            for cat in el.css("span.category-head"):
               catdat.append(cat.attributes.get("data-id"))

        cat_links = [f"https://rs24.ru/search.htm?c={i}" for i in catdat]

        return cat_links
    return []


async def parse_products(session):
    """Парсинг информации о товарах"""
    supply_path = await parse_categories()
    good_links = []
    product_links = []
    article_list = []
    name_list = []
    price_list = []

    # Счетчик запросов
    request_count = 0

    for elem in supply_path:
        print(f"elem = {elem}")
        request_count +=1
        driver.get(elem)

        response_text = driver.page_source

        if response_text is not None:
            parser = HTMLParser(response_text)
            if parser.css("a.pagination-item-last"):
                page = [item.text() for item in parser.css("a.pagination-item-last")]


                for num in range(1,int(page[0])+1):

                    driver.get(f"{elem}&p={num}")
                    time.sleep(4)
                    response_text = driver.page_source
                    parser = HTMLParser(response_text)
                    for prod in parser.css("div.single-item-block"):
                        for stat,oostock in zip(prod.css("div.retail"),prod.css("div.item-block")):
                            if stat.text() == "По запросу" or oostock.css("div.out-of-stock-status"):

                                pass
                            else:
                                for item in prod.css('div.item-name a'):

                                    good_links.append("https://rs24.ru" + item.attributes.get("href"))

                                for item in prod.css('div.single-item-img img'):

                                    name_list.append(item.attributes.get("alt"))

                                for art in prod.css("div.item-block div.item-code"):

                                    article_list.append(art.text())
                                for pr in prod.css("div.retail"):

                                    price_list.append(float(pr.text().replace("&nbsp;","")[:-1].replace("\xa0","")))
    #
    #
    return good_links, article_list, name_list, price_list


async def main():
    start = time.time()
    async with aiohttp.ClientSession() as session:
         product_links, article_list, name_list, price_list = await parse_products(session)

    #
    new_slovar = {
            "Код конкурента":  "01-01028082",
            "Конкурент": "Русский свет",
            "Артикул": article_list,
            "Наименование": name_list,
            "Вид цены": "Цена на сайте",
            "Цена": price_list,
            "Ссылка": product_links
        }
    df = pd.DataFrame(new_slovar)
    file_path = "\\tg-storage01\\Аналитический отдел\\Проекты\\Python\\Парсинг конкрунтов\\Выгрузки\\Русский свет\\Выгрузка цен.xlsx"
    # file_path = "C:\\Users\\Admin\\PycharmProjects\\Парсер Руссвет"
    if os.path.exists(file_path):
        os.remove(file_path)
        df.to_excel(file_path, sheet_name="Лист 1", index=False)
        print("Парсинг выполнен")
    end = time.time()
    print("Время", (end - start))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        raise e

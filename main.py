import aiohttp
import asyncio
from selectolax.parser import HTMLParser
import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()

from dotenv import load_dotenv, find_dotenv
from telegram_bot_logger import TgLogger
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(find_dotenv())

CHATS_IDS = '\\\\TG-Storage01\\Аналитический отдел\\Проекты\\Python\\chats_ids.csv'

logger = TgLogger(
    name='Парсинг_РусСвет',
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


# driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
#     'headers': {
#
#     "Referer": "https://rs24.ru/",
#     "Accept-Encoding": "gzip, deflate, br, zstd",
#     "Accept-Language": "ru,en;q=0.9"}
#
# })


async def parse_categories():
    """Парсинг категорий товаров"""
    catdat = []
    cat_links = []
    sfacet = ["https://rs24.ru/search.htm?c=18&ps=16", "https://rs24.ru/search.htm?c=22&ps=16",
              "https://rs24.ru/search.htm?c=75&ps=16", "https://rs24.ru/search.htm?c=78&ps=16",
              "https://rs24.ru/search.htm?c=80&ps=16",
              "https://rs24.ru/search.htm?c=2888&ps=16", "https://rs24.ru/search.htm?c=146&ps=16",
              "https://rs24.ru/search.htm?c=194&ps=16", "https://rs24.ru/search.htm?c=30&ps=16"]

    print(sfacet)
    datass = []
    results = []
    for el in sfacet:
        print(el)
        driver.get(el)

        time.sleep(5)
        response_text = driver.page_source

        # button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.ID, "infoBannerConfirmBtn"))
        # )
        #
        # # Нажимаем на кнопку
        # button.click()
        parser = HTMLParser(response_text)

        last_level_items = parser.css(
            'div.catalog-header__categories a.categories__item')

        # Сбор данных

        for item in last_level_items:
            print(item.html)
            data_id = item.attributes.get("data-id")
            results.append(data_id)

            # datass.append(cat.attributes.get('data-id'))
            # for el in cat.css("span.category-head"):
            #     if el.attributes.get("data-id") in links_index:

        # for cat in parser.css("span.category-head"):
        #    catdat.append(cat.attributes.get("data-id"))

    #
    cat_links = [f"https://rs24.ru/search.htm?c={i}&ps=100" for i in set(results)]
    print(cat_links)
    return cat_links


async def parse_products(session):
    """Парсинг информации о товарах"""
    supply_path = await parse_categories()
    print(f"supply_path:{supply_path}")
    print(len(supply_path))
    supply_path = set(supply_path)
    print(len(supply_path))

    good_links = []
    product_links = []
    article_list = []
    name_list = []
    price_list = []

    for elem in supply_path:
        print(f"elem = {elem}")
        time.sleep(10)
        driver.get(elem)

        # button = WebDriverWait(driver, 100).until(
        #     EC.element_to_be_clickable((By.ID, "infoBannerConfirmBtn"))
        # )
        #
        # # Нажимаем на кнопку
        # button.click()

        # single_item_block = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.single-item-block"))
        # )
        time.sleep(10)

        response_text = driver.page_source

        if response_text is not None:
            parser = HTMLParser(response_text)
            # if not parser.css("a.page-selection__pages-total"):
            #     print("no way")
            if parser.css("div.page-selection__pages-total"):
                page = [item.text().split(" ")[1] for item in parser.css("div.page-selection__pages-total")]
                print(f"page: {page}")
                for num in range(1, int(page[0]) + 1):
                    print(f"{elem}&p={num}")
                    time.sleep(8)
                    driver.get(f"{elem}&p={num}")
                    time.sleep(7)
                    # single_item_block = WebDriverWait(driver, 10).until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.single-item-block"))
                    # )
                    response_text = driver.page_source
                    parser = HTMLParser(response_text)

                    for prod in parser.css("div.search-results__item.js-product.search-results__item_view_list"):

                        if prod.css("div.analytical-category-label.analytical-category-label__out-of-stock"):

                            continue
                        else:
                            item = prod.css_first('div.item-name a')
                            print(f"goodlibks  {'https://rs24.ru' + item.attributes.get('href')}")

                            good_links.append("https://rs24.ru" + item.attributes.get("href"))
                            print(item.text().split("\n")[1].split("\t\t\t\t\t\t")[1])
                            name_list.append(item.text().split("\n")[1].split("\t\t\t\t\t\t")[1])

                            # item = prod.css_first('div.single-item-img img')
                            # print(f"nameLinks {item.attributes.get('alt')}")
                            # name_list.append(item.attributes.get("alt"))

                            art = prod.css_first("div.item-characteristic-value")
                            print(f"artlist {art.text()}")
                            article_list.append(art.text())
                            pr = prod.css_first("span.price-value.js-product-price")
                            print(f"piar {pr.text()}")
                            if "По запросу" in pr.text():
                                print("no way")
                                price_list.append(1000)
                            else:
                                price_list.append(pr.text().replace("&nbsp;", "")[:-1].replace("\xa0", ""))
        else:
            print("no html")
    return good_links, article_list, name_list, price_list


async def main():
    start = time.time()
    async with aiohttp.ClientSession() as session:
        # await parse_categories()
        product_links, article_list, name_list, price_list = await parse_products(session)

        combined_tuples = list(zip(product_links, article_list, name_list, price_list))
        sct = set(combined_tuples)
        # Удаление повторяющихся кортежей с помощью set
        product_links = [t[0] for t in sct]
        article_list = [t[1].strip() for t in sct]
        name_list = [t[2] for t in sct]
        price_list = [t[3] for t in sct]

        #
        print(len(product_links))
        print(len(article_list))
        print(len(name_list))
        print(len(price_list))

        new_slovar = {
            "Код конкурента": "01-01075397",
            "Конкурент": "Русский свет",
            "Артикул": article_list,
            "Наименование": name_list,
            "Вид цены": "Цена РусскийСветБарнаул",
            "Цена": price_list,
            "Ссылка": product_links
        }
        df = pd.DataFrame(new_slovar)
        file_path = "\\\\tg-storage01\\Аналитический отдел\\Проекты\\Python\\Парсинг конкрунтов\\Выгрузки\\Русский свет\\Выгрузка цен.xlsx"

        df.to_excel(file_path, sheet_name="Данные", index=False)
        print("Парсинг выполнен")
    end = time.time()
    print("Время", (end - start))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(e)
        raise e

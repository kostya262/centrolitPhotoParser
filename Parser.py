import difflib
import pandas as pd
import requests
import csv
from consts import *
from bs4 import BeautifulSoup


def load_data():
    data = []
    try:
        # source: https://realpython.com/python-csv/
        csv_file = open(DATA_FILE_NAME)
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                data.append(row[0:3:2])
                line_count += 1
        print(f'Обработано {line_count} строк')
    except FileNotFoundError:
        print(f'Файл данных с именем \"{DATA_FILE_NAME}\" не найден')
    return data


# source: https://antonz.ru/difflib-ratio/
def similarity(s1, s2):
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


class Parser:
    def __init__(self, ftp):
        print("Инициализация парсера")
        self.ftp = ftp
        self.data = load_data()
        self.images_count = 0
        self.already_download_images = []

    def start(self, index=9, end_index=-1):
        count_clear_page = 0
        while count_clear_page != 3 and (end_index == -1 or index <= end_index):
            links = self.category_parse(index)
            index += 1
            if links is None:
                count_clear_page += 1
            else:
                count_clear_page = 0
                for link in links:
                    self.product_parse(link)

        print("Было использованно", self.images_count, "изображений")
        print("Сохраняю данные в Excel")
        # source: https://coderoad.ru/55508303/Как-записать-список-списков-в-excel-с-помощью-python
        df = pd.DataFrame(self.data)
        writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Товары', index=False)
        writer.save()
        print("Данные успешно сохранены в файл output.xlsx")

    def category_parse(self, index):
        html = requests.get(CATEGORY_PAGE_URL + str(index)).text
        soup = BeautifulSoup(html, 'html.parser')
        elements = soup.find(class_="jshop_list_product")
        if elements is None:
            return
        elements = elements.find(class_="jshop")
        if elements is None:
            return
        elements = elements.find_all(class_="block_product")
        links = []
        for element in elements:
            link = element.find(class_="product_link").get("href")
            links.append(link)
        return links

    def product_parse(self, link):
        html = requests.get(DOMAIN_URL + link).text
        soup = BeautifulSoup(html, 'html.parser')
        product = soup.find(class_="jshop productfull")
        gost = ""
        if product is None:
            return

        block_range = product.find(class_="range")
        if block_range is None:
            return
        image_block = block_range.find(class_="full_img_block")
        if image_block is None:
            return
        image = image_block.span.a.get("href")
        title = block_range.find("h2").text

        description = product.find(class_="jshop_prod_description")
        if description is not None:
            elements = description.find_all("p")
            for element in elements:
                if "ГОСТ" in element.text:
                    gost = element.text

        must_similar_percent = 0
        index_must_similar = 0
        for index in range(len(self.data)):
            name, weight = self.data[index][0], self.data[index][1]
            now_similarity = similarity(name, title)
            if now_similarity > must_similar_percent:
                must_similar_percent = now_similarity
                index_must_similar = index
            if now_similarity > 0.4:
                photo_name = title.replace(" ", "_").replace("/", "_") + ".jpg"
                if len(self.data[index]) == 2:
                    if photo_name not in self.already_download_images:
                        self.save_photo(image, photo_name)
                        self.already_download_images.append(photo_name)
                    self.images_count += 1
                    self.data[index].append(gost)
                    self.data[index].append(OUR_DOMAIN_URL + "/" + photo_name)
                    self.data[index].append(str(must_similar_percent))
                elif float(self.data[index][-1]) < now_similarity:
                    self.data[index][2] = gost
                    self.data[index][3] = OUR_DOMAIN_URL + "/" + photo_name
                    self.data[index][4] = str(must_similar_percent)
        if must_similar_percent > 0.2:
            photo_name = title.replace(" ", "_").replace("/", "_") + ".jpg"
            if len(self.data[index_must_similar]) == 2:
                if photo_name not in self.already_download_images:
                    self.save_photo(image, photo_name)
                    self.already_download_images.append(photo_name)
                self.images_count += 1
                self.data[index_must_similar].append(gost)
                self.data[index_must_similar].append(OUR_DOMAIN_URL + "/" + photo_name)
                self.data[index_must_similar].append(str(must_similar_percent))
            elif float(self.data[index_must_similar][-1]) < must_similar_percent:
                self.data[index_must_similar][2] = gost
                self.data[index_must_similar][3] = OUR_DOMAIN_URL + "/" + photo_name
                self.data[index_must_similar][4] = str(must_similar_percent)

    def save_photo(self, url, photo_name):
        response = requests.get(url)
        with open("./" + TMP_FOLDER_NAME + "/" + TMP_FILE_NAME, 'wb') as fd:
            for chunk in response.iter_content():
                fd.write(chunk)
        tmp_file = open("./" + TMP_FOLDER_NAME + "/" + TMP_FILE_NAME, 'rb')
        self.ftp.storbinary('STOR ' + photo_name, tmp_file)

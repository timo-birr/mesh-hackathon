import json
import os

import pandas as pd

str_products = "products"
str_media = "Media"
str_product_id = "ProductId"
str_product_picture = "Product Picture"
str_application_picture = "Application Picture"
str_url = "Url"
str_type = "Type"


def read_json(path):
    with open(path, 'r') as infile:
        return json.load(infile)


def get_category_data(path):
    category_data_file = [i for i in os.listdir(path) if i.endswith(".json")][0]
    category_data_path = os.path.join(path, category_data_file)
    return read_json(category_data_path)


def recursive(path, dict_list):
    if str_products in os.listdir(path):
        print("In products")
        product_folder_path = os.path.join(path, str_products)
        for product_file in os.listdir(product_folder_path):
            product_file_path = os.path.join(product_folder_path, product_file)
            product_data = read_json(product_file_path)
            # print(product_data)
            product_id = product_data[str_product_id]
            if str_media in product_data:
                media_data = product_data[str_media]
                url_list = [d[str_url] for d in media_data if str_product_picture in d[str_type]]
                if not url_list:
                    url_list = [d[str_url] for d in media_data if str_application_picture in d[str_type]]
                url = min(url_list, key=len)
                dict_list.append({str_product_id: product_id, str_url: url})
            else:
                dict_list.append({str_product_id: product_id, str_url: ""})
    else:
        for folder in os.listdir(path):
            folder_path = os.path.join(path, folder)
            if os.path.isdir(folder_path):
                recursive(folder_path, dict_list)


if __name__ == "__main__":
    raw_data_path = "../raw_data"
    dict_list_main = []
    for category_main in os.listdir(raw_data_path):
        category_main_path = os.path.join(raw_data_path, category_main)
        if os.path.isdir(category_main_path):
            recursive(category_main_path, dict_list_main)
    df = pd.DataFrame(dict_list_main)
    df.to_csv('../product_id_url.csv')

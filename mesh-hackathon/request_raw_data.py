import json
import os

import requests


url_all_categories = "https://fischer-sitecore-cat.smartcommerce.se/v1/categories/FIWE/de_DE"
url_format_category = "https://fischer-sitecore-cat.smartcommerce.se/v1/categories/{category}/FIWE/de_DE"
url_format_product = "https://fischer-sitecore-cat.smartcommerce.se/v1/products/{product}/FIWE/de_DE"

str_child_categories = "ChildCategories"
str_products_ids = "ProductIds"


def get_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None


def join_path_makedirs(path, folder_name):
    new_path = os.path.join(path, folder_name)
    os.makedirs(new_path, exist_ok=True)
    return new_path


def save_json(path, file_name, data):
    file_path = os.path.join(path, f"{file_name}.json")
    with open(file_path, "w") as outfile:
        json.dump(data, outfile)


def recursive(data, path):
    if str_child_categories in data:
        list_child_categories = data[str_child_categories]
        for category in list_child_categories:
            print("ChildCategories:", category)
            path_child_category = join_path_makedirs(path, category)
            data_category = get_data(url_format_category.format(category=category))
            save_json(path_child_category, category, data_category)
            recursive(data_category, path_child_category)
    elif str_products_ids in data:
        list_product_ids = data[str_products_ids]
        product_path = join_path_makedirs(path, "products")
        for product in list_product_ids:
            print("ProductId:", product)
            data_product = get_data(url_format_product.format(product=product))
            save_json(product_path, product, data_product)
    else:
        print("WTF")


if __name__ == "__main__":
    data_categories = get_data(url_all_categories)
    category_ids = data_categories["CategoryIds"]
    path_data = "../raw_data"
    for category_main in category_ids:
        print("Main category:", category_main)
        path_main_category = join_path_makedirs(path_data, category_main)
        data_category_main = get_data(url_format_category.format(category=category_main))
        save_json(path_main_category, category_main, data_category_main)
        recursive(data_category_main, path_main_category)

import json
import os
import re

str_products = "products"
str_test_list = "TextList"
str_attributes = "Attributes"
str_product_id = "ProductId"
str_product_name = "ProductName"
str_category_name = "CategoryName"


def read_json(path):
    with open(path, 'r') as infile:
        return json.load(infile)


def get_category_data(path):
    category_data_file = [i for i in os.listdir(path) if i.endswith(".json")][0]
    category_data_path = os.path.join(path, category_data_file)
    return read_json(category_data_path)


def clean_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def process_value(d):
    if 'Value' in d:
        return d['Value']
    elif 'ValueList' in d:
        return d['ValueList']


def recursive(path, parent_categories):
    parent_categories_copy = parent_categories.copy()
    parent_categories_copy.append(get_category_data(path))
    if str_products in os.listdir(path):
        print("In products")
        product_folder_path = os.path.join(path, str_products)
        for product_file in os.listdir(product_folder_path):
            product_file_path = os.path.join(product_folder_path, product_file)
            product_data = read_json(product_file_path)

            product_id = product_data[str_product_id]
            product_name = product_data[str_product_name] if str_product_name in product_data else ""
            test_list_values = [clean_html_tags(d['Value']) for d in product_data[str_test_list]]
            if str_attributes in product_data:
                attributes_list = [f"{d['AttributeName']}: {process_value(d)} {d['Unit']}" if "Unit" in d
                                   else f"{d['AttributeName']}: {process_value(d)}"
                                   for d in product_data[str_attributes]]
                attributes_list = [clean_html_tags(text) for text in attributes_list]
            else:
                attributes_list = []
            category_name_list = [f"Das Produkt ist von der Kategorie {category_data[str_category_name]}"
                                  for category_data in parent_categories_copy]
            text_category = "\n".join(category_name_list)

            test_list_text = "\n".join(test_list_values)
            attributes_text = "\n".join(attributes_list)
            product_text = f"Diese Datei beschreibt das Produkt {product_name} mit der ID {product_id}\n" \
                           f"{test_list_text}\n{attributes_text}\n{text_category}"
            with open(f"../data_processed/{product_id}.txt", "w") as f:
                f.write(product_text)
    else:
        for folder in os.listdir(path):
            folder_path = os.path.join(path, folder)
            if os.path.isdir(folder_path):
                print(folder)
                recursive(folder_path, parent_categories_copy)


if __name__ == "__main__":
    raw_data_path = "../raw_data"
    os.makedirs("../data_processed/", exist_ok=True)
    for category_main in os.listdir(raw_data_path):
        category_main_path = os.path.join(raw_data_path, category_main)
        if os.path.isdir(category_main_path):
            recursive(category_main_path, [])

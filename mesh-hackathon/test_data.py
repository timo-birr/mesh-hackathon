import requests


def get_data(url):
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None


url_all_products = "https://fischer-sitecore-cat.smartcommerce.se/v1/products/FIWE/de_DE"
url_all_categories = "https://fischer-sitecore-cat.smartcommerce.se/v1/categories/FIWE/de_DE"
url_bsp_product = "https://fischer-sitecore-cat.smartcommerce.se/v1/products/050106/FIWE/de_DE"
# url = "https://fischer-sitecore-cat.smartcommerce.se/v1/categories/1001341450/FIWE/de_DE"

print(len(get_data(url_all_products)["ProductIdst"]))

"""
data_all_categories = get_data(url_all_categories)
for categorie in ["1001341448"]: #data_all_categories["CategoryIds"]:
    url_categorie = f"https://fischer-sitecore-cat.smartcommerce.se/v1/categories/{categorie}/FIWE/de_DE"
    data_categorie = get_data(url_categorie)
    for key, value in data_categorie.items():
        print(key, value)
        print()
    #print(data_categorie["CategoryName"])


data_bsp_product = get_data(url_bsp_product)
for categorie in data_bsp_product["CategoryPath"]:
    url_categorie = f"https://fischer-sitecore-cat.smartcommerce.se/v1/categories/{categorie}/FIWE/de_DE"
    data_categorie = get_data(url_categorie)
    print(data_categorie["CategoryName"])
"""

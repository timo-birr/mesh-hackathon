import requests


def load_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f'Error: {response.status_code}')
        return None

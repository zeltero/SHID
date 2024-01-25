import requests
import time
import os
import re
from colored_print import log



# Utwórz sesję
session = requests.Session()



# Funkcja do czyszczenia nazwy produktu
def clean_product_name(name):
    name = re.sub(r'\W+', '_', name)  # Zastąp wszystkie znaki specjalne i spacje podkreśleniem
    name = name.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')  # Zastąp polskie znaki ich podstawowymi odpowiednikami
    return name

# Słownik do przechowywania informacji o produktach
product_info = {}

# Pobierz listę wszystkich produktów
page = 1
while True:
       # czy plik 'access_token.txt' istnieje
    if os.path.isfile('access_token.txt'):      
        with open('access_token.txt', 'r') as file:
            accessToken = file.read().strip()
    else:
        log.err("Brak Autoryzacji. [Wygeneruj accessToken w menu!]")
        

    # czy plik 'url.txt' istnieje
    if os.path.isfile('url.txt'):
        with open('url.txt', 'r') as file:
            entrypoint = file.read().strip()
    else:
        log.err("Brak URL sklepu. [Wygeneruj accessToken w menu!]")
        
    headers = {
    'Authorization': f'Bearer {accessToken}',
    'Content-Type': 'application/json'
    }

    products_url = f'{entrypoint}/webapi/rest/products?page={page}'
    log.info(f'{entrypoint}/webapi/rest/products?page={page}')
    response = session.get(products_url, headers=headers)
    products = response.json()
    time.sleep(0.3)

    # Jeśli lista produktów jest pusta, zakończ pętlę
    if not products['list']:
        break

    # Iteruj przez wszystkie produkty
    for product in products['list']:
        # Pobierz ID produktu
        product_id = product['product_id']

        # Pobierz najnowszą nazwę produktu
        product_url = f'{entrypoint}/webapi/rest/products/{product_id}'
        response = session.get(product_url, headers=headers)
        product = response.json()
        time.sleep(0.3)

        if 'translations' in product and 'pl_PL' in product['translations'] and 'name' in product['translations']['pl_PL']:
            original_product_name = product['translations']['pl_PL']['name']
        else:
            original_product_name = product['name'] if 'name' in product else None

        if original_product_name:
            product_name = clean_product_name(original_product_name)
            # Dodaj informacje o produkcie do słownika
            product_info[product_id] = {'name': product_name, 'images': []}
        else:
            log(f"Product ID {product_id} does not have a 'name'. Full product data: {product}")
        continue


        # Dodaj informacje o produkcie do słownika
        product_info[product_id] = {'name': product_name, 'images': []}

    # Przejdź do następnej strony
    page += 1

# Pobierz listę wszystkich zdjęć
page = 1
while True:
    images_url = f'{entrypoint}/webapi/rest/product-images?page={page}'
    log.info(f'{entrypoint}/webapi/rest/product-images?page={page}')
    response = session.get(images_url, headers=headers)
    images = response.json()
    time.sleep(0.3)

    # Jeśli lista zdjęć jest pusta, zakończ pętlę
    if not images['list']:
        break

    # Dodaj informacje o zdjęciach do słownika
    for image in images['list']:
        image_id = image['gfx_id']
        image_product_id = image['product_id']

        # Sprawdź, czy zdjęcie należy do jednego z produktów
        if image_product_id in product_info:
            product_info[image_product_id]['images'].append(image_id)

    # Przejdź do następnej strony
    page += 1

# Aktualizuj 'name' i 'name' w 'pl_PL' translation dla każdego zdjęcia
for product_id, info in product_info.items():
    log(f'Processing product ID: {product_id}, original name: "{info["name"]}", images: {len(info["images"])}')
    for image_id in info['images']:
        new_image_name = info['name']
        update_url = f'{entrypoint}/webapi/rest/product-images/{image_id}'

        data = {
            'name': new_image_name,
            'translations': {
                'pl_PL': {
                    'name': new_image_name
                }
            }
        }
        time.sleep(0.3)

        while True:
            response = session.put(update_url, headers=headers, json=data)
            if response.status_code == 200:
                log(f'Image {image_id} updated, Name: "{new_image_name}"')
                break
            elif response.status_code == 429:  # Kod statusu 429 oznacza zbyt wiele zapytań
                log('Osiągnięto limit zapytań, czekam...')
                time.sleep(0.3)  # Czekaj 10 sekund przed ponownym zapytaniem
            else:
                log(f'Coś poszło nie tak przy aktualizacji zdjęcia {image_id}: {response.content}')
                time.sleep(0.3)  # Czekaj 10 sekund przed ponownym zapytaniem

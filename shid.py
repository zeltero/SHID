import requests
import time
import os
import json
from colored_print import log
from pyfiglet import Figlet
from requests.auth import HTTPBasicAuth


# DANE UWIERZYTELNIAJĄCE 





session = requests.Session()




def check_images():
    images_url = f'{entrypoint}/webapi/rest/product-images?page=1'
    try:
        response = session.get(images_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.err(f"Błąd podczas sprawdzania zdjęć: {e}")
        return False
    images = response.json()
    return 'list' in images and images['list']

def delete_images():
    # Sprawdź, czy plik 'access_token.txt' istnieje
    if os.path.isfile('access_token.txt'):
        # Jeśli istnieje, wczytaj token dostępu
        with open('access_token.txt', 'r') as file:
            accessToken = file.read().strip()
    else:
        # Jeśli nie istnieje, wyświetl błąd i wróć do menu
        log.err("Brak Autoryzacji. [Wygeneruj accessToken w menu!]")
        return

    # Sprawdź, czy plik 'url.txt' istnieje
    if os.path.isfile('url.txt'):
        # Jeśli istnieje, wczytaj URL sklepu
        with open('url.txt', 'r') as file:
            entrypoint = file.read().strip()
    else:
        # Jeśli nie istnieje, wyświetl błąd i wróć do menu
        log.err("Brak URL sklepu. [Wygeneruj accessToken w menu!]")
        return
    headers = {
    'Authorization': f'Bearer {accessToken}',
    'Content-Type': 'application/json'
    }

    
    total_images = 0
    deleted_images = 0
    image_counter = 0
    start_time = None
    end_time = None
    page = 1

    # Pobierz listę wszystkich zdjęć
    image_ids = []
    while True:
        images_url = f'{entrypoint}/webapi/rest/product-images?page={page}'
        try:
            start_time = time.time()
            response = session.get(images_url, headers=headers)
            response.raise_for_status()
            end_time = time.time()
            log.pink(f'Żądanie GET do {images_url} trwało {end_time - start_time} sekund')
            time.sleep(0.3)
        except requests.exceptions.RequestException as e:
            log.err(f"Błąd podczas pobierania listy zdjęć: {e}")
            break
        images = response.json()
        

        if 'list' not in images or not images['list']:
            break

        # Dodaj identyfikatory zdjęć do listy
        for image in images['list']:  
            image_id = image['gfx_id']  
            image_ids.append(image_id)

        total_images += len(images['list'])
        page += 1

    print(f'Całkowita ilość zdjęć do usunięcia: {total_images}')

    if total_images == 0:
        return

    #ZĄDANIA BULK
    bulk_request = []
    for image_id in image_ids:
        delete_url = f'/webapi/rest/product-images/{image_id}'
        bulk_request.append({
            "id": f"delete-image-{image_id}",
            "path": delete_url,
            "method": "DELETE"
        })

        # Jeśli zebrano 25 zdjęć wyślij żądanie
        if len(bulk_request) == 25:
            log.info(f'Usuwanie 25 zdjęć...')
            try:
                start_time = time.time()
                response = session.post(f'{entrypoint}/webapi/rest/bulk', headers=headers, json=bulk_request)
                response.raise_for_status()
                end_time = time.time()
                log.info(f'Żądanie POST do {entrypoint}/webapi/rest/bulk trwało {end_time - start_time} sekund')
                deleted_images += 25
                log.success(f'Usunięto {deleted_images}/{total_images} zdjęć')
            except requests.exceptions.RequestException as e:
                log.err(f"Błąd podczas usuwania zdjęć: {e}")
            bulk_request = []
            time.sleep(250/1000)

    # Usuń pozostałe zdjęcia, jeśli istnieją
    if bulk_request:
        log.info(f'Usuwanie {len(bulk_request)} zdjęć...')
        try:
            start_time = time.time()
            response = session.post(f'{entrypoint}/webapi/rest/bulk', headers=headers, json=bulk_request)
            response.raise_for_status()
            end_time = time.time()
            log.info(f'Żądanie POST do {entrypoint}/webapi/rest/bulk trwało {end_time - start_time} sekund')
            deleted_images += len(bulk_request)
            log.success(f'Usunięto {deleted_images}/{total_images} zdjęć')
        except requests.exceptions.RequestException as e:
            log.err(f"Błąd podczas usuwania zdjęć: {e}")

    # Sprawdź, czy wszystkie zdjęcia zostały usunięte
    if not check_images():
        log.warn("WSZYSTKIE ZDJECIA ZOSTAŁY USUNIĘTE")


def display_menu():
    f = Figlet(font='slant')
    print(f.renderText('SHID'))

    print("1. Wyczyść zdjęcia produktów")
    print("2. Generuj accessToken")
    print("3. Wyjdz")

    choice = input("Wybierz opcję: ")
    return choice


def get_access_token():
    shop_url = input("Podaj URL sklepu(z https://):")
    if not shop_url.startswith('https://'):
        log.error("URL musi zawierać 'https://'")
        return None

    client_id = input("Podaj login do konta API:")
    client_secret = input("Podaj haslo do konta API:")

    url = f'{shop_url}/webapi/rest/auth'

    # Wykonaj żądanie POST
    response = requests.post(url, auth=HTTPBasicAuth(client_id, client_secret))

    # Sprawdź, czy żądanie zakończyło się sukcesem
    if response.status_code == 200:
        access_token = response.json()['access_token']
        log.success(f'[SUCCESS] Access Token: {access_token}')
        log("Zapisano token. Mozesz uzyc programu.")

        # Zapisz token dostępu do pliku tekstowego
        with open('access_token.txt', 'w') as file:
            file.write(access_token)

        # Zapisz URL sklepu do pliku tekstowego
        with open('url.txt', 'w') as file:
            file.write(shop_url)

        return access_token
    else:
        print(f'Błąd podczas uzyskiwania tokena dostępu: {response.content}')
        return None

def main():
    while True:
        choice = display_menu()
        if choice == "3":
            break
        elif choice == "1":
            delete_images()
        elif choice == "2":
            get_access_token()

if __name__ == "__main__":
    main()


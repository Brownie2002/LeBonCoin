import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json

# Fonction pour extraire un champ à partir d'un label (méthode générique qui cherche le texte)
def extract_field(soup, label):
    # Rechercher un élément contenant exactement le texte label (par exemple "Kilométrage")
    label_element = soup.find(lambda tag: tag.name in ["span", "div"] and label in tag.get_text())
    if label_element:
        # On suppose que la valeur à extraire se trouve dans le sibling suivant ou dans le parent suivant
        next_element = label_element.find_next_sibling()
        if next_element:
            return next_element.get_text().strip()
    return None

def scrape_leboncoin(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/92.0.4515.131 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    # Vérifier que la page a bien été récupérée
    if response.status_code != 200:
        print(f"Erreur lors du téléchargement de la page: code {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the script tag with type "application/ld+json"
    script_tag = soup.find('script', type='application/ld+json')


    # Exemple d'extraction par recherche de labels
    # Ces sélecteurs doivent être adaptés en fonction du code HTML réel de la page.
    # Pour le prix, il se peut qu'il soit indiqué dans une balise particulière (par exemple "span" avec une classe ou un attribut spécifique)

    price = None
    kilometrage = None
    date_mise_circulation = None
    vendeur = None
    localisation = None
    
    if script_tag and script_tag.string:
        # Load the JSON content from the script tag.
        json_data = json.loads(script_tag.string)
        
        # Extract the price
        offers = json_data.get("offers", {})
        price = offers.get("price")

        mileageFromOdometer = json_data.get("mileageFromOdometer", {})
        kilometrage = mileageFromOdometer.get("value")
        
        vehicleModelDate = json_data.get("vehicleModelDate", {})

        info = soup.find('script', type='application/json',id="__NEXT_DATA__")
        info_json=json.loads(info.string)

        att = info_json['props']['pageProps']['ad']['attributes']
        location = info_json['props']['pageProps']['ad']['location']
        owner    = info_json['props']['pageProps']['ad']['owner']

        all_att = {item['key']: item['value'] for item in att}

        price = info_json['props']['pageProps']['ad']['price_cents']/100
        vendeur = owner["name"]
        localisation  = location["city_label"]
        date_mise_circulation = all_att["regdate"]
        kilometrage = all_att["mileage"]

        print("Price extracted:", price)
    else:
        print("Script tag with ld+json not found or is empty.")

   
    # On ajoute la date de récupération pour suivi
    date_scraping = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "url": url,
        "date_scraping": date_scraping,
        "kilometrage": kilometrage,
        "date_mise_en_circulation": date_mise_circulation,
        "vendeur": vendeur,
        "localisation": localisation,
        "prix": price
    }
    
    return data

def sauvegarder_csv(data, filename='leboncoin_data.csv'):
    # Si le fichier n'existe pas, on écrira l'en-tête
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            fichier_existe = True
    except FileNotFoundError:
        fichier_existe = False
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["url", "date_scraping", "kilometrage", "date_mise_en_circulation", "vendeur", "localisation", "prix"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not fichier_existe:
            writer.writeheader()
        
        writer.writerow(data)
    print(f"Données sauvegardées dans {filename}")

if __name__ == "__main__":

    # Load URLs from a file
    with open("urls.txt", "r") as file:
        url_list = [line.strip() for line in file if line.strip()]

 
    for url in url_list:
        # Scraper l'annonce
        annonce_data = scrape_leboncoin(url)
        
        if annonce_data:
            print("Données extraites :")
            for cle, valeur in annonce_data.items():
                print(f"{cle}: {valeur}")
            
            # Sauvegarder les données dans un CSV
            sauvegarder_csv(annonce_data)
        else:
            print("L'annonce n'est pas accessible ou n'existe plus.")

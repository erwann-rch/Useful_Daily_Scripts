import requests
from bs4 import BeautifulSoup

# The URL of the web page
url = "https://www.carburant-prix-coutant.fr/"

try:
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        tree = BeautifulSoup(response.text, "html.parser")

        # Find the section with the specified class and ID
        section = tree.find("section", {"class": "container", "id": "alerte"})

        # Check if the section was found
        if section:
            divs = section.find_all("div", {"class": "feature col"})
            print("[+] Carburant prix coûtant :")
            for div in divs:
                # Find the <h3> element and extract its brand
                h3_element = div.find("h3")
                if h3_element:
                    title = h3_element.get_text(strip=True).split()[-1]

                # Find the <p> element and extract its text
                p_element = div.find("p")
                if p_element:
                    description = p_element.get_text()

                # Find the link within the <a> tag
                link = div.find("a")["href"] if div.find("a") else ""

                print("\t\n####################\n")
                print("\t[*] Brand:", title)
                print("\t[*] Description:", description)
                print("\t[*] Link:", link)
                
        
        else:
            print("[+] No alert for fuel at cost operation")
    else:
        print("[-] Failed to fetch the web page. Status code:", response.status_code)
except requests.exceptions.RequestException as e:
    print("[-] An error occurred:", e)

#time.sleep(0.052)
#time.sleep(0.045)
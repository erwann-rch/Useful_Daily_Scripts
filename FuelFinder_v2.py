#!/usr/bin/env python3
############################# [ IMPORTS ] #############################

import requests, os, time, json, argparse
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import great_circle

############################# [ VARIABLES ] #############################
data = []
timestamp = int(time.time())
#datetimeString = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # different naming system

# Check if datetimeString is in variables
dateChoice = datetimeString if 'datetimeString' in globals() else timestamp

############################# [ FUNCTIONS ] #############################

# Handling the args
def getArgs():
    parser = argparse.ArgumentParser("python3 FuelFinder_v2.py")  # Create an object to get args
    # Options of this program
    parser.add_argument("-F", "-f", "--fuel", nargs="*", dest="fuels", help="Enter the fuel(s) you want separted by a space (default: 'SP95')", type=str)
    parser.add_argument("-C", "-c", "--city", dest="address", help="Enter the city, the zipcode or the address you are")
    parser.add_argument("-D", "-d", "--distance", dest="dist", help="Enter the distance you want in kilometer (<=20km) (default: 5)", type=float)
    options = parser.parse_args()
    if options.fuels is not None: 
        for fuel in options.fuels :
            if not fuel in ['SP98', 'SP95', 'Gazole', 'E10', 'E85', 'GPLc']:  # CHeck if the fuel is supported
                parser.error("\n\t[-] Error in the command : please chose every fuels  you want among : 'SP98' / 'SP95' / 'Gazole' / 'E10' / 'E85' / 'GPLc'")
                parser.error("Check -h or --help for help")
                exit()
    else:  # default value
        options.fuels = ["SP95"]

    if options.address is None:  # Check if city option is empty
        parser.error("\n\t[-] Error in the command : please specify a city/zipcode/address")
        parser.error("Check -h or --help for help")
        exit()

    if options.dist is not None:  # Check if dist option is empty
        if options.dist > 20:
            parser.error("\n\t[-] Error in the command : please specify a distance (in km) under 20")
            parser.error("Check -h or --help for help")
            exit()
    else:  # default value
        options.dist = 5

    return options

# --------------------------------------------------
# Function to forge url depending on the fuels chosen
def URLForger(fuelList):
    urlBase = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/json?select=geom%2Cadresse%2Ccp%2Cville%2Cprix&lang=fr&timezone=Europe%2FParis&limit=2000"
    urlEnd = "".join(f"&refine=carburants_disponibles%3A%22{fuel}%22" for fuel in fuelList)  # Add filter for each fuel wanted
    return urlBase+urlEnd

# --------------------------------------------------
# Function to download the file in the ./tmp/ directory
def download(url, fuels):
    response = None  # Initialize the response variable
    filename = os.path.join(f"{os.getcwd()}/tmp/",f"{'_'.join(fuels)}_{dateChoice}.json")  # Create a file into ./tmp depending on the fuels chosen
    try:
        response = requests.get(url)
        if response.status_code == 200:  # Check if response is 200 OK
            with open(filename, 'wb') as file:
                file.write(response.content)
        return filename
    
    except Exception as e:
        if response is not None:
            print(f"[-] Wasn't able to download the file. Status code: {response.status_code}")
        else:
            print(f"[-] An error occurred while making the request: {str(e)}")
        exit()

# --------------------------------------------------
# Function to parse the file into a dictionary
def JSONParser(filename) :
    with open(filename, 'r') as jsonFile:
        data = json.load(jsonFile)
    return data # {{geom:dict,adresse:str,cp:str,ville:str,prix:list(dict)},{},{},...}

# --------------------------------------------------
# Function to register all the pumps in a given distance
def registerNearPumps(data, coords, dist):
    nearPumpList = []
    lat, lon = coords
    for pump in data:  # Iterate through the whole reverse dict of pumps
        pumpCoords = tuple(pump['geom'].values())[::-1]  # Get the coords of each pump in the right order
        if great_circle(pumpCoords, coords).kilometers <= dist :
            nearPumpList.append(pump)
    
    return nearPumpList # [{geom:dict,adresse:str,cp:str,ville:str,prix:list(dict)},{},{},...]

# --------------------------------------------------
# # Function to order pumps by price of the chosen fuel
def ascOrder(stations, firstChoiceFuelName):
    sortedPumpList = []  # Initialize sortedPumpList
    for station in stations:
        fuels = eval(station['prix'])  # Get the dict of fuels available at this station to extract the price of the chosen fuel
        firstChoiceFuelPrice = None  # Initialize the firstChoiceFuelPrice
        for fuel in fuels:
            if fuel['@nom'] == firstChoiceFuelName:
                firstChoiceFuelPrice = float(fuel['@valeur'])  # Convert the price to a float
                break  # Stop the search

        if firstChoiceFuelPrice is not None:
            # Add the first choice fuel infos to the station info
            station['firstChoiceFuel'] = {'name' : firstChoiceFuelName, 'price' : firstChoiceFuelPrice}
            sortedPumpList.append(station)

    # Sort the stations by first choice fuel price
    sortedPumpList = sorted(sortedPumpList, key=lambda x: x['firstChoiceFuel']['price'])

    return sortedPumpList

# --------------------------------------------------
# Function to get the coordinates from the address
def getAddress(address):
    locator = Nominatim(user_agent=f"python-getCoordsAddr")
    geoLoc = locator.geocode(address)
    lat, lon = geoLoc.latitude, geoLoc.longitude
    return (lat, lon)

# --------------------------------------------------
# Function to delete the file 
# def delete(file):
#     time.sleep(0.1)  # Sleep to be sure process of parsing in ended
#     os.remove(file)

# --------------------------------------------------
# Main function
def main():
    try:
        # Get the args
        options = getArgs()

        # Available fuels: 'SP98' / 'SP95' / 'Gazole' / 'E10' / 'E85' / 'GPLc'
        url = URLForger(options.fuels)
        
        # Initialize filename variable
        filename = None
        
        # This second try/finally permit to keep filename variable in local 
        try :
            # Download the JSON file with the specified fuel types
            filename = download(url, options.fuels)
            
            # Parse the file into a dict
            data = JSONParser(filename)

            # Get the sorted by first choice fuel price list of near pumps 
            stationList = ascOrder(registerNearPumps(data, getAddress(options.address), options.dist), options.fuels[0])
            if len(stationList) == 0:  # Handle in no pumps with chosen fuel
                print(f"\t[-] There is no stations with {options.fuels} in {options.dist}km around")
                # raise ValueError  # raise error when 0 pumps to quit
            
            print(f"[*]You chose '{options.fuels[0]}' as first choice fuel, the next list will be sorted depending on its price.")
            print("[*]Change the fuel order if you want an other order.")
            for station in stationList:
                print("#----------#")
                print("[+] Coordinates:")
                print(f"\t[+] Latitude: {station['geom']['lat']}")
                print(f"\t[+] Longitude: {station['geom']['lon']}")
                print("[+] Address:")
                print(f"\t[+] {station['adresse']}, {station['cp']} {station['ville']}")
                print("[+] Prices:")
                for fuel in eval(station['prix']):
                    print(f"\t[+] Name: {fuel['@nom']}")
                    print(f"\t[+] Update: {fuel['@maj']}")
                    print(f"\t[+] Price: {fuel['@valeur']}")
                    print("\t# ----- #")
        
        # Remove file if it has been downloaded
        finally :
            if filename is not None:
                os.remove(filename)

    # Catch any exception of both try block
    except Exception as e :
        print("\t[-] An error occurred :")
        print(e)

############################# [ LAUNCH ] #############################
# create tmp subdirectory of the current directory 
if not os.path.exists(f"{os.getcwd()}/tmp"):
    os.makedirs(f"{os.getcwd()}/tmp")    

main()
#time.sleep(0.052)
#time.sleep(0.045)
#!/usr/bin/env python3
############################# [ IMPORTS ] #############################

import requests, zipfile, os, argparse
import xml.etree.ElementTree as ET

from io import BytesIO
from geopy.geocoders import Nominatim
from math import *

############################# [ VARIABLES ] #############################

url = "https://donnees.roulez-eco.fr/opendata/instantane"  # Output : zip file
filename = "InstantFuelPrice.xml"

############################# [ FUNCTIONS ] #############################

# Handling the args
def getArgs():
    parser = argparse.ArgumentParser("python3 FuelFinder.py")  # Create an object to get args
    # Options of this program
    parser.add_argument("-F", "-f", "--fuel", dest="fuel", help="Enter the fuel you want (default='SP95')", type=str)
    parser.add_argument("-C", "-c", "--city", dest="city", help="Enter the address, the city or the zipcode you are")
    parser.add_argument("-D", "-d", "--distance", dest="dist", help="Enter the distance you want (default=5)", type=float)
    options = parser.parse_args()
    #print(parser.parse_args())
    if options.fuel is not None:  # Check if fuel option is empty
        if not options.fuel in ['SP98', 'SP95', 'Gazole', 'E10', 'E85', 'GPLc']:  # Check if the fuel is supported
            parser.error("\n    [-] Error in the command : please chose a fuel among : 'SP98' / 'SP95' / 'Gazole' / 'E10' / 'E85' / 'GPLc'")
            parser.error("Check -h or --help for help")
            exit()
    else:  # default value
        options.fuel = "SP95"

    if options.city is None:  # Check if city option is empty
        parser.error("\n    [-] Error in the command : please specify a city")
        parser.error("Check -h or --help for help")
        exit()

    if options.dist is not None:  # Check if dist option is empty
        if options.dist > 20:
            parser.error("\n    [-] Error in the command : please specify a distance (in km) under 20")
            parser.error("Check -h or --help for help")
            exit()
    else:  # default value
        options.dist = 5

    return options

# --------------------------------------------------
# Function to register all the pumps in a given distance
def registerPumps(filename, coords, dist):
    output = []
    tree = ET.parse(filename)
    root = tree.getroot()
    # Get zone
    coords1 = getCoordZone(coords, dist)  # Get coordinates + distance(m)
    coords2 = getCoordZone(coords, -dist)  # Get coordinates - distance(m)
    for child in root:
        lat = float(child.attrib.get('latitude')) / 10 ** 5  # Get the good lat format
        lon = float(child.attrib.get('longitude')) / 10 ** 5  # Get the good lon format
        if float(coords1[0]) >= float(lat) >= float(coords2[0]) and float(coords1[1]) >= float(lon) >= float(
                coords2[1]):
            output.append(child)  # Append only if the current lat & lon is in the zone
    return output

# --------------------------------------------------
# Function to find the nearest pump
def pumpOrdering(pumpList, fuel):
    # Fuels available: 'SP98' / 'SP95' / 'Gazole' / 'E10' / 'E85' / 'GPLc'
    nearPumpList = []
    for pump in pumpList:
        for attribute in range(len(pump)):
            if pump[attribute].tag == 'prix':  # Check if the attribute is the price
                if pump[attribute].get('nom') == fuel:  # Check if the fuel is the chosen one
                    # Make a list of dict with useful infos
                    nearPumpList.append({"Address": f"{pump[0].text}, {pump[1].text}, {getAddress(pump[1].text)[0]}",
                                         "Latitude": float(pump.attrib.get('latitude'))/10**5,
                                         "Longitude": float(pump.attrib.get('longitude'))/10**5,
                                         "Data": {"Last MAJ": pump[attribute].get('maj'),
                                                  "Fuel": pump[attribute].get('nom'),
                                                  "Price": float(pump[attribute].get('valeur'))}
                                         })

    return nearPumpList

# --------------------------------------------------
# Function to order pumps by price of the chosen fuel
def ascOrder(nearPumpList):
    orderedList = sorted(nearPumpList, key=lambda x: x['Data']['Price'])
    return orderedList[:3]  # return only 3 best

# --------------------------------------------------
# Function to determine the coords of the zone
def getCoordZone(coords, dist):
    lat, lon = coords
    # (pi/180) * earthRadius * cos(theta*pi/180) where earthRadius = 6371 and theta = lat deg > get the number of km per deg
    kmTodeg = (dist / 6371) * (180 / pi)  # approx 111km/deg
    newLat = lat + kmTodeg  # Get the new lat
    newLon = lon + (kmTodeg / cos(
        lat * pi / 180))  # Get the new lon based on the lat because the Earth is not a perfect sphere
    #print(newLat,newLon)
    return newLat, newLon

# --------------------------------------------------
# Function to get the zipcode from the city name
def getAddress(city):
    locator = Nominatim(user_agent=f"python-getzipcode")
    geoLoc = locator.geocode(city)
    address = tuple(geoLoc.address.split(','))  # Get the whole address
    zipcode = address[-2][1:]  # Get the zipcode
    lat = geoLoc.latitude
    lon = geoLoc.longitude
    return zipcode, (lat, lon)

# --------------------------------------------------
# Function to download and set the path of the file
def download():
    req = requests.get(url)  # Get zip file
    zip = zipfile.ZipFile(BytesIO(req.content))  # Write the zip file
    zip.extractall("New Folder")  # Extract it
    if os.path.isfile(filename):  # Deleting the file if exists
        os.remove(filename)
    os.replace("New Folder/PrixCarburants_instantane.xml", "./" + filename)  # Moving and renaming the file
    os.rmdir("New Folder")  # Deleting the directory

# --------------------------------------------------
# Main function
def main(fuel, coords, dist):
    download()
    # Available fuel: 'SP98' / 'SP95' / 'Gazole' / 'E10' / 'E85' / 'GPLc'
    availablePumps = pumpOrdering(registerPumps(filename, coords, dist), fuel)  # Determine which pumps are available
    os.remove(filename)
    return ascOrder(availablePumps)  # Return ascendant order


############################# [ LAUNCH ] #############################

options = getArgs()
#print(options)
#time.sleep(0.052)
#time.sleep(0.045)

pumpList = main(options.fuel, getAddress(options.city)[1], options.dist)
if len(pumpList) == 0:
    print(f"\t[-] There is no {options.fuel} in {options.dist}km around")

for pump in pumpList:
    print("#----------#")
    for key in pump.keys():
        if type(pump[key]) != dict:
            print(f"\t[+] {key} : {pump[key]}")
        else:
            print(f"\t[+] {key} :")
            for key2 in pump[key]:
                if not key2 == 'Price':
                    print(f"\t\t[*] {key2} : {pump[key][key2]}")
                else:
                    print(f"\t\t[*] {key2} : {pump[key][key2]}€/L")


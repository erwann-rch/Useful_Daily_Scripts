#!/usr/bin/env python3
############################# [ IMPORTS ] #############################

import pycountry, holidays, argparse, tabulate
from datetime import date, timedelta

############################# [ VARIABLES ] #############################

lsDates = {
    "Holiday name": [],
    "From": [],
    "To": [],
    "Week #": [],
    "Paid leaves": [],
    "# of days off": []
}  # Dict of data related to holidays

days = ["Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"]


# ############################# [ FUNCTIONS ] #############################

# Handling the args
def getArgs():
    parser = argparse.ArgumentParser("python3 HolidayFinder.py")  # Create an object to get args
    # Options of this program
    parser.add_argument("-Y", "-y", "--year", dest="year", help="Enter the year you want", type=int)
    parser.add_argument("-C", "-c", "--code", dest="code", help="Enter the country/state code you are (if you know it)", type=str)
    options = parser.parse_args()

    if options.year is not None:  # Check if year option is empty
        if not 1801 < options.year <= 9999 :  # Check if the year is supported
            parser.error("\n    [-] Error in the command : please chose a year in the range ]1801;9999]")
            parser.error("Check -h or --help for help")
            exit()
    else:
        parser.error("\n    [-] Error in the command : please specify a year")
        parser.error("Check -h or --help for help")
        exit()

    if options.code is not None:  # Check if code option is empty
        if options.code != options.code.upper():
            options.code = options.code.upper()    
        if pycountry.countries.get(alpha_2=options.code) is not None :  # Check if it's a country code
            if pycountry.subdivisions.get(country_code=options.code.split("-")[0]) is None :  # Check if it's a subdivision code
                parser.error("\n    [-] Error in the command : please specify a valid state code or don't specify code")
                parser.error("Check -h or --help for help")
                exit()
        else : 
            parser.error("\n    [-] Error in the command : please specify a valid country code or don't specify code")
            parser.error("Check -h or --help for help")
            exit()

    return options # options = Namespace object with attributes


#--------------------------------------------------
# Function to help user getting his country/state code
def findCode():
    # Display a list of available countries to the user
    availableCountries = {}
    for country in sorted(list(pycountry.countries),key=lambda x: x.alpha_2): 
        availableCountries[country.alpha_2] = country.name 

    print("\n[+] Available countries:\n")
    for countryCode, countryName in availableCountries.items():
        print(f"{countryCode}: {countryName}")

    # Prompt the user to enter a country code
    selectedCountryCode = input("\n[+] Enter the country code: ").upper()

    # Check if the entered country code is valid
    if selectedCountryCode not in availableCountries.keys():
        print("\n[-] Invalid country code. Please enter a valid country code.")
        findCode()
    else: 
        selectedCountry = pycountry.countries.get(alpha_2=selectedCountryCode)

        subdivs = pycountry.subdivisions.get(country_code=selectedCountry.alpha_2)
        # Check if there is state/province in all subdivisions
        if any(subdiv.type == 'State' or subdiv.type == 'Province' for subdiv in subdivs): 
            # Display a list of available state/province to the user
            availableSubdivs = {}
            for subdiv in sorted(list(subdivs),key=lambda x: x.code): 
                availableSubdivs[subdiv.code] = subdiv.name

            print("\n[+] Available subdivisions:\n")
            for stateCode, stateName in availableSubdivs.items():
                print(f"{stateCode}: {stateName}")

            # Prompt the user to enter a country code
            selectedSubdivCode = input("\n[+] Enter the subdivision code: ").upper()
            
            # Retrieve the holidays for the selected subdivision (if possible)
            if selectedSubdivCode not in availableSubdivs.keys():
                print("\n[-] Invalid state/province code. Please enter a valid code.")
                findCode()
            else :
                print(f"\n[+] Your code is : {selectedSubdivCode}")
                return selectedSubdivCode # selectedSubdivCode = str
        else :
            print(f"\n[+] Your code is : {selectedCountryCode}")
            return selectedCountryCode # selectedCountryCode = str


#--------------------------------------------------
# Function to get holidays days depending on the country/state code
def findHolidays(year, code):
    if "-" in code:  # Checking if subdivision code 
        countryCode, subdivCode = code.split("-")
        holidaysList = holidays.CountryHoliday(countryCode, state=subdivCode, years=year)
    else:
        countryCode = code
        holidaysList = holidays.CountryHoliday(countryCode, state=None, years=year)

    filteredHolidays = {}
    for date, holidayName in holidaysList.items():
        if 0 <= date.weekday() <= 4:  # Check if the day is a weekday (weekend day is not useful to look up)
            filteredHolidays[holidayName] = date 

    # Sort the dictionary by week number
    sortedHolidays = dict(sorted(filteredHolidays.items(), key=lambda x: x[1].isocalendar()))
     
    lsDates["Holiday name"].extend(sortedHolidays.keys())  # Sort the properties of the table too
    
    return sortedHolidays  # filteredHolidays = {str: datetime object}

#--------------------------------------------------
# Function to calculate ranges for taking paid leaves
def makeRanges(dateList):
    rangesCoeff = []
    for date in dateList.items():  # Calculate number of days to add or subtract to have a range
        # print(days[date[0].weekday()])
        if date[1].weekday() == 0:  # Monday
            rangesCoeff.append((0, 4))  # Before and after weekdays left
        elif date[1].weekday() == 1:  # Tuesday
            rangesCoeff.append((1, 3))
        elif date[1].weekday() == 2:  # Wednesday
            rangesCoeff.append((2, 2))
        elif date[1].weekday() == 3:  # Thursday
            rangesCoeff.append((3, 1))
        else:  # Friday
            rangesCoeff.append((4, 0))

    rangesDates = []
    for i in range(len(rangesCoeff)):
        currentHoliday = list(dateList.items())[i][1]  # datetime object of the list of tuple
        startDay = currentHoliday - timedelta(days=rangesCoeff[i][0])  # Start paid leave to take
        endDay = currentHoliday + timedelta(days=rangesCoeff[i][1])  # End paid leave to take

        if startDay == currentHoliday:  # If holiday is Monday >> no need to take days before
            tmp = currentHoliday + timedelta(days=1)
            rangesDates.append((tmp, endDay))
        elif endDay == currentHoliday:  # If holiday is Friday >> no need to take days after
            tmp = currentHoliday - timedelta(days=1)
            rangesDates.append((startDay, tmp))
        else:  # In any other cases the range is correct
            rangesDates.append((startDay, endDay))

    return rangesDates  # rangesDates = [(datetime object, datetime object),...]


#--------------------------------------------------
# Function to make a clean table
def makeTabulate(rangesDateList):
    for date in rangesDateList:
        lsDates["From"].append(date[0])  # Start date
        lsDates["To"].append(date[1])  # End date
        lsDates["Week #"].append(date[0].isocalendar()[1])  # Week number
        deltadays = date[1]-date[0]
        lsDates["Paid leaves"].append(deltadays.days+1)  # Number of paid leaves to take
        lsDates["# of days off"].append(deltadays.days+1+4)  # Number of off days (+4 => 2 weekends surrounding the week)


#--------------------------------------------------
# Function to print a pretty table 
def tablePrint():
    return str(tabulate.tabulate(lsDates, headers="keys", tablefmt="github"))  # Make a pretty print


############################# [ LAUNCH ] #############################

options = getArgs()
if options.code is None :
    options.code = findCode()

dateList = findHolidays(options.year,options.code)
rangesDateList = makeRanges(dateList)
makeTabulate(rangesDateList)

#time.sleep(0.052)
#time.sleep(0.045)

print(tablePrint())

#!/usr/bin/env python3
############################# [ IMPORTS ] #############################

from tabulate import tabulate
import ipaddress, argparse, re

############################# [ VARIABLES ] #############################

pattern = r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}\/([1-9]|[12]\d|3[01]?|32)"  # Regex pattern of an ip address X.X.X.X/Y with X = [0-255] and Y = [1-32]

############################# [ FUNCTIONS ] #############################

# Handling the args
def getArgs():
    parser = argparse.ArgumentParser("python3 SubnetCalculator.py")
    parser.add_argument("-I", "-i", "--ip", dest="netIP", help="Enter the network's address you want to cut", type=str)
    parser.add_argument("-n", "--subnet", dest="nbSubnets", help="Enter the number of subnets you want (if the option is empty, the default number is 4)", type=int)
    options = parser.parse_args()

    if options.netIP is None:  # Check is IP empty
        parser.error("\n    [-] Error in the command: network address option is empty")
        parser.error("Check -h or --help for help")
        exit()
    elif not re.fullmatch(pattern, options.netIP):  # Check is IP valid
        parser.error("\n    [-] Error in the command: The specified address does not seem to be a valid IPv4 address in CIDR format")
        parser.error("Check -h or --help for help")
        exit()

    if options.nbSubnets is not None:  # Check is nbSubnets empty
        try:
            int(options.nbSubnets)
        except ValueError:
            parser.error("\n    [-] Error in the command: Please enter an integer value for the subnet number")
            parser.error("Check -h or --help for help")
            exit()

        if not 0 < int(options.nbSubnets) <= getMaxSub(int(options.netIP.split("/")[1])):  # Check is nbSubnets is valid
            parser.error("\n    [-] Error in the command: Please enter a valid number of subnets")
            parser.error("Check -h or --help for help")
            exit()
    else:
        options.nbSubnets = 4

    return options


# --------------------------------------------------
# Function to get the maximum number of subnets (or hosts)
def getMaxSub(mask):
    subnetMask = int(mask)
    if not 1 <= subnetMask <= 32:
        print("\n    [-] Error in the command: Please enter a valid subnet mask")
        exit()

    maxSubnets = 2 ** (32 - subnetMask)
    # maxHosts = (2 ** (32 - subnetMask)) // options.nbSubnets
    return maxSubnets


# --------------------------------------------------
# Function to calculate every subnet info
def subnetCalc():
    subnetMask = int(IP.split("/")[1])
    nbSubnets = int(options.nbSubnets)
    network = ipaddress.ip_network(IP, strict=False)
    maxPrefixlenDiff = 4 if subnetMask <= 26 else 2
    subnets = list(network.subnets(prefixlen_diff=maxPrefixlenDiff))  # TODO : make proper maxPrefixlenDiff
    subnetInfo = {
        "Network ID": [str(x) for x in range(options.nbSubnets)],
        "Network IP": [],
        "Broadcast IP": [],
        "Subnet Range": [],
        "CIDR Mask": [],
        "DD Mask": [],
        "Anti-DD Mask": [],
        "Usable Hosts": []
    }
 
    for i,subnet in enumerate(subnets[:nbSubnets]):  # Limit the iteration to the desired number of subnets 
        #subnetInfo["Network ID"].append(subnet.network_address)
        subnetInfo["Network IP"].append(subnet.network_address)
        subnetInfo["Broadcast IP"].append(subnet.broadcast_address)
        subnetInfo["Subnet Range"].append(f"{subnet.network_address + 1} - {subnet.broadcast_address - 1}")
        subnetInfo["CIDR Mask"].append(subnet.prefixlen)
        subnetInfo["DD Mask"].append(str(subnet.netmask))
        subnetInfo["Anti-DD Mask"].append(str(subnet.hostmask))
        subnetInfo["Usable Hosts"].append(subnet.num_addresses - 2)

    return subnetInfo


# --------------------------------------------------
# Function to make a pretty table print
def tablePrint(): 
    return tabulate(subnetCalc(), headers="keys", tablefmt="github")


############################# [ LAUNCH ] #############################

options = getArgs()  # Get the args
IP = options.netIP

# time.sleep(0.052)
# time.sleep(0.045)

print(tablePrint())
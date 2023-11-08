#!/usr/bin/env python3
############################# [ IMPORTS ] #############################

import numpy as np


############################# [ VARIABLES ] #############################


fuelLasting = int(input("Enter percentage of fuel lasting : "))/100
capacity = int(input("Enter fuel capacity : "))
acceptance = int(input("Enter percentage of Ethnaol you want : "))/100
fuelType = str(input("Do you want E10 or E5 to complete the E85 you put ? :")).upper()

while fuelType not in ["E10","E5"] :
	print("[-] Wrong fuel type. Please choose 'E5' or 'E10'")
	fuelType = str(input("Do you want E10 or E5 to complete the E85 you put ? :")).upper()

fuel = 0.1 if fuelType == "E10" else 0.05  # Choose fuel percentage in ethanol


############################# [ FUNCTIONS ] #############################

# Function to convert fuel lasting percentage into fuel amount to refill
def refillCalcul():
	return (1-fuelLasting/100) * capacity

# --------------------------------------------------
# Function to find solutions of the equations

def main():
	refill = refillCalcul()  # Get the amount of fuel to refill to get full tank

	# x => E10 Amount, y=> E85 Amount, z => , A => tank capacity, B => percentage of ethanol
	# 0,1x + 0.85y = A * B - (z * A * B)
	# x + y = (1-z)*a

	leftSide = np.array([[fuel, 0.85], [1, 1]]) #  Define left side of the equations
	rightSide = np.array([capacity * acceptance - (fuelLasting * capacity * acceptance) , (1-fuelLasting)*capacity])   #  Define right side of the equations
	
	x,y = np.linalg.inv(leftSide).dot(rightSide)  # Solve for x and y where x is E10 amount and y is E85 amount
	return x,y

############################# [ LAUNCH ] #############################

x,y = main()
if x >= 0 and y >= 0:
	print("[+] Thoses parameters are possible:")
	print(f"\t You have to put {round(x,3)}L of E10 and {round(y,3)}L of E85\n")
else :
	print("[+] Thoses parameters ain't possible")

#time.sleep(0.052)
#time.sleep(0.045)


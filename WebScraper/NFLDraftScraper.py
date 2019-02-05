import requests
from bs4 import BeautifulSoup
import csv
import numpy as np
import os

##NEED TO DO##
# x. Extract player height and weight (maybe date of birth) from player information pages (use href on the player column)
# x. Find a way to include combine data into this table
# x. Create for loop to get data for all draft classes from 2000 to 2016 (may be able to go even further back?)
# x. Convert data collected into a .csv file
# x. Add headers to the CSV file in some automated way
# x. Might be useful to first clear anything that is in the CSV file before writing to it so that there is no need to empty it manually

##SOME NOTES##
#1. It turns out that some OLINE positions have offensive stats and some have defensive stats, we could either leave them in
#   (there's like two in the 2018 draft class) or get rid of them
#2. It also turns out that there is a static html page for combine data from the year as well! (https://www.pro-football-reference.com/draft/2018-combine.htm)
#   there may be a way to scrape this page and find by player name (this would involve matching their playerURL) the information we are looking for on combine statistics. 
#   For 2018 there is data on 152 players who were drafted, this means we may have to expand our data to include defensive players
#3. Could use variables such as 'hometown' and 'college attended' for our adverse impact analysis

#All the following column headers will be used
columnHeaders = ["draftRound", "draftPick", "playerName", "position", "age", "height", "weight",
					"collegeAttended", "rushingAttempts", "rushingYards", "avgYardsPerRush", "rushingTouchdowns",
					"receptions", "receivingYards", "avgYardsPerReception", "receivingTouchdowns", "passCompletions",
					"passAttempts", "passCompletionPercentage", "passingYards", "avgYardsPerPass", "passingTouchdowns",
					"passingInterceptions", "fortyYardDash", "verticalJump", "benchPress", "broadJump", "threeCone", "shuttle"]

#The only information we need the input is the year of the draft class we want to search
startDraftYear = "2000"
endDraftYear = "2018"

#Initialise an empty array which will store info about all the players a search is succesfully returned for
allPlayers = []

def ScrapeAttackYouGettingScraped(startDraftYear, endDraftYear):
	#Create variables to store integer values of start and end year for search
	startYear = int(startDraftYear)
	endYear = int(endDraftYear)

	if startYear < 2000 or endYear > 2018:
		if startYear < 2000:
			print("Invalid start year, cannot search for data before 2000")
		if endYear > 2018:
			print("Invalid end year, cannot search for data after 2018")
		return

	if (startYear == endYear):
		#Convert the draft year back into a string so it can be used for URLs
		draftYear = str(draftYear)
		ScrapeItAwayBaby(draftYear)

	else:
		for draftYear in range (startYear, endYear + 1):
			#Convert the draft year back into a string so it can be used for URLs
			draftYear = str(draftYear)
			ScrapeItAwayBaby(draftYear)

	#Write all the information that was found into an appropriate CSV file
	ConvertToCSV(allPlayers)

def ScrapeItAwayBaby(draftYear):
	websiteURL = "https://www.pro-football-reference.com/years/" + draftYear + "/draft.htm"
	GetPlayerInformation(websiteURL, draftYear)

def GetPlayerInformation(websiteURL, draftYear):
	htmlResponse = requests.get(websiteURL).text

	soup = BeautifulSoup(htmlResponse,'lxml')

	table = soup.find('table')
	tableBody = table.find('tbody')
	tableRows = tableBody.findAll('tr')

	i = 1

	for row in tableRows:
		#In every row, they put the draft round as a 'th' item
		draftRound = row.find('th').string
		playerInformation = row.findAll('td')

		#Every 30 rows or so there is a row containing all the table headers again, ignore these
		if len(playerInformation) <= 0:
			continue

		#Some players do not have a URL that links to college stats, these should also be ignored
		if playerInformation[27].find('a') is None:
			continue

		#Put all the basic information we've found into the relevant variables
		draftRound = draftRound
		draftPick = playerInformation[0].string
		draftedTeam = playerInformation[1].string
		playerName = playerInformation[2].string
		position = playerInformation[3].string
		age = playerInformation[4].string
		collegeAttended = playerInformation[26].string

		#We also want to collect associated URLS to search for further information
		#Firstly get a URL link to their college statistics
		collegeStatsURL = playerInformation[27].find('a')['href']

		#Get player information from their page
		#The html only shows the suffix for the URL, therefore the starting part needs to be added manually
		playerURL = playerInformation[2].find('a')

		#Need to first check if there is a valid player URL, if not just skip this person
		if playerURL == None:
			continue

		playerURL = playerURL['href']
		fullPlayerURL = "https://www.pro-football-reference.com" + playerURL

		# #We are only concerned with offensive players
		# #This means if their position is "DB", "DE", "DT", "K", "LB", "CB", "ILB", "OLB", "P", "S", "T", "G"
		# #they should be ignored

		# #Centres also do not get any offensive stats (and instead it shows defensive stats)
		# if (position == "DB" or position == "DE" or position == "DT" or position == "K" or position == "LB"
		# 		or position == "CB" or position == "ILB" or position == "OLB" or position == "P" or position == "S"
		# 		or position == "T" or position == "G"):
		# 	continue

		#Now need to get information on their college statistics
		#Check that the search for college stats was valid (0 = invalid, 1 = valid)
		(collegeStatsValid, collegeInformation) = GetCollegeInformation(collegeStatsURL)

		#If the search was invalid, then skip this player and go to the next one
		if (collegeStatsValid == 0):
			continue

		#Put all the college statistics we've received into the relevant variables
		rushingAttempts = collegeInformation[0]
		rushingYards = collegeInformation[1]
		avgYardsPerRush = collegeInformation[2]
		rushingTouchdowns = collegeInformation[3]
		receptions = collegeInformation[4]
		receivingYards = collegeInformation[5]
		avgYardsPerReception = collegeInformation[6]
		receivingTouchdowns = collegeInformation[7]
		passCompletions = collegeInformation[8]
		passAttempts = collegeInformation[9]
		passCompletionPercentage = collegeInformation[10]
		passingYards = collegeInformation[11]
		avgYardsPerPass = collegeInformation[12]
		passingTouchdowns = collegeInformation[13]
		passingInterceptions = collegeInformation[14]

		#Need to get information about players height and weight
		(physicalStatisticsValid, height, weight) = GetPhysicalInformation(fullPlayerURL)

		#Check if valid physical statistics were retrieved, if not, ignore this player
		if physicalStatisticsValid == 0:
			continue

		(combineStatisticsValid, combineInformation) = GetCombineInformation(draftYear, playerURL)

		#Check that at least one valid combine statistic was retrieved, if not, ignore this player
		if combineStatisticsValid == 0:
			continue

		fortyYardDash = combineInformation[0] 
		verticalJump = combineInformation[1]
		benchPress = combineInformation[2]
		broadJump = combineInformation[3]
		threeCone = combineInformation[4]
		shuttle = combineInformation[5]

		print("Basic Player Information (no.",i,"): ")
		print(draftRound, draftPick, playerName, position, age, height, weight, collegeAttended)
		print("College Statistics: ")
		print(rushingAttempts, rushingYards, avgYardsPerRush, rushingTouchdowns, receptions, receivingYards,
				avgYardsPerReception, receivingTouchdowns, passCompletions, passAttempts, passCompletionPercentage,
				passingYards, avgYardsPerPass, passingTouchdowns, passingInterceptions)
		print("Combine Statistics: ")
		print(fortyYardDash, verticalJump, benchPress, broadJump, threeCone, shuttle)


		#Create an array storing all the player information so that we can put it into a larger array containing 
		#everyones information
		playerInformation = [draftRound, draftPick, playerName, position, age, height, weight, collegeAttended, rushingAttempts,
								rushingYards, avgYardsPerRush, rushingTouchdowns, receptions, receivingYards, avgYardsPerReception,
								receivingTouchdowns, passCompletions, passAttempts, passCompletionPercentage, passingYards, avgYardsPerPass,
								passingTouchdowns, passingInterceptions, fortyYardDash, verticalJump, benchPress, broadJump, threeCone, shuttle]
		allPlayers.append(playerInformation)
		i += 1

def GetCollegeInformation(websiteURL):
	htmlResponse = requests.get(websiteURL).text

	soup = BeautifulSoup(htmlResponse, 'lxml')

	playerInformation = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

	table = soup.find('table')

	#Only table that don't require JavaScript are accessible
	#This means in some cases no table will be found, if this is the case return the function
	#and move on to the next case
	if table is None:
		return (0, playerInformation)

	#If the table contains rushing data extract it accordingly
	if table['id'] == "rushing":
		tableFooter = table.find('tfoot')
		rushingInformation = tableFooter.findAll('td')
		
		playerInformation[0] = rushingInformation[5].string
		playerInformation[1] = rushingInformation[6].string
		playerInformation[2] = rushingInformation[7].string
		playerInformation[3] = rushingInformation[8].string

		playerInformation[4] = rushingInformation[9].string
		playerInformation[5] = rushingInformation[10].string
		playerInformation[6] = rushingInformation[11].string
		playerInformation[7] = rushingInformation[12].string
		return(1, playerInformation)

	if table['id'] == "receiving":
		tableFooter = table.find('tfoot')
		receivingInformation = tableFooter.findAll('td')

		playerInformation[4] = receivingInformation[5].string
		playerInformation[5] = receivingInformation[6].string
		playerInformation[6] = receivingInformation[7].string
		playerInformation[7] = receivingInformation[8].string

		playerInformation[0] = receivingInformation[9].string
		playerInformation[1] = receivingInformation[10].string
		playerInformation[2] = receivingInformation[11].string
		playerInformation[3] = receivingInformation[12].string
		return(1, playerInformation)

	if table['id'] == "passing":
		tableFooter = table.find('tfoot')
		passingInformation = tableFooter.findAll('td')

		playerInformation[8] = passingInformation[5].string
		playerInformation[9] = passingInformation[6].string
		playerInformation[10] = passingInformation[7].string
		playerInformation[11] = passingInformation[8].string
		playerInformation[12] = passingInformation[9].string
		playerInformation[13] = passingInformation[11].string
		playerInformation[14] = passingInformation[12].string
		return(1, playerInformation)

	return(0, playerInformation)

def GetPhysicalInformation(websiteURL):
	htmlResponse = requests.get(websiteURL).text

	soup = BeautifulSoup(htmlResponse, 'lxml')

	infoSection = soup.find('div', {'id':'info'})
	paragraphs = infoSection.findAll('p')
	heightAndWeightParagraph = paragraphs[2]
	height = heightAndWeightParagraph.findAll('span')[0].string
	weight = heightAndWeightParagraph.findAll('span')[1].string

	#Check that weight and height statistics were actually retrieved
	#if either of them are empty, just skip this player
	if(height == "" or weight == "" or height == None or weight == None):
		return (0, height, weight)

	#Format height and weight correctly
	weight = int(weight.replace('lb', ''))

	#With height, first split it into feet and inches, then convert it into a height in cms
	heightSplit = height.split('-')
	heightFeet = int(heightSplit[0])
	heightInches = int(heightSplit[1])
	heightInches += (heightFeet * 12)
	height = round(heightInches * 2.54, 0)

	return(1, height, weight)

def GetCombineInformation(draftYear, playerURL):
	websiteURL = "https://www.pro-football-reference.com/draft/" + draftYear + "-combine.htm"
	htmlResponse = requests.get(websiteURL).text

	soup = BeautifulSoup(htmlResponse, 'lxml')

	table = soup.find('table')
	tableBody = table.find('tbody')
	tableRows = tableBody.findAll('tr')

	#Create an array that will store the combine information
	playerInformation = [None, None, None, None, None, None]

	for row in tableRows:
		playerHeaderInformation = row.find('th')

		currentPlayerURL = playerHeaderInformation.find('a')

		#First need to check if there actually exists a playerURL, if there isn't just skip this row
		if currentPlayerURL == None:
			continue

		currentPlayerURL = currentPlayerURL['href']

		#If the current row is not for the correct player just skip it
		if currentPlayerURL != playerURL:
			continue

		combineInformation = row.findAll('td')

		playerInformation[0] = combineInformation[5].string
		playerInformation[1] = combineInformation[6].string
		playerInformation[2] = combineInformation[7].string
		playerInformation[3] = combineInformation[8].string
		playerInformation[4] = combineInformation[9].string
		playerInformation[5] = combineInformation[10].string

	#Check that at least one combine statistic was retrieved
	if (playerInformation == [None, None, None, None, None, None]):
		return(0, playerInformation)
	return(1, playerInformation)

def ConvertToCSV(allPlayers):
	#Create the file name to show information about the start year and end year
	filename = "NFLDraftData" + startDraftYear + "-" + endDraftYear +  ".csv"

	#Before we write to the CSV file check if there is an old one, and if so delete it
	if os.path.exists(filename):
		os.remove(filename)
		print("Deleted old data file named: " + filename)

	with open(filename, "w+") as csvFile:
		csvWriter = csv.writer(csvFile, delimiter = ',')
		csvWriter.writerow(columnHeaders)
		csvWriter.writerows(allPlayers)

ScrapeAttackYouGettingScraped(startDraftYear, endDraftYear)
import sys
import re
import os
import json
import random
import math
import copy
import cv2
import numpy as np
import csv

SETTING = 'tests.json'

########
# Superglobals

def getFiles( wildch ):
	splitName = wildch.split('/')
	mypath = os.getcwd()
	pureWildch = splitName.pop()
	fullPath = mypath + '/' + '/'.join(splitName)
	onlyfiles = [f for f in os.listdir(fullPath) if os.path.isfile(os.path.join(fullPath, f))]
	filtered = []
	for f in onlyfiles:
		if(re.match(pureWildch, f) != None):
			filtered.append(f)
	return filtered

def getBuildings( config ):
	sourceCsv = open(config['file'])
	lineReader = csv.reader(sourceCsv, delimiter=',', quotechar='|')
	buildings = []
	for row in lineReader:
		newBuilding = dict()
		for idx, title in enumerate(config['struct']):
			if title == '': continue
			if title == 'search':
				newBuilding['search'] = int(row[idx][0:1])
				newBuilding['searchType'] = row[idx][-1]
				switcher = {
					's': 2,
					'V': 3
				}
				newBuilding['searchType'] = switcher.get(newBuilding['searchType'], 1)
				continue
			if title == 'count': row[idx] = int(row[idx])
			if title == 'A': row[idx] = int(row[idx][0:1])
			if title == 'L': row[idx] = int(row[idx][0:1])
			if title == 'Z': row[idx] = int(row[idx][0:1])
			newBuilding[title] = row[idx]
		for idx in range(newBuilding['count']): buildings.append(newBuilding)
	sourceCsv.close()
	return buildings

def newTestState( ):
	state = dict()
	state['step'] = 0
	state['search'] = 0
	state['enemy'] = 0
	state['step_cnt'] = 0
	state['search_cnt'] = 0
	state['enemy_cnt'] = 0
	return state

def changeTestState( state, building, conditions ):
	state['step_cnt'] = state['step_cnt'] + 1
	state['search_cnt'] = state['search_cnt'] + building['search']
	state['enemy_cnt'] = state['enemy_cnt'] + building['A'] + building['L'] + building['Z']
	for i in range(building['search']):
		if random.randint(0, 100) < conditions['searchProb']:
			if building['search'] in conditions['searchType']:
				if building['lvl'] in conditions['searchLvl']:
					if state['step_cnt'] >= conditions['minLocs']:
						state['search'] = state['search'] + 1

def checkTestState( state, buildingCount, conditions ):
	if state['search'] >= conditions["searchCnt"]:
		if state['step_cnt'] >= conditions['minLocs']:
			return 1
	if buildingCount == 0:
			return -1
	return 0

def npMean(field, list):
	return '%.2f' % np.mean([c[field] for c in list])

def npStd(field, list):
	return '%.2f' % np.std([c[field] for c in list])

def printTestStatistics( tests ):
	failed = np.sum([c['result'] < 0 for c in tests])
	trivial = np.sum([c['step_cnt'] < 3 for c in tests])
	print('Summary\t\tfailed: '+str(failed)+'\ttrivial: '+str(trivial))
	print('Steps\t\tav: '+npMean('step_cnt', tests)+'\tdev: '+npStd('step_cnt', tests))
	print('Enemy\t\tav: '+npMean('enemy_cnt', tests)+'\tdev: '+npStd('enemy_cnt', tests))
	print('Search\t\tav: '+npMean('search_cnt', tests)+'\tdev: '+npStd('search_cnt', tests))

########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]

print('\nReading input file --> '+SETTING)
files = getFiles(SETTING)
if(len(files)!=1):
	print('\nThere is something wrong with the file '+SETTING+'!!')
	exit()

source = json.load(open(SETTING))
setting = source['general']
if(len(source)==0):
	print('\nSource file should contain JSON array.')
	exit()
print('Loading done\n')

for test in source['scenarios']:
	print('\n=========\nTest: '+test['name']+'\n=========\n')
	buildings0 = getBuildings(test['buildings'])
	res = []
	for idx in range(setting['runs']):
		state = newTestState()
		sys.stdout.write('.')
		buildings = copy.deepcopy(buildings0)
		for idx in range(len(buildings)):
			building = buildings.pop(random.randint(0, len(buildings)-1))
			changeTestState(state, building, test['conditions'])
			state["result"] = checkTestState(state, len(buildings), test['conditions'])
			if state["result"] != 0:
				res.append(state)
				break
	print('\nTest ended ('+str(setting['runs'])+' runs)')
	printTestStatistics(res)

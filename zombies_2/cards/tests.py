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

if(len(source)==0):
	print('\nSource file should contain JSON array.')
	exit()
print('\nProcessing')
if(not os.path.isdir(DIRECTORY)):
    os.mkdir(DIRECTORY)

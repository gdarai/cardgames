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
from pyexcel_ods import get_data
from six import string_types

########
# Globals
canPrint = True

SETTING = 'cards.json'
TASK = 'prototype'
DIRECTORY = 'print'
BREAK_CHAR = '|'
FIXED_SPACE = '_'
Y_SPACE = 5
TEX_FILE = 'cards.tex'
A4_WIDTH = 21
A4_MARGIN = 1.5
RESIZE_FILE = 'resize.png'
RESIZE_HEIGHT = 300
SVG_DIRECTORY = 'svg'
PNG_DIRECTORY = 'png'
ALLOWED_PROCESSES = [
	'EXPORT_TABLE',
	'CONVERT_SVGS',
	'PRINT_CARDS',
	'PRINT_A_CARD',
	'COMBINE_PNGS',
	'SPLIT_TEX',
	'ADD_TEXT',
	'TERMINATE',
];

A4_TEXT_W = A4_WIDTH - (2*A4_MARGIN)
COUNTERS = dict()
IMAGES = dict()
IMAGES[TEX_FILE] = list()

FONTS = dict()
FONTS['HERSHEY_SIMPLEX'] = cv2.FONT_HERSHEY_SIMPLEX
FONTS['HERSHEY_PLAIN'] = cv2.FONT_HERSHEY_PLAIN
FONTS['HERSHEY_DUPLEX'] = cv2.FONT_HERSHEY_DUPLEX
FONTS['HERSHEY_COMPLEX'] = cv2.FONT_HERSHEY_COMPLEX
FONTS['HERSHEY_TRIPLEX'] = cv2.FONT_HERSHEY_TRIPLEX
FONTS['HERSHEY_COMPLEX_SMALL'] = cv2.FONT_HERSHEY_COMPLEX_SMALL
FONTS['HERSHEY_SCRIPT_SIMPLEX'] = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
FONTS['HERSHEY_SCRIPT_COMPLEX'] = cv2.FONT_HERSHEY_SCRIPT_COMPLEX

printLog = dict();

def ALIGN_LEFT(xmin, xmax, imgwidth):
	return xmin
def ALIGN_RIGHT(xmin, xmax, imgwidth):
	return xmax - imgwidth
def ALIGN_CENTER(xmin, xmax, imgwidth):
	return xmin + int((xmax - xmin - imgwidth) / 2)
ALIGN = dict()
ALIGN['left'] = ALIGN_LEFT
ALIGN['right'] = ALIGN_RIGHT
ALIGN['center'] = ALIGN_CENTER

def VALTYPE_INT(variable):
	return isinstance(variable, int)
def VALTYPE_FLOAT(variable):
	return isinstance(variable, (float))
def VALTYPE_IMG(variable):
	return isinstance(variable, complex)
def VALTYPE_STR(variable):
	return isinstance(variable, string_types)
def VALTYPE_LIST(variable):
	return isinstance(variable, list)

VALTYPE = dict()
VALTYPE['int'] = VALTYPE_INT
VALTYPE['float'] = VALTYPE_FLOAT
VALTYPE['img'] = VALTYPE_IMG
VALTYPE['string'] = VALTYPE_STR
VALTYPE['list'] = VALTYPE_LIST

COMB_SHAPE = dict()
COMB_SHAPE['row'] = { "cross": 1, "size": 0, "increment": +1, "center": False }
COMB_SHAPE['rowC'] = { "cross": 1, "size": 0, "increment": +1, "center": True }
COMB_SHAPE['col'] = { "cross": 0, "size": 1, "increment": +1, "center": False }
COMB_SHAPE['colC'] = { "cross": 0, "size": 1, "increment": +1, "center": True }

class ANALYZE_CONST:
	def __init__(self, value):
		self.value = str(value)
	def nextVal(self):
		return self.value

def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class ANALYZE_REG_CONST:
	def __init__(self, value):
		self.value = value
	def getValue(self, index, restValue):
		return self.value + restValue
	def getCount(self):
		return 1

class ANALYZE_REG_RANGE:
	def __init__(self, minV, maxV):
		if representsInt(minV) and representsInt(maxV):
			self.type = 'int'
			self.minV = int(minV)
			self.count = int(maxV) - self.minV + 1
		elif len(minV) == 1 and len(maxV) == 1 :
			self.type = 'ord'
			self.minV = ord(minV)
			self.count = ord(maxV) - self.minV + 1
		else:
			print('!! Regexp error, range ['+minV+'-'+maxV+'] is not understanded')
			exit()
	def getValue(self, index, restValue):
		value = self.minV + index
		if self.type == 'int':
			return str(value) + restValue
		return chr(value)
	def getCount(self):
		return self.count

class ANALYZE_REG_ITEMIZE:
	def __init__(self, source):
		self.source = source
		if len(self.source) < 1:
			print('!! Regexp error, itemize ['+str(source)+'] is not understanded')
			exit()
	def getValue(self, index, restValue):
		value = self.source[index]
		return value + restValue
	def getCount(self):
		return len(self.source)

class ANALYZE_REG_LINK:
	def __init__(self, linkName, source):
		self.linkName = linkName
		self.source = source
	def getValue(self, index, restValue):
		value = self.source[self.linkName].getValue(index)
		return value + restValue
	def getCount(self):
		return self.source[self.linkName].getCount()

class ANALYZE_REG_COND:
	def __init__(self, linkName, ifNot, source):
		self.linkName = linkName
		self.ifNot = ifNot
		self.source = source
	def getValue(self, index, restValue):
		value = self.source[self.linkName].getValue(index)
		if value == '':
			return self.ifNot
		return restValue
	def getCount(self):
		return self.source[self.linkName].getCount()

class ANALYZE_REG_FULL:
	def __init__(self, script, counterName, isMaster):
		self.script = script
		self.counterName = counterName
		self.isMaster = isMaster
		COUNTERS[counterName] = 0
		maxIndex = 1
		for oneItem in script:
			maxIndex = maxIndex * oneItem.getCount()
		self.maxIndex = maxIndex
	def nextVal(self):
		index = COUNTERS[self.counterName]
		if self.isMaster == True:
			COUNTERS[self.counterName] = index + 1
		index = index % self.maxIndex
		value = ''
		for sc in reversed(self.script):
			count = sc.getCount()
			idx = index % count
			value = sc.getValue(idx, value)
		return value

class ANALYZE_LIST:
	def __init__(self, values, counterName, isMaster):
		self.values = values
		self.counterName = counterName
		self.isMaster = isMaster
		COUNTERS[counterName] = 0
	def nextVal(self):
		index = COUNTERS[self.counterName]
		if self.isMaster == True:
			COUNTERS[self.counterName] = index + 1
		index = index % len(self.values)
		return str(self.values[index])
	def getValue(self, index):
		index = index % len(self.values)
		return str(self.values[index])
	def getCount(self):
		return len(self.values)

def ANALYZE_REG(regStr, counterName, isMaster, source):
	script = list()
	while regStr != '':
		nextStr = ''
		if regStr[0] == '[':
			nextStr = (regStr[1:].split(']'))[0]
			regStr = regStr[len(nextStr)+2:]
			regSplit = nextStr.split('-')
			if len(regSplit) == 2:
				script.append(ANALYZE_REG_RANGE(regSplit[0], regSplit[1]))
			else:
				script.append(ANALYZE_REG_ITEMIZE(nextStr))
		elif regStr[0] == '{':
			linkName = (regStr[1:].split('}'))[0]
			regStr = regStr[len(linkName)+2:]
			script.append(ANALYZE_REG_LINK(linkName, source))
		elif regStr[0] == '?':
			linkName = (regStr[2:].split('}'))[0]
			regStr = regStr[len(linkName)+2:]
			ifNot = (regStr[2:].split('}'))[0]
			regStr = regStr[len(ifNot)+3:]
			script.append(ANALYZE_REG_COND(linkName, ifNot, source))
		else:
			nextStr = (re.split('[\[\{]', regStr))[0]
			regStr = regStr[len(nextStr):]
			script.append(ANALYZE_REG_CONST(nextStr))
	return ANALYZE_REG_FULL(script, counterName, isMaster)

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
# Printing
def writeLine(f, intention, text):
    f.write('\t'*intention+text+'\n');

def checkField(cardName, props, fieldName, values, defaultVal):
	return checkFieldRaw('Card', cardName, props, fieldName, values, defaultVal)

def checkFieldRaw(objectType, objectName, props, fieldName, values, defaultVal):
	if fieldName not in props:
		if defaultVal is None:
			print('!! '+objectType+' '+objectName+' is missing mandatory field '+fieldName)
			exit()
		props[fieldName] = defaultVal
		return props[fieldName]
	else:
		value = props[fieldName]
		if isinstance(values, list):
			if value not in values:
				print('!! '+objectType+' '+objectName+' field '+fieldName+' must be one of '+str(values))
				exit()
		else:
			if not VALTYPE[values](value):
				print('!! '+objectType+' '+objectName+' field '+fieldName+' must be '+values)
				exit()
	return props[fieldName]

def int_to_bool_list(num, maxL):
    return [bool(num & (1<<n)) for n in range(maxL)]

def addLine(out, size, newLine, data):
	newLineString = ' '.join(newLine)
	out.append(newLineString)
	lnSize, _ = cv2.getTextSize(newLineString, data['font'], 1, data['line'])
	size[0] = max(size[0], lnSize[0])
	size[1] = size[1] + lnSize[1]

def getNewTextAnalysis(index, data):
	indexSplit = int_to_bool_list(index, data['maxBitIdx'])
	out = list()
	size = [0, 0]
	indexInUse = 0
	for lnIdx in range(0, len(data['text'])):
		ln = data['text'][lnIdx]
		if lnIdx > 0:
			addLine(out, size, newLine, data)
		newLine = list()

		for wIdx in range(0, len(ln)):
			if wIdx == 0:
				newLine.append(ln[wIdx])
			else:
				if indexSplit[indexInUse]:
					addLine(out, size, newLine, data)
					newLine = list()
				newLine.append(ln[wIdx])
				indexInUse = indexInUse + 1
	if len(newLine) > 0:
		addLine(out, size, newLine, data)

	scale = [1, 1];
	if size[0] > 0:
		scale[0] = data['size'][0] / size[0];
	spacing = (len(out) - 1) * data['space'];
	if size[1] > 0:
		scale[1] = (data['size'][1] - spacing) / size[1];

	result = dict()
	result['score'] = min(scale[0], scale[1])
	result['text'] = out
	return result

def analyzeTextSplit(theText, tgtSize, yspace, font, lineTh, separator):
	data = dict()
	data['size'] = [float(tgtSize[1][0]-tgtSize[0][0]), float(tgtSize[1][1]-tgtSize[0][1])]
	data['space'] = yspace
	data['font'] = font
	data['line'] = lineTh
	data['text'] = theText.split(separator)
	data['maxBitIdx'] = 1
	for i in range(0, len(data['text'])):
		data['text'][i] = data['text'][i].split(' ')
		data['maxBitIdx'] = data['maxBitIdx'] + len(data['text'][i]) - 1
	data['maxIdx'] = 2 ** data['maxBitIdx']

	bestAnalysis = dict()
	nextIndex = 0
	bestAnalysis['score'] = 0
	bestAnalysis['text'] = theText.split(separator)
	while nextIndex < data['maxIdx']:
		newAnalysis = getNewTextAnalysis(nextIndex, data)
		if newAnalysis['score'] > bestAnalysis['score']:
			bestAnalysis = newAnalysis
		nextIndex = nextIndex + 1

	return bestAnalysis['text']

def fixRGBA(img):
	# RGB to RGBA
	if img.shape[2] == 3:
		# First create the image with alpha channel
		rgba = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
		# Then assign the mask to the last channel of the image
		rgba[:, :, 3] = np.zeros(img.shape[:2], np.uint8)
		img = rgba
	return img

# COMBINE_PNGS
def combinePNGs(setting, outName):
	srcImgs = dict()
	skip = checkFieldRaw('CombinePNGs', outName, setting, '_skip', 'list', [''])

	config = checkFieldRaw('CombinePNGs', outName, setting, '_shape', list(COMB_SHAPE.keys()), 'rowC')
	config = COMB_SHAPE[config]
	sizeCoor = config['size']
	isRow = sizeCoor == 0

	cross = 0;
	size = 0;

	for paramName in setting['_formula']:
		if paramName not in srcImgs:
			fileName = setting[paramName].nextVal()
			if fileName in skip:
				srcImgs[paramName] = None
				continue
			srcImgs[paramName] = fixRGBA(cv2.imread(fileName))
		imShape = srcImgs[paramName].shape
		size += imShape[config['size']]
		cross = max(cross, imShape[config['cross']])

	newImg = np.zeros((cross, size, 4) if isRow else (size, cross, 4), np.uint8)
	notRev = config['increment'] > 0
	formula = setting['_formula'] if notRev else reversed(setting['_formula'])
	dirSize = 0

	for paramName in formula:
		img = srcImgs[paramName]
		if img is None:
			continue
		imShape = img.shape
		w = [dirSize, dirSize + imShape[0]] if isRow else [0, imShape[0]]
		h = [0, imShape[1]] if isRow else [dirSize, dirSize + imShape[1]]
		newImg[h[0]:h[1], w[0]:w[1]] = img
		dirSize += imShape[sizeCoor]

	cv2.imwrite(outName, newImg[:, :, :3])
	return

def printCsvTable(setting, name):
	targetFile = checkFieldRaw('Export', '??', setting, 'target', 'string', None)
	sheetName = checkFieldRaw('Export', setting['target'], setting, 'sheet', 'string', None)
	tableIdx = checkFieldRaw('Export', setting['target'], setting, 'table', 'int', 1)
	tableIdxMem = tableIdx
	operation = checkFieldRaw('Export', setting['target'], setting, '_opp', 'string', 'w')
	skipTitle = checkFieldRaw('Export', setting['target'], setting, 'skipTitle', 'int', 1)

	if '_sourceOds' not in setting:
		print('!! No source ODS file specified yet, need _sourceOds entry key.')
		exit()

	if sheetName not in setting['_sourceOds']:
		print('!! The source ODS file does not contain sheet '+sheetName)
		print(setting['_sourceOds'].keys())
		exit()

	sheet = setting['_sourceOds'][sheetName]
	maxLen = np.max([len(ln) for ln in sheet])

	if maxLen == 0:
		print('!! The sheet '+sheetName+' has no content')
		exit()

	table = []
	keepTitle = skipTitle != 1
	lastWasNotTable = True

	for ln in sheet:
		res = 0
		isTheTable = tableIdx == 0
		isTableLine = len(ln) == maxLen
		if lastWasNotTable:
			res = 100
			if isTableLine:
				res = 110
				lastWasNotTable = False
				tableIdx = tableIdx - 1
				if tableIdx == 0: isTheTable = True
				if isTheTable and keepTitle:
					res = 111
					table.append(ln)
		else:
			res = 200
			if isTableLine:
				res = 210
				if isTheTable:
					res = 211
					table.append(ln)
			else:
				res = 220
				lastWasNotTable = True


	if len(table) == 0:
		print('!! The sheet '+sheetName+' has no table '+str(tableIdxMem))
		exit()

	firstNonempty = 0
	while table[0][firstNonempty] == '' and firstNonempty<len(table[0]): firstNonempty = firstNonempty + 1

	f = open(targetFile,setting['_opp'])
	for line in table:
		cells = line[firstNonempty:]
		strCells = ','.join(map(str, cells))
		writeLine(f,0,strCells)
	f.close()

def printCardFile(setting, name, single = False):
	cardName = setting['_card']
	img = fixRGBA(cv2.imread(cardName+'.png'))

	# --- Print log entry for this card ---
	log_entry = dict()
	log_entry['cardName'] = cardName + '.png'
	log_entry['outDict'] = setting['_out'] if '_out' in setting else None
	log_entry['components'] = []

	for fieldName in setting['_cardParamNames']:
		if fieldName not in setting:
			continue

		props = setting['_cardParams'][fieldName]
		checkField(cardName, props, 'type', ['text', 'img'], 'text')
		if props['type'] == 'text':
			checkField(cardName, props, 'position', 'list', None)
			checkField(cardName, props, 'padding', 'list', [[0, 0], [0, 0]])
			checkField(cardName, props, 'font', list(FONTS.keys()), list(FONTS.keys())[0])
			checkField(cardName, props, 'align', list(ALIGN.keys()), list(ALIGN.keys())[0])
			checkField(cardName, props, 'line', 'int', 1)
			checkField(cardName, props, 'fixed', 'int', 1)
			checkField(cardName, props, 'color', 'list', [0, 0, 0])
			checkField(cardName, props, 'fixed_space', 'string', FIXED_SPACE)

			font = FONTS[props['font']]
			thickness = props['line']
			color = props['color']
			tgtPos0 = props['position']
			tgtPos1 = props['padding']
			tgtPos = [np.add(tgtPos0[0], tgtPos1[0]), np.subtract(tgtPos0[1],tgtPos1[1])]

			theText = setting[fieldName].nextVal()
			if props['fixed'] == 1:
				theText = theText.split(setting['_break'])
			else:
				theText = analyzeTextSplit(theText, tgtPos, setting['_yspace'], font, thickness, setting['_break'])

			align = ALIGN[props['align']]
			size = []
			sizeCheck = 0
			sizeTotal = [0, -setting['_yspace']]
			for ln0 in theText:
				ln = ln0.replace(props['fixed_space'], ' ')
				oneSize, _ = cv2.getTextSize(ln, font, 1, thickness)
				size.append(oneSize)
				sizeCheck = max(sizeCheck, oneSize[1]*oneSize[0])
				sizeTotal[0] = max(sizeTotal[0], oneSize[0])
				sizeTotal[1] = sizeTotal[1]+oneSize[1]+setting['_yspace']
			if sizeCheck == 0 :
				print('!! text-to-insert is empty ... skipping.')
				continue
			imgScale = min((float(tgtPos[1][1]) - tgtPos[0][1]) / sizeTotal[1], (float(tgtPos[1][0]) - tgtPos[0][0]) / sizeTotal[0])
			finSizeY = int(imgScale * sizeTotal[1])
			oneSizeY = int(finSizeY / len(theText))
			shiftY = oneSizeY

			for ln0 in theText:
				ln = ln0.replace(props['fixed_space'], ' ')
				finSize, _ = cv2.getTextSize(ln, font, imgScale, thickness)
				finPos = (align(tgtPos[0][0], tgtPos[1][0], finSize[0]), ALIGN_CENTER(tgtPos[0][1], tgtPos[1][1], finSizeY)+shiftY)
				img = cv2.putText(img, ln, finPos, font, imgScale, color, thickness, cv2.LINE_AA)
				# --- Log this text component ---
				log_entry['components'].append({
					'type': 'text',
					'text': ln,
					'font': props['font'],
					'thickness': thickness,
					'align': props['align'],
					'position': finPos
				})
				shiftY = shiftY + oneSizeY
		elif props['type'] == 'img':
			fileName = setting[fieldName].nextVal()
			if fileName == '' :
				print('!! image-to-insert is empty ... skipping.')
				continue
			checkField(cardName, props, 'position', 'list', None)
			checkField(cardName, props, 'mask', 'list', [0, 0])
			checkField(cardName, props, 'maskTolerance', 'float', 0.05)
			checkField(cardName, props, 'useMask', 'string', 'True')
			pos = props['position']
			size = [pos[1][0]-pos[0][0], pos[1][1]-pos[0][1]]
			pos0 = pos[0]
			if os.path.exists(fileName) == False:
				print('Trying to read file '+fileName+' which does not exist')
				print(props)
			theImg = fixRGBA(cv2.imread(fileName))
			imgSize = theImg.shape[:2]
			imgScale = min(float(size[0])/imgSize[1], float(size[1])/imgSize[0])
			theImg = cv2.resize(theImg, None, fx=imgScale, fy=imgScale)
			imgSize = theImg.shape[:2]
			pastePos = [pos0[0]+int((size[0]-imgSize[1])/2), pos0[1]+int((size[1]-imgSize[0])/2)]
			thePaste = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
			thePaste[pastePos[1]:pastePos[1]+imgSize[0], pastePos[0]:pastePos[0]+imgSize[1]] = theImg
			if props['useMask'] == 'True':
				maskPos = props['mask']
				maskTol = props['maskTolerance']

				hsvImg = cv2.cvtColor(theImg, cv2.COLOR_BGR2HSV)
				thePixel = hsvImg[maskPos[0], maskPos[1]]
				thePixel0 = hsvImg[maskPos[0], maskPos[1]]-(125*maskTol)
				thePixel1 = hsvImg[maskPos[0], maskPos[1]]+(125*maskTol)

				theMask = np.full((img.shape[0], img.shape[1]), 4, dtype=np.uint8)
				hsvImg = cv2.cvtColor(theImg, cv2.COLOR_BGR2HSV)
				subMask = cv2.bitwise_not(cv2.inRange(hsvImg, thePixel0, thePixel1))
				theMask[pastePos[1]:pastePos[1]+imgSize[0], pastePos[0]:pastePos[0]+imgSize[1]] = subMask

				maskedImg = cv2.bitwise_or(thePaste, thePaste, mask=theMask)
				maskedMainImg = cv2.bitwise_or(img, img, mask=cv2.bitwise_not(theMask))

				img = cv2.bitwise_or(maskedMainImg, maskedImg)
				# --- Log this image component with mask ---
				log_entry['components'].append({
					'type': 'img',
					'file': fileName,
					'position': pastePos,
					'size': imgSize,
					'useMask': True,
					'maskPos': maskPos,
					'maskTolerance': maskTol
				})
			else:
				img[pastePos[1]:pastePos[1]+imgSize[0], pastePos[0]:pastePos[0]+imgSize[1]] = theImg
				# --- Log this image component without mask ---
				log_entry['components'].append({
					'type': 'img',
					'file': fileName,
					'position': pastePos,
					'size': imgSize,
					'useMask': False
				})
		else:
			print('!! Card '+setting['_card']+' field '+fieldName+' is of unknown type.')
			exit()

	if single == True:
		cv2.imwrite(DIRECTORY+'/'+RESIZE_FILE, img[:, :, :3])
		resizeCmd = 'convert '+DIRECTORY+'/'+RESIZE_FILE+ ' -resize '+str(setting['_resize'])+' '+name
		os.system(resizeCmd)
	else:
		fileName = DIRECTORY+'/'+name+'.png'
		cv2.imwrite(DIRECTORY+'/'+RESIZE_FILE, img[:, :, :3])
		resizeCmd = 'convert '+DIRECTORY+'/'+RESIZE_FILE+ ' -resize '+str(setting['_resize'])+' '+fileName
		os.system(resizeCmd)
		imageDict = dict()
		imageDict['file'] = name
		imageDict['onOneLine'] = setting['_onOneLine']
		imageDict['randomize'] = setting['_randomize']
		imageDict['task'] = 'print'
		IMAGES[setting['_out']].append(imageDict)

	# --- Store the log entry for this card ---
	if name not in printLog:
		printLog[name] = log_entry
	else:
		# If multiple cards with same name, append as a list
		if isinstance(printLog[name], list):
			printLog[name].append(log_entry)
		else:
			printLog[name] = [printLog[name], log_entry]
	return

def addPrintSeparator(setting):
	imageDict = dict()
	imageDict['file'] = setting['_out']
	imageDict['onOneLine'] = setting['_onOneLine']
	imageDict['randomize'] = setting['_randomize']
	imageDict['task'] = 'split'
	IMAGES[setting['_out']].append(imageDict)
	return

def addPrintText(setting):
	imageDict = dict()
	imageDict['file'] = setting['_out']
	imageDict['task'] = 'text'
	imageDict['text'] = setting['_text']
	imageDict['size'] = checkFieldRaw('TextPrint', '??', setting, '_size', 'string', 'Large')
	IMAGES[setting['_out']].append(imageDict)
	return


########
# Process

def readOneParameter(setting, paramName, paramSource):
	newParam = None
	if isinstance(paramSource, dict) == True:
		if 'value' in paramSource:
			newParam = ANALYZE_CONST(paramSource['value'])
		elif 'reg' in paramSource:
			counterName = len(list(COUNTERS.keys()))
			isMaster = True
			if 'counter' in paramSource:
				counterName = paramSource['counter']
			if 'isMaster' in paramSource:
				isMaster = paramSource['isMaster']
			newParam = ANALYZE_REG(paramSource['reg'], counterName, isMaster, setting)
		elif 'list' in paramSource:
			counterName = len(list(COUNTERS.keys()))
			isMaster = True
			if 'counter' in paramSource:
				counterName = paramSource['counter']
			if 'isMaster' in paramSource:
				isMaster = paramSource['isMaster']
			newParam = ANALYZE_LIST(paramSource['list'], counterName, isMaster)
			setting['_count'] = len(paramSource['list'])
		else:
			print('!! Parameter '+paramName+' is wrongly formated.')
			exit()

	else:
		newParam = ANALYZE_CONST(paramSource)

	setting[paramName] = newParam
	return setting

def printSvgFile(setting, fileName):
	pngFileName = fileName[:-3]+'png'
	pngPath = PNG_DIRECTORY+'/'+pngFileName
	svgPath = SVG_DIRECTORY+'/'+fileName
	print(svgPath+' --> '+pngPath)
	command = f'inkscape "{svgPath}" --export-type=png --export-filename="{pngPath}"'
	if setting["_resize"] != 0:
		command = command + " --export-width="+str(setting["_resize"])
	os.system(command)

def readSimpleParameter(setting, source, name, default = None):
	if name in source:
		setting[name] = source[name]
	elif default != None:
		setting[name] = default

def readParameters(setting, source):
	if '_process' in source:
		setting['_process'] = source['_process'].upper()
		if any(setting['_process'] in s for s in ALLOWED_PROCESSES) == False:
			print('!! _process '+setting['_process']+' is unknown!')
			exit()

	if setting['_process'] == 'CONVERT_SVGS':
		readSimpleParameter(setting, source, '_resize', 0)
		return setting;

	if '_sourceOds' in source:
		setting['_process'] = 'EXPORT_TABLE'
		fileName = source['_sourceOds']
		print('!! Swapping ods input to file '+fileName)
		odsFiles = getFiles(fileName)
		if len(odsFiles) != 1:
			print('!! Isn\'t the input file '+fileName+' missing?')
			exit()
		setting['_sourceOds'] = get_data(fileName)

	if setting['_process'] == 'EXPORT_TABLE':
		setting['_cardParamNames'] = []
		for paramName in setting['_exportTableParams']:
			readSimpleParameter(setting, source, paramName)

	readSimpleParameter(setting, source, '_onOneLine')

	if '_card' in source:
		readSimpleParameter(setting, source, '_process', 'PRINT_CARDS')
		if setting['_card'] != '':
			print('!! multiple cards assinged in this branch, rewriting '+setting['_card']+' with '+source['_card'])
		setting['_card'] = source['_card']
		pngFiles = getFiles(setting['_card']+'.png')
		jsonFiles = getFiles(setting['_card']+'.json')
		if len(pngFiles) != 1 or len(jsonFiles) != 1:
			print('!! The cards files for '+setting['_card']+' (png/json) are wrong. There must be exactly one of each.')
			exit()
		setting['_cardParams'] = json.load(open(setting['_card']+'.json'))
		setting['_cardParamNames'] = list(setting['_cardParams'].keys())

	# if '_lists' in source:
	# 	for listName in source['_lists']:
	# 		setting['_lists']['_fixedLists'] = source[listName]

	if '_list' in source:
		newLists = source['_list'].keys()
		for listName in newLists:
			theList = source['_list'][listName]
			if listName in setting['_lists']:
				print('!! Overwriting list '+listName+': '+str(theList))
			else:
				print(' - Adding list '+listName+': '+str(theList))
			setting['_lists'][listName] = list(theList)

	for listName in setting['_lists']:
		if listName in source:
			theList = setting['_lists'][listName]
			theData = source[listName]
			if isinstance(theData, list) == True:
				expLen = len(theList)
				if len(theData) != expLen:
					print('!! Key List '+listName+' should be '+expLen+' long, but this may be intentional.')
					expLen = min(expLen, len(theData))
				for idx in range(0, expLen):
					setting = readOneParameter(setting, theList[idx], theData[idx])
			elif isinstance(theData, string_types) == True:
				sourceCsv = open(theData, 'r')
				lineReader = csv.reader(sourceCsv, delimiter=',', quotechar='|')
				tableData = []
				print(lineReader)
				for row in lineReader:
					tableData.append(row)
				tableData = np.array(tableData)
				sourceCsv.close()

				expLen = len(theList)
				if tableData.shape[1] == (expLen+1):
					print('(i) File loading with counts, _count is the first column.')
					counts = tableData[:, 0]
					tableDataOrig = tableData[:, 1:]
					tableData = np.tile(tableDataOrig[0], (int(counts[0]), 1))
					for idx in range(1, len(counts)):
						tableData = np.append(tableData, np.tile(tableDataOrig[idx], (int(counts[idx]), 1)), axis=0)

				tableData = tableData.transpose()
				if tableData.shape[0] != expLen:
					expLen = min(expLen, tableData.shape[0])
					print('!! Key List '+listName+' should be '+str(expLen)+' long, but this may be intentional.')
				for idx in range(0, tableData.shape[0]):
					oneData = dict()
					oneData['list'] = list(tableData[idx])
					setting = readOneParameter(setting, theList[idx], oneData)
			else:
				print('!! Key List '+listName+' must contain array or existing filename.')
				exit()

	if setting['_process'] == 'COMBINE_PNGS':
		if '_formula' not in source:
			print('!! Config must contain core list parameter \'_formula\'.')
			exit()
		setting['_cardParamNames'] = source['_formula']
		setting['_formula'] = source['_formula']

		readSimpleParameter(setting, source, '_skip')
		readSimpleParameter(setting, source, '_shape')

		if '_out' not in source:
			print('!! Config must contain core string parameter \'_out\'.')
			exit()
		setting = readOneParameter(setting, '_out', source['_out'])
		for paramName in setting['_cardParamNames']:
			if paramName in source:
				setting = readOneParameter(setting, paramName, source[paramName])
	if setting['_process'] == 'SPLIT_TEX':
		readSimpleParameter(setting, source, '_out')

	if setting['_process'] == 'ADD_TEXT':
		readSimpleParameter(setting, source, '_out')
		readSimpleParameter(setting, source, '_size')
		readSimpleParameter(setting, source, '_text')

	if setting['_process'] == 'PRINT_CARDS':
		for paramName in setting['_cardParamNames']:
			if paramName in source:
				setting = readOneParameter(setting, paramName, source[paramName])

		readSimpleParameter(setting, source, '_count')
		readSimpleParameter(setting, source, '_resize')
		readSimpleParameter(setting, source, '_break')
		readSimpleParameter(setting, source, '_yspace')
		if '_out' in source:
			newFile = source['_out']
			setting['_out'] = newFile
			print('!! Swapping output to file '+newFile)
			if newFile not in IMAGES:
				IMAGES[newFile] = list()
		if '_randomize' in source:
			setting['_randomize'] = source['_randomize'] == 'True'

	if setting['_process'] == 'PRINT_A_CARD':
		for paramName in setting['_cardParamNames']:
			if paramName in source:
				setting = readOneParameter(setting, paramName, source[paramName])

		readSimpleParameter(setting, source, '_resize')
		readSimpleParameter(setting, source, '_break')
		readSimpleParameter(setting, source, '_yspace')

		setting = readOneParameter(setting, '_out', source['_out'])

	return setting

def checkParameters(setting):
	missing = list()

	for paramName in setting['_cardParamNames']:
		if paramName not in setting:
			missing.append(paramName)
	return missing

def readAndProcessList(level, name, sourceList, setting):
	index = 0
	for s in sourceList:
		index = index + 1
		newName = name + '-' + str(index);
		if '_key' in s:
			newName = name + '-' + s['_key']
		readAndProcess(level, newName, s, copy.deepcopy(setting))

def readAndProcess(level, name, source, setting):
	separator = '  ' * level
	print(separator+name)
	newLevel = level + 1
	setting = readParameters(setting, source)
	print(setting['_process'])
	if '_sub' in source:
		readAndProcessList(newLevel, name, source['_sub'], copy.deepcopy(setting))
	else:
		if setting['_process'] == 'TERMINATE':
			exit()

		if setting['_process'] == 'CONVERT_SVGS':
			svgFiles = getFiles(SVG_DIRECTORY+'/.*.svg')
			print('\nConverting '+str(len(svgFiles))+' svg''s')
			for fileName in svgFiles:
				printSvgFile(setting, fileName)
			return

		if setting['_process'] == 'EXPORT_TABLE':
			missing = checkParameters(setting)
			if len(missing) > 0:
				print(separator+' -Missing '+str(missing))
			print(separator+' -Printing table')
			printCsvTable(setting, name)
			return

		if setting['_process'] == 'COMBINE_PNGS':
			missing = checkParameters(setting)
			if len(missing) > 0:
				print(separator+' -Missing '+str(missing))

			for idx in range(0, setting['_count']):
				newFileName = setting['_out'].nextVal()
				print(separator+' -Combining PNGs row '+str(idx)+' (to '+newFileName+')')
				combinePNGs(setting, newFileName)
			return

		if setting['_process'] == 'SPLIT_TEX':
			addPrintSeparator(setting)
			return

		if setting['_process'] == 'ADD_TEXT':
			addPrintText(setting)
			return

		if setting['_card'] == '':
			print('!! Should do the printing now, but still missing the mandatory "_card" key.')
			exit()

		missing = checkParameters(setting)
		if len(missing) > 0:
			print(separator+' -Missing '+str(missing))

		if setting['_process'] == 'PRINT_A_CARD':
			for idx in range(0, setting['_count']):
				newFileName = setting['_out'].nextVal()
				print(separator+' -Printing img '+str(idx)+' ('+newFileName+')')
				printCardFile(setting, newFileName, True)
			return

		print(separator+' -Printing '+str(setting['_count'])+'x')
		for idx in range(0, setting['_count']):
			printCardFile(setting, name+'_'+str(idx))

def printImagesSelection(IMAGES):
	if len(IMAGES) == 0:
		return
	onOneLine = IMAGES[0]['onOneLine']
	doRandom = IMAGES[0]['randomize']
	imgWidth = str(A4_TEXT_W / onOneLine)
	if doRandom:
		random.shuffle(IMAGES)
	for img in IMAGES:
		if img['onOneLine'] != onOneLine:
			onOneLine = img['onOneLine']
			writeLine(f,0,'\\newline')
			imgWidth = str(A4_TEXT_W / onOneLine)
		writeLine(f,1,'\\includegraphics[width='+imgWidth+'cm]{'+DIRECTORY+'/'+img['file']+'}')

def printImages(IMAGES):
	pick = list();
	onOneLine = IMAGES[0]['onOneLine']
	doRandom = IMAGES[0]['randomize']
	for IMG in IMAGES:
		if(IMG['task'] == 'print' and IMG['onOneLine'] == onOneLine and IMG['randomize'] == doRandom):
			pick.append(IMG)
		else:
			printImagesSelection(pick)
			if IMG['task'] == 'text':
				print('\nPrinting a text')
				writeLine(f,0,'{\\'+IMG['size']+' '+IMG['text']+'}')
				continue

			pick = list()
			if IMG['task'] == 'print':
				pick.append(IMG)
				onOneLine = pick[0]['onOneLine']
				doRandom = pick[0]['randomize']
			elif IMG['task'] == 'split':
				writeLine(f,0,'\\newline')
				writeLine(f,0,'\\newline')
	printImagesSelection(pick)

########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]
if(len(sys.argv) > 2):
	TASK = sys.argv[2]

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

setting = dict()
setting['_count'] = 1
setting['_resize'] = RESIZE_HEIGHT
setting['_break'] = BREAK_CHAR
setting['_yspace'] = Y_SPACE
setting['_onOneLine'] = 4
setting['_cardParams'] = dict()
setting['_card'] = ''
setting['_lists'] = dict()
setting['_out'] = TEX_FILE
setting['_randomize'] = True
setting['_process'] = 'PRINT_CARDS'
setting['_exportTableParams'] = ['sheet', 'table', 'target', '_opp', 'skipTitle']

readAndProcessList(0, "INPUT", source, setting)

for fileName in IMAGES.keys():
	IMGS = IMAGES[fileName]
	if len(IMGS) == 0 :
		print('\n!! There are NO images to print, skipping PDF print '+fileName)
		continue

	print('\nPrinting '+fileName+' ('+str(len(IMGS))+') with pdf latex\n')

	f = open(fileName,'w')
	writeLine(f,0,'\\documentclass[a4paper]{article}')
	writeLine(f,0,'\\usepackage[a4paper, margin='+str(A4_MARGIN)+'cm]{geometry}')
	writeLine(f,0,'\\usepackage{graphicx}')
	writeLine(f,0,'\\graphicspath{ {./cards/} }')
	writeLine(f,0,'\\setlength{\\parindent}{0cm}')
	writeLine(f,0,'\\begin{document}')
	printImages(IMGS)
	writeLine(f,0,'\end{document}')
	f.close()

	os.system('pdflatex '+fileName)

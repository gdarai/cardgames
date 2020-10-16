#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os

########
# Globals
canPrint = True;
fileNameBase = 'rules';
########
# Superglobals

def printError(text):
    print('!ERR '+text);
    canPrint = False;

def printWarning(text):
    print('WARN '+text);

def writeLine(f, intention, text):
    f.write('\t'*intention+text+'\n');

def writeLineCondition(f, intention, textNo, textYes, condition):
    if(condition):
        f.write('\t'*intention+textYes+'\n');
    else:
        f.write('\t'*intention+textNo+'\n');

def    writeLineBlocks(f,intention, texts):
    allBut = texts[0:-1]
    last = texts[-1]
    for l in allBut:
        writeLine(f, intention, l+',')
        writeLine(f, intention, last)

def parseLine(line):
    line = re.sub(r"\s+#\s+","#", line)
    line = re.sub(r"\n","", line)
    line = re.sub(r"\r","", line)
    return line.split("#")

def expandCzechLetters(line):
    line = re.sub(r"\n","", line)
    line = re.sub(r"a\'","á", line)
    line = re.sub(r"A\'","Á", line)
    line = re.sub(r"c\'","č", line)
    line = re.sub(r"C\'","Č", line)
    line = re.sub(r"d\'","ď", line)
    line = re.sub(r"D\'","Ď", line)
    line = re.sub(r"e\'\'","é", line)
    line = re.sub(r"E\'\'","É", line)
    line = re.sub(r"e\'","ě", line)
    line = re.sub(r"E\'","Ě", line)
    line = re.sub(r"i\'","í", line)
    line = re.sub(r"I\'","Í", line)
    line = re.sub(r"n\'","ň", line)
    line = re.sub(r"N\'","Ň", line)
    line = re.sub(r"o\'","ó", line)
    line = re.sub(r"O\'","Ó", line)
    line = re.sub(r"r\'","ř", line)
    line = re.sub(r"R\'","Ř", line)
    line = re.sub(r"s\'","š", line)
    line = re.sub(r"S\'","Š", line)
    line = re.sub(r"t\'","ť", line)
    line = re.sub(r"T\'","Ť", line)
    line = re.sub(r"u\'\'","ú", line)
    line = re.sub(r"u\'","ů", line)
    line = re.sub(r"U\'","Ú", line)
    line = re.sub(r"y\'","ý", line)
    line = re.sub(r"Y\'","Ý", line)
    line = re.sub(r"z\'","ž", line)
    line = re.sub(r"Z\'","Ž", line)
    return line

def parseName(name):
    name = name.lower()
    name = re.sub(r"\_","", name)
    return name

def getFiles( wildch ):
    mypath = os.getcwd()
    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    filtered = []
    for f in onlyfiles:
        if(re.match(wildch, f) != None):
            filtered.append(f)
    return filtered

def getLinesInFiles( wildch ):
    print('File search pattern: '+wildch)
    files = getFiles(wildch)
    print(files)

    lines = []
    for nm in files:
        with open(nm) as f:
            lns = f.readlines()
            f.closed
            print('File '+nm+', '+str(len(lns))+' lines')
            lines = lines + lns

    return lines

def expandWildchars( lst0, lstFull ):
    lst1 = []
    for it in lst0:
        if((it[0]=="<")and(it[-1]==">")):
            r = re.compile(it[1:-1])
            lst1.extend(list(filter(r.match, lstFull)))
        else:
            lst1.append(it)
    return lst1
########
# Process

# Comments file
print('\n--> '+fileNameBase+'.tex')
lines = getLinesInFiles(fileNameBase+'.txt')
f = open(fileNameBase+'.tex','w')
writeLine(f,0,'\\documentclass[a4paper]{article}')
writeLine(f,0,'\\usepackage[a4paper]{geometry}')
writeLine(f,0,'\\usepackage[czech]{babel}')
writeLine(f,0,'\\usepackage[utf8]{inputenc}')
writeLine(f,0,'\\renewcommand{\\arraystretch}{1.5}')
writeLine(f,0,'')
for line in lines:
    text = expandCzechLetters(line)
    if(line[0]=='<'):
        text = expandCzechLetters(line[3:])
        if(line[3] == '>'):
            text = expandCzechLetters(line[4:])
        if(line[1]=='T'):
            writeLine(f,0,'\\title{'+text+'}')
            writeLine(f,0,'\\date{2013-09-01}')
            writeLine(f,0,'\\author{Martin \'Gaimi\' Darai}')
            writeLine(f,0,'')
            writeLine(f,0,'\\begin{document}')
            writeLine(f,1,'\\maketitle')
            writeLine(f,1,'\\begin{par}')
        elif(line[1]=='P'):
            writeLine(f,1,'\\end{par}')
            writeLine(f,1,'\\vspace{1em}')
            writeLine(f,1,'\\begin{par}')
        elif(line[1]=='C'):
            if(line[2]=='1'):
                writeLine(f,1,'\\end{par}')
                writeLine(f,1,'\\subsection{'+text+'}')
                writeLine(f,1,'\\begin{par}')
            elif(line[2]=='2'):
                writeLine(f,1,'\\end{par}')
                writeLine(f,1,'\\subsubsection{'+text+'}')
                writeLine(f,1,'\\begin{par}')
            else:
                writeLine(f,1,'\\end{par}')
                writeLine(f,1,'\\section{'+text+'}')
                writeLine(f,1,'\\begin{par}')
        elif(line[1]=='I'):
            if(line[2]=='0'):
                writeLine(f,2,'\\begin{itemize}')
            elif(line[2]=='1'):
                writeLine(f,2,'\\end{itemize}')
            else:
                writeLine(f,3,'\\item '+text)
        elif(line[1]=='B'):
            if(line[2]=='0'):
                writeLine(f,2,'\\begin{center}')
                writeLine(f,3,'\\begin{tabular}{ '+text+' }')
            elif(line[2]=='1'):
                writeLine(f,3,'\\end{tabular}')
                writeLine(f,2,'\\end{center}')
            elif(line[2]=='L'):
                writeLine(f,4,'\\hline')
            else:
                writeLine(f,4,text+'\\\\')
        else:
            printWarning('Strange LINE: '+line+', unknown tag')
            writeLine(f,2,text)
    else:
        writeLine(f,2,text)
writeLine(f,1,'\\end{par}')
writeLine(f,0,'\end{document}')
f.close()

os.system('pdflatex '+fileNameBase+'.tex');

os.system('xdg-open '+fileNameBase+'.pdf');

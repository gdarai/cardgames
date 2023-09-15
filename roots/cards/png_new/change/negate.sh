#!/bin/bash
echo "Negate Images"
mkdir neg
for file in *.png; do convert "-negate" $file "neg/"$file; done

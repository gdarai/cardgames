#!/bin/bash
echo "Negate Images"
mkdir neg

for file in *.png; do
	convert "-negate" $file "pom.png"
	cmd="convert -crop 370x370+15+15 pom.png neg/"$file
	echo $cmd
	$cmd
done

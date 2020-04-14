#!/bin/sh

# variables
re='^[0-9]+$'
time=$2
filepath="/home/pi/Videos/"$1".h264"

# code

if [ "$1" = "" ] || [ "$2" = "" ]
then
	echo "error: your command should be $videoCap <filename> <time>";
	exit 1
fi


if ! [[ $time =~ $re ]] || [ $time -lt 1000 ]
then
   echo "error: wrong parameters (time must be > 1000 ms)";
   exit 1
else
	echo; echo "Record time:" $(($time/1000)) "seconds" 
	echo "Saves to:   " $filepath; echo
fi

raspivid -o $filepath -t $time -p 10,0,640,480
#!/bin/sh
cd ~/DiPy
while [ 1 ]
do
    git pull;
    git add --all;
    git commit -a -m "auto-commit (RP)::probably temp only";
    git push;
    echo "Waiting for 2 minutes..."
    sleep 10;
done

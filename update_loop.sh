#!/bin/sh
cd /home/pi/DiPy
echo "Update-Task: Start"
git config --global user.email "backskin@outlook.com"
git config --global user.name "backskin-pi"
while /bin/true; do
    echo "Update-Task: Pull...";
    git pull;
    echo "Trying to gather all data and commit";
    git add --all;
    git commit --author "backskin-pi"  -a -m "auto-commit (RP)::probably temp only";
    git push;
    echo "Update-Task: Objectives done";
    echo "Waiting for 2 minutes...";
    sleep 120;
done &

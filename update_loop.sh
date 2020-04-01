#!/bin/sh
echo "Update-Task: Start"
cd /home/pi/DiPy

while /bin/true; do
    echo "Update-Task: Pull..."
    git pull
    echo "Trying to gather all data and commit"
    git add --all
    echo "configuring GIT"
    git config --global user.email "backskin@outlook.com"
    git config --global user.name "backskin"
    git config credentials.helper store
    echo "Commit line";
    git commit --author "backskin"  -a -m "auto-commit (RP)::probably temp only"
    
    echo "Push line"
    git push
    echo "Update-Task: Objectives done"
    echo "Waiting for 2 minutes..."
    sleep 120
done &

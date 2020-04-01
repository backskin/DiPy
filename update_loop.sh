#!/bin/sh
echo "Update-Task: Start"
cd /home/pi/DiPy
git config --global user.email "backskin@outlook.com"
git config --global user.name "backskin"
git config credentials.helper store
while /bin/true; do
    echo "Update-Task: Pull...";
    git pull;
    echo "Trying to gather all data and commit";
    git add --all;
    git commit --author "backskin"  -a -m "auto-commit (RP)::probably temp only";
    git push;
    echo "Update-Task: Objectives done";
    echo "Waiting for 2 minutes...";
    sleep 120;
done &

#!/bin/sh
echo "Update-Task: Start"
cd /home/pi/DiPy;

while /bin/true; do
    echo "Update-Task: Pull..."
    git pull;
    echo "Trying to gather all data and commit"
    git add --all
    echo "Commit line";
    git commit --author "backskin"  -a -m "auto-commit (RP)"
    echo "Push line";
    git push
    echo "Update-Task: Objectives done"
    echo "Waiting for 2 minutes..."
    sleep 120;
done
from sombrero import *
import os

standings = "standings.csv"
testbatter = {"shortbatter": "Javier Baez"}

f = open(standings, "r")
f.close()
def update_standings(batter):
    oncharts = False
    f = open(standings, "r")
    lines = f.readlines()
    f.close()
    f =open(standings,"w")
    for line in lines:
        if line.startswith(batter["shortbatter"]):
            oncharts = True
            s = re.findall(r"\d", line)
            f.write(batter["shortbatter"] + ", " + str((int(s[0])+1)) + "\n")
        else:
            f.write(line)

    if oncharts == False:
        f.write(batter["shortbatter"] + ", 1")
    f.close()


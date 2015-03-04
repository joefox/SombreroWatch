from sombrero import *
import twitter
from standings import *
import yo
from auth import *
import os
#import appnope

#appnope.nope()

api = twitter.Api(consumer_key=Akey,consumer_secret=Askey,access_token_key = Atoken,access_token_secret = Astoken)

fours = y + "-" + m + "-" + d + "_sombreros.txt"
threes = y + "-" + m + "-" + d + "_sombreros_close.txt"
strikeouts = y + "-" + m + "-" + d + "_all.csv"
f = open(fours, "a+")
f.close()
f = open(threes, "a+")
f.close()
f = open(strikeouts, "w")
f.close()
t = 1 

if games_in_progress(basegamedayURL) != 0:
    todays_games = get_games(basegamedayURL)
    f = open(strikeouts, "w")
    f.write("player,team,k,ab,extra\n")    
    f.close()
    for x in range(0,len(todays_games)):
        batter_list = batters(todays_games[x])
        extras_statement = ""
        if is_extras(todays_games[x]):
            extras_statement = "(extra innings) "
        for batter in batter_list:
            f = open(strikeouts,"a+")
            line = batter["batter"] + "," + batter["team"] + "," + batter["so"] + "," + batter["ab"] + "," + extras_statement + "\n"
            f.write(line)
            f.close()
            if batter["batter"] + ", " + batter["so"] in open(fours).read():
                print batter["batter"] + " already tweeted"
                pass
            elif int(batter["so"]) > 4:
                # yo_client.yo()
                status = batter["batter"] + ": " + batter["so"] + " strikeouts in " + batter["ab"] + " at-bats. " + extras_statement + "#PlatinumSombrero #SombreroWatch #" + batter["team"].replace(" ","") + " #Whiff"
                api.PostUpdate(status)
                print batter["batter"]
                if batter["batter"] in open(fours).read():
                    f = open(fours, "r")
                    lines = f.readlines()
                    f.close()
                    f = open(fours, "w")
                    for line in lines:
                        if line!=batter["batter"] + ", 4, " + str(re.compile("\d,.")) + "\n":
                            f.write(line)
                    f.close()
                open(fours, "a+").write(batter["batter"] + ", " + batter["so"] + ", " + batter["ab"] + ", " + batter["team"] + "\n")
            elif batter["so"] == "4":
                status = batter["batter"] + ": " + batter["so"] + " strikeouts in " + batter["ab"] + " at-bats. " + extras_statement + "#GoldenSombrero #" + batter["team"].replace(" ","") + " #Whiff"
                api.PostUpdate(status)
                update_standings(batter)
                print batter["batter"]
                f = open(threes, "r")
                lines = f.readlines()
                f.close()
                f = open(threes, "w")
                for line in lines:
                    if line!=batter["batter"] + ", 3, " + str(re.compile(".")) + "\n":
                        f.write(line)
                f.close()
                open(fours, "a+").write(batter["batter"] + ", " + batter["so"] + ", " + batter["ab"] + ", " + batter["team"] + "\n")
            elif batter["so"] == "3":
                if batter["batter"] in open(threes).read():
                    print batter["batter"] + " already tweeted #" + batter["team"].replace(" ","")
                    pass
                else:
                    status = batter["batter"] + " is one strikeout away from a #GoldenSombrero! " + extras_statement + "#" + batter["team"].replace(" ","") + " #Whiff"
                    api.PostUpdate(status)
                    print batter["batter"]
                    open(threes, "a+").write(batter["batter"] + ", " + batter["so"] + ", " + batter["ab"] + ", " + batter["team"] + "\n")
    #            close(filename)
            elif int(batter["so"]) > 0:
                if batter["final"] != "F":
                    print batter["batter"] + batter["so"]
    # f = open(strikeouts, "rb")
    # s3_conn.upload(strikeouts,f,"sombrero.watch/sombrero",public=True)
    # f = open(standings, "rb")
    # s3_conn.upload(standings,f,"sombrero.watch/sombrero",public=True)

print games_in_progress(basegamedayURL)
f = open(fours, "r")
done = f.readlines()
f.close()
if games_in_progress(basegamedayURL) == 0 and (len(done) == 0 or done[len(done)-1] != "done"):
    f = open(fours, "a+")
    f2 = open(threes, "r")
    sombreros = 0
    close_calls = 0
    for line in f:
        sombreros += 1
    for line in f2:
        close_calls += 1
    f.write("done")
    f.close()
    f2.close()
    print "sombreros: " + str(sombreros)
    if sombreros == 0 and close_calls == 0:
        status = "Nobody even came close to a sombrero today. :( #GoldenSombrero #whiff"
        api.PostUpdate(status)
    if sombreros == 0 and close_calls == 1:
        status = str(close_calls) + " close call, but no sombreros today. #GoldenSombrero #whiff"
        api.PostUpdate(status)
    if sombreros == 0 and close_calls > 1:
        status = str(close_calls) + " close calls, but no sombreros today. #GoldenSombrero #whiff"
        api.PostUpdate(status)
    if sombreros == 1:
        f = open(fours, "r")
        line = f.readline()
        status = "Only one MLB player/hero (" + line.split(",")[0] + ") earned a golden sombrero today. #GoldenSombrero #" + line.split(",")[3].replace(" ","") + " #whiff"
        api.PostUpdate(status)
        f.close()
    if sombreros > 1:
        print "ok"
        status = str(sombreros) + " MLB players earned sombreros today. It was a good day. #GoldenSombrero #whiff"
        api.PostUpdate(status)


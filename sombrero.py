import httplib2
import re
import time
import datetime
from bs4 import BeautifulSoup

y = time.strftime("%Y")
m = time.strftime("%m")
#d = "07"
d = time.strftime("%d")

basegamedayURL = "http://gd2.mlb.com/components/game/mlb/year_" + y + "/month_" + m + "/day_" + d + "/"
top10 = [{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0},{"speed":0, "pitcher":0}]
bottom10 = [{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0},{"speed":200, "pitcher":0}]

team_dict = {"cle": "Indians", "cha": "White Sox", "bos": "Red Sox", "nya": "Yankees", "chn": "Cubs", "sln": "Cardinals", "col": "Rockies", "sfn": "Giants", "det": "Tigers", "sdn": "Padres", "hou": "Astros", "tex": "Rangers", "kca": "Royals", "min": "Twins", "lan": "Dodgers", "ari": "Diamondbacks", "mia": "Marlins", "phi": "Phillies", "nyn": "Mets", "ana": "Angels", "oak": "Athletics", "sea": "Mariners", "pit": "Pirates", "mil": "Brewers", "tba": "Rays", "cin": "Reds", "tor": "Blue Jays", "bal": "Orioles", "was": "Nationals", "atl": "Braves","asu":"Arizona State","boc":"Boston College","neu":"Northeastern University","umi":"University of Miami"}

#f1 = open("pitches.txt", "w+")
def get_games(gamedayURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gamedayURL,"GET")
    page[0]
    soup = BeautifulSoup(page[1])
    games = [gamedayURL + game.lstrip() for game in soup.find_all(text=re.compile("gid"))]
    return games

def games_in_progress(gamedayURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gamedayURL + "scoreboard.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    count = 0
    for game in soup.find_all("game"):
        if game["status"] == "IN_PROGRESS" or game["status"] == "PRE_GAME" or game["status"] == "IMMEDIATE_PREGAME" or game["status"] == "DELAYED":
            count += 1
    return count
    
def start_time(gamedayURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gamedayURL + "master_scoreboard.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    game1 = soup.find("game")
    return time.strptime(game1.get("time_date"))
    
def in_progress(gameURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gameURL + "boxscore.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    if soup.find("boxscore").get("status") == "F":
        return false
   
def is_extras(gameURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gameURL + "boxscore.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    if len(soup.find_all("inning_line_score")) > 9:
        return True
    else:
        return False

def load_batters(batter):
    d = {}
    d["final"] = batter.parent.parent.get("status_ind")
    if batter.parent.parent.get("game_id").endswith("2"):
        d["batter"] = batter.get("name_display_first_last") + " (game 2)"
    else:
        d["batter"] = batter.get("name_display_first_last")
    d["shortbatter"] = batter.get("name_display_first_last")
    d["ab"] = batter.get("ab")
    d["so"] = batter.get("so")
    print d["batter"]
    d["team"] = team_dict[batter.parent.parent.get(batter.parent.get("team_flag") + "_team_code")]
    return d
    
def batters(gameURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gameURL + "boxscore.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    batters = [load_batters(batter) for batter in soup.find_all("batter")]
    return batters

def get_silver_sombreros(gameURL,silver):
    conn = httplib2.Http(".cache")
    page = conn.request(gameURL + "boxscore.xml","GET")
    page[0]
    soup = BeautifulSoup(page[1])
    silver = [check_silver(batter) for batter in soup.find_all("batter")]
    return silver

    

def get_pitch_info(pitch):
    d = {}
    d["pitcher"] = pitch.parent.get("pitcher")
    if pitch.get("start_speed") == "":
        d["speed"] = 0
    else:
        d["speed"] = float(pitch.get("start_speed"))
    return d

def get_pitches(gameURL):
    conn = httplib2.Http(".cache")
    page = conn.request(gameURL + "game_events.xml", "GET")
    page[0]
    soup = BeautifulSoup(page[1])
    pitches = [get_pitch_info(pitch) for pitch in soup.find_all("pitch")]
    return pitches

def get_fastest_pitches(pitches):
    for pitch in pitches:
        if pitch["speed"] >= top10[9]["speed"]:
            count = 9
            while pitch["speed"] > top10[count]["speed"]:
                if count > 0:
                    count -= 1
                else:
                    top10.insert(0, pitch)
                    top10.pop()
            if pitch["speed"] == top10[count]["speed"]:
                top10.insert(count, pitch)
                top10.pop()
    
def get_slowest_pitches(pitches):
    for pitch in pitches:
        if pitch["speed"] <= bottom10[9]["speed"] and pitch["speed"] > 0:
            count = 9
            while pitch["speed"] < bottom10[count]["speed"]:
                if count > 0:
                    count -= 1
                else:
                    bottom10.insert(0, pitch)
                    bottom10.pop()
            if pitch["speed"] == bottom10[count]["speed"]:
                bottom10.insert(count, pitch)
                bottom10.pop()
            




#for x in xrange(0,len(todays_games)):
#    print todays_games[x] + "game_events.xml"
#    game_pitches = get_pitches(todays_games[x])
#    get_fastest_pitches(game_pitches)
#    get_slowest_pitches(game_pitches)


#f1.write(pitches)



#print top10
#print bottom10

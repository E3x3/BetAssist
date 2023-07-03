# Written by Ethan Roush
import copy

from nba_api.stats.endpoints import playergamelog

#from MongoPersister import MongoPersister
from Scraper import Scraper
import sys
import time
import tkinter as tk
import tksheet
import requests
import statsapi

#from constants import BET_ASSIST_URI, BET_ASSIST_DB_COLLECTION, BET_ASSIST_DB_NAME

# GLOBALS

MLB_ABBREVIATIONS = {"Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS", "Chicago Cubs": "CHC",
                     "Chicago White Sox": "CWS", "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL", "Detroit Tigers": "DET", 
                     "Miami Marlins": "MIA", "Houston Astros": "HOU", "Kansas City Royals": "KAN", "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
                     "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM", "New York Yankees": "NYY", "Oakland Athletics": "OAK",
                     "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT", "San Diego Padres": "SD", "San Francisco Giants": "SF", "Seattle Mariners": "SEA",
                      "St. Louis Cardinals": "STL", "Tampa Bay Rays": "TB", "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR", "Washington Nationals": "WAS" }
OPPONENT_IND = 4
POINT_IND = 24
REB_IND = 18
ASSIST_IND = 19
STEAL_IND = 20
BLOCK_IND = 21
FTM_IND = 13
FGA_IND = 8
THREE_POINT_MAKE_IND = 10
TO_IND = 22
PF_IND = 23
GAME_TYPE_IND = 0
MIN_IND = 6
BASE_URL = 'https://statsapi.mlb.com/api/v1/people/player_id/stats?stats=gameLog&group=category&gameType=R&sitCodes=1,2,3,4,5,6,7,8,9,10,11,12&season=2023&language=en'

NUM_MULTI_PLAYERS = 2

class BetAssist:
    includePlayoffs = False
    playerGames = {}
    homeTeams = []
    numAPICalls = 0

    def __init__(self, includePlayoffs, homeTeams, sport):
        self.includePlayoffs = includePlayoffs
        self.playerGames = {}
        self.homeTeams = homeTeams
        self.numAPICalls = 0
        self.sport = sport
        self.req = requests.Session()

    def _getGames(self, playerID, playerType):
        if playerID not in self.playerGames:
            if self.sport == "NBA":
                regularSeasonGamelogs = playergamelog.PlayerGameLog(playerID)
                regularSeasonGames = regularSeasonGamelogs.get_dict()['resultSets'][0]['rowSet']
            if self.sport == "MLB":
                # Change URL for hitter/pitcher and playerID
                gamelog_url = BASE_URL.replace("player_id", str(playerID)).replace("category", playerType)

                response = ''
                while response == '':
                    try:
                        response = self.req.get(gamelog_url, timeout=20)
                        break
                    except requests.exceptions.Timeout:
                        print("Connection timeout")
                        print("Sleeping for 5 seconds.")
                        time.sleep(5)
                        print("Continue...")
                    except:
                        print("Connection refused by the server...")
                        print("Sleeping for 5 seconds.")
                        time.sleep(5)
                        print("Continue...")

                try:
                    regularSeasonGames = response.json()["stats"][0]["splits"]
                except:
                    print(response.json())
                    print(playerID)
                    print(playerType)
                    regularSeasonGames = []

            self.numAPICalls += 1
            if self.includePlayoffs:
                playoffGameLogs = playergamelog.PlayerGameLog(playerID, season_type_all_star="Playoffs")
                self.numAPICalls += 1
                playoffGames = playoffGameLogs.get_dict()['resultSets'][0]['rowSet']
                playoffGames.extend(regularSeasonGames)
                self.playerGames[playerID] = playoffGames
                return playoffGames
            else:
                self.playerGames[playerID] = regularSeasonGames
                return regularSeasonGames
        else:
            return self.playerGames[playerID]


    def _getPlayerStatlines(self, playerID, playerType):
        games = self._getGames(playerID, playerType)
        seasonStatlines = []
        for i in range(0, len(games)):

            isHomeGame = True
            if self.sport == "MLB":
                isHomeGame = games[i]['isHome']
            if self.sport == "NBA":
                if '@' in games[i][OPPONENT_IND]:
                    isHomeGame = False

            isPlayoffGame = False
            if self.sport == "NBA":
                if games[i][GAME_TYPE_IND] == '42022':
                    isPlayoffGame = True

            if self.sport == "NBA":
                game_dict = {'opp': games[i][OPPONENT_IND][-3:], 'min': games[i][MIN_IND],'home': isHomeGame, 'playoff': isPlayoffGame,
                            'pts': games[i][POINT_IND], 'asts': games[i][ASSIST_IND], 'rebs': games[i][REB_IND],
                            '3pm': games[i][THREE_POINT_MAKE_IND], 'stls': games[i][STEAL_IND],
                            'blks': games[i][BLOCK_IND], 'fga': games[i][FGA_IND], 'tos': games[i][TO_IND],
                            'pfs': games[i][PF_IND], 'ftm': games[i][FTM_IND]}

            if self.sport == "MLB":
                opp = MLB_ABBREVIATIONS[games[i]["opponent"]["name"]]
                if playerType == 'hitting':
                    game_dict = {'playerType': playerType, 'opp': opp, 'home': isHomeGame, 'playoff': isPlayoffGame,
                                'tb': games[i]["stat"]["totalBases"], 'hs': games[i]["stat"]["strikeOuts"], 
                                'r': games[i]["stat"]["runs"]}
                if playerType == "pitching":
                    game_dict = {'playerType': playerType, 'opp': opp, 'home': isHomeGame, 'playoff': isPlayoffGame,
                                'pt': games[i]["stat"]["numberOfPitches"], 'ps': games[i]["stat"]["strikeOuts"], 
                                'po': games[i]["stat"]["outs"], 'ha': games[i]["stat"]["hits"],'wa': games[i]["stat"]["baseOnBalls"],
                                'era': games[i]["stat"]["earnedRuns"]}

            seasonStatlines.append(game_dict)

        if self.sport == "MLB":
            seasonStatlines.reverse()

        return seasonStatlines

    def _calculateHitPercentage(self, statlines, overAmnt, category):
        numHits = 0
        totalMin = 0
        for statline in statlines:
            if self.sport == "NBA":
                pts = statline['pts']
                asts = statline['asts']
                rebs = statline['rebs']
                threePointMakes = statline['3pm']
                stls = statline['stls']
                blks = statline['blks']
                fga = statline['fga']
                tos = statline['tos']
                pfs = statline['pfs']
                ftm = statline['ftm']
                min = statline['min']
                totalMin += min
                fantasyScore = pts + (1.2 * rebs) + (1.5 * asts) + (3 * blks) + (3 * stls) + (-1 * tos)
            
            if self.sport == "MLB":
                if statline['playerType'] == 'hitting':
                    tb = statline['tb']
                    hs = statline['hs']
                    r = statline['r']
                if statline['playerType'] == 'pitching':
                    pt = statline['pt']
                    ps = statline['ps']
                    po = statline['po']
                    ha = statline['ha']
                    wa = statline['wa']
                    era = statline['era']

            if category == 'Pitches Thrown' and pt >= overAmnt:
                numHits += 1
            if category == 'Pitcher Strikeouts' and ps >= overAmnt:
                numHits += 1
            if category == 'Pitching Outs' and po >= overAmnt:
                numHits += 1
            if category == 'Hits Allowed' and ha >= overAmnt:
                numHits += 1
            if category == 'Walks Allowed' and wa >= overAmnt:
                numHits += 1
            if category == 'Earned Runs Allowed' and era >= overAmnt:
                numHits += 1
            if category == 'Total Bases' and tb >= overAmnt:
                numHits += 1
            if category == 'Hitter Strikeouts' and hs >= overAmnt:
                numHits += 1
            if category == 'Runs' and r >= overAmnt:
                numHits += 1
            if category == 'Points' and pts >= overAmnt:
                numHits += 1
            elif category == 'Rebounds' and rebs >= overAmnt:
                numHits += 1
            elif category == 'Assists' and asts >= overAmnt:
                numHits += 1
            elif category == 'Pts+Rebs+Asts' and (pts + rebs + asts) >= overAmnt:
                numHits += 1
            elif category == 'Pts+Rebs' and (pts + rebs) >= overAmnt:
                numHits += 1
            elif category == 'Pts+Asts' and (pts + asts) >= overAmnt:
                numHits += 1
            elif category == 'Rebs+Asts' and (rebs + asts) >= overAmnt:
                numHits += 1
            elif category == '3-PT Made' and threePointMakes >= overAmnt:
                numHits += 1
            elif category == 'Blks+Stls' and (blks + stls) >= overAmnt:
                numHits += 1
            elif category == 'Blocked Shots' and blks >= overAmnt:
                numHits += 1
            elif category == 'Steals' and stls >= overAmnt:
                numHits += 1
            elif category == 'Turnovers' and tos >= overAmnt:
                numHits += 1
            elif category == 'Free Throws Made' and ftm >= overAmnt:
                numHits += 1
            elif category == 'FG Attempted' and fga >= overAmnt:
                numHits += 1
            elif category == 'Personal Fouls' and pfs >= overAmnt:
                numHits += 1
            elif category == 'Fantasy Score' and fantasyScore >= overAmnt:
                numHits += 1

        avgMin = totalMin / len(statlines) if len(statlines) != 0 else 0
        if sport == "MLB":
            avgMin = 25
        return ((numHits / len(statlines)), avgMin) if len(statlines) != 0 else ('N/A', avgMin)


    def _printBets(self, betList):
        for entry in betList:
            print(f'\nName: {entry["Name"]}\nTeam: {entry["Team"]}\nProp: Hit {entry["Over"]} {entry["Prop"]}\nTotal Hit %: *** {entry["TotalHitPercentage"]} ***')
            for k, v in entry['HitPercentagesPrintableDict'].items():
                if v != 'N/A':
                    print(f'-{k}: {v}')

    def _checkOccurences(self, id, betList):
        count = 0
        for entry in betList:
            if entry['Id'] == id:
                count+=1
        return count

    def _displayTksheet(self, displayData):
        displayList = [["TOP", "30", "NON-RISKY", "BETS"]]
        headers = []
        risky = False
        riskCounter = 1
        top_30_len = 0
        top_15_len = 0
        bot_20_len = 0
        bot_15_len = 0
        for dict in displayData:
            prop_info = []
            for key in dict:
                if key == 'HitPercentagesPrintableDict':
                    for keyj in dict[key]:
                        prop_info.append(dict[key][keyj])
                        headers.append(keyj)
                headers.append(key)
                prop_info.append(dict[key])
                
            if prop_info[8] != risky:
                if riskCounter == 1:
                    top_30_len = len(displayList)
                    displayList.append(["TOP", "15", "RISKY", "BETS"])
                if riskCounter == 2:
                    top_15_len = len(displayList)
                    displayList.append(["BOTTOM", "20", "NON-RISKY", "BETS"])
                if riskCounter == 3:
                    bot_20_len = len(displayList)
                    displayList.append(["BOTTOM", "15", "RISKY", "BETS"])

                riskCounter += 1
                risky = prop_info[8]

            displayList.append(prop_info[:5] + prop_info[8:9] + prop_info[11:20])

        if top_30_len == 0:
            top_30_len = len(displayList)
        elif top_15_len == 0:
            top_15_len = len(displayList)   
        elif bot_20_len == 0:
            bot_20_len = len(displayList)
        else:
            bot_15_len = len(displayList)

        headers = headers[:5] + headers[8:9] + headers[11:20]
        headers[6] = 'Total Hit %'
        headers[10] = 'Against Opponent'

        app = tk.Tk()

        screen_width = app.winfo_screenwidth()
        screen_height = app.winfo_screenheight()

        app.geometry("%dx%d" % (screen_width, screen_height))
        app.grid_columnconfigure(0, weight = 1)
        app.grid_rowconfigure(0, weight = 1)

        main_frame = tk.Frame(app)
        main_frame.grid(row = 0, column = 0, sticky = "nsew", padx = 10, pady = 10)

        main_frame.grid_columnconfigure(0, weight = 1)
        main_frame.grid_rowconfigure(1, weight = 1)
        
        sheet = tksheet.Sheet(main_frame,
              total_rows = len(displayList),
              total_columns = len(headers), headers=headers)
        sheet.grid(row = 1, column = 0, sticky = "nswe", padx = 10, pady = 10)

        sheet.enable_bindings(("single_select",

                       "row_select",

                       "column_width_resize",

                       "arrowkeys",

                       "right_click_popup_menu",

                       "rc_select",

                       "rc_insert_row",

                       "rc_delete_row",

                       "copy",

                       "cut",

                       "paste",

                       "delete",

                       "undo",

                       "edit_cell"))
        
        sheet.set_sheet_data(displayList)
        sheet.highlight_rows(rows = range(1,top_30_len), bg = "#00ff00")
        sheet.highlight_rows(rows = range(top_30_len + 1,top_15_len), bg = "#ffff00")
        sheet.highlight_rows(rows = range(top_15_len + 1,bot_20_len), bg = "#00ff00")
        sheet.highlight_rows(rows = range(bot_20_len + 1,bot_15_len), bg = "#ffff00")
        app.mainloop()

    """
    def _persistToDatabase(self, entries):
        persister = MongoPersister(BET_ASSIST_URI, BET_ASSIST_DB_NAME, BET_ASSIST_DB_COLLECTION)
        persister.connectClient()
        
        #DBBets return format: [{'_id', 'Id', 'Name', 'Date', 'Over', 'Decision',  ...} ]
        dbBets = persister.readAll()

        unpersistedBets = []
        for entry in entries:
            unpersistedBet = {}
            unpersistedBetId = entry['Id']
            unpersistedBetName = entry['Name']
            unpersistedBetDate = entry['Date']
            unpersistedBetOver = float(entry['Over'])
            unpersistedBetCategory = entry['Prop']
            unpersistedBetTotalHitPercentage = entry['TotalHitPercentage']
            unpersistedBetHitPercentagesPrintableDict = entry['HitPercentagesPrintableDict']
            unpersistedBetDecision = entry['Decision']
            unpersistedBetTeam = entry['Team']
            unpersistedBetRisk = 'Y' if entry['Risky'] else 'N'
            unpersistedBetLowFrequency = entry['LowFrequency']

            alreadyInDB = False
            for dbBet in dbBets:
                if dbBet['Id'] == unpersistedBetId and dbBet['Date'] == unpersistedBetDate and dbBet['Prop'] == unpersistedBetCategory \
                    and dbBet['Over'] == unpersistedBetOver and dbBet['Decision'] == unpersistedBetDecision:
                    alreadyInDB = True

            if not alreadyInDB:
                unpersistedBets.append({'Id': unpersistedBetId, 'Name': unpersistedBetName, 'Date': unpersistedBetDate,
                                        'TotalHitPercentage': unpersistedBetTotalHitPercentage,
                                        'Prop': unpersistedBetCategory, 'HitPercentagesPrintableDict': unpersistedBetHitPercentagesPrintableDict,
                                        'Over': unpersistedBetOver, 'Decision': unpersistedBetDecision, 'Risky': unpersistedBetRisk, 'Team': unpersistedBetTeam,
                                        'LowFrequency': unpersistedBetLowFrequency})

        persister.batchWrite(unpersistedBets)
        """



    def findGoodBets(self, betData):
        print("Finding Good Bets.")
        betList = []
        startTime = time.time()
        for i in range(len(betData)):

            # necessary so API calls for game data do not cause HTTP Timeout
            if self.numAPICalls > 0 and self.numAPICalls % 5 == 0:
                time.sleep(10)

            if i % 30 == 0:
                elapsedTime = time.time() - startTime
                print(f'{i}/{len(betData)} player props analyzed. {elapsedTime:.2f} seconds elapsed')

            entry = betData[i]
            playerName = entry['Name']
            playerID = entry['Id']
            playerType = entry['PlayerType']
            overAmnt = float(entry['Over'])
            category = entry['Prop']
            team = entry['Team']
            opponent = entry['Opponent']
            entry['Risky'] = False
            entry['AvgMinOverLastFiveGames'] = 0
            entry['LowFrequency'] = 'N'
            if category == '3-PT Made' or category == 'Blks+Stls' or category == 'Blocked Shots' \
                or category == 'Steals' or category == 'Turnovers' or category == 'Free Throws Made' \
                or category == 'Personal Fouls':
                    entry['LowFrequency'] = 'Y'


            games = self._getPlayerStatlines(playerID, playerType)

            lastFiveGames = [games[i] for i in range(len(games)) if i <= 4]
            lastTenGames = [games[i] for i in range(len(games)) if i <= 9]
            lastFifteenGames = [games[i] for i in range(len(games)) if i <= 14]
            versusOpponentGames = [games[i] for i in range(len(games)) if
                                   games[i]['opp'].upper() == opponent.upper() or games[i][
                                       'opp'].upper() in opponent.upper()]
            homeGames = []
            awayGames = []
            if team.upper() in self.homeTeams and self.homeTeams:
                homeGames = [games[i] for i in range(len(games)) if games[i]['home'] is True]
            elif team.upper() not in self.homeTeams and self.homeTeams:
                awayGames = [games[i] for i in range(len(games)) if games[i]['home'] is False]
            playoffGames = []
            if self.includePlayoffs:
                playoffGames = [games[i] for i in range(len(games)) if games[i]['playoff'] == True]


            lastFiveGamesHitPercentage, avgMinOverLastFiveGames = self._calculateHitPercentage(lastFiveGames, overAmnt, category)[0], self._calculateHitPercentage(lastFiveGames, overAmnt, category)[1]
            lastTenGamesHitPercentage = self._calculateHitPercentage(lastTenGames, overAmnt, category)[0]
            lastFifteenGamesHitPercentage = self._calculateHitPercentage(lastFifteenGames, overAmnt, category)[0]
            versusOpponentGamesHitPercentage = self._calculateHitPercentage(versusOpponentGames, overAmnt, category)[0]
            homeGamesHitPercentage = self._calculateHitPercentage(homeGames, overAmnt, category)[0]
            awayGamesHitPercentage = self._calculateHitPercentage(awayGames, overAmnt, category)[0]
            playoffGamesHitPercentage = self._calculateHitPercentage(playoffGames, overAmnt, category)[0]
            gamesHitPercentage = self._calculateHitPercentage(games, overAmnt, category)[0]

            entry['AvgMinOverLastFiveGames'] = avgMinOverLastFiveGames

            hitPercentages = [lastFiveGamesHitPercentage, lastTenGamesHitPercentage, lastFifteenGamesHitPercentage, versusOpponentGamesHitPercentage,
                              gamesHitPercentage, homeGamesHitPercentage, awayGamesHitPercentage, playoffGamesHitPercentage]
            totalHitPercentage = sum([float(pct) for pct in hitPercentages if pct != 'N/A']) / len([pct for pct in hitPercentages if pct != 'N/A'])

            hitPercentagesPrintableDict = {'Last Five Games': lastFiveGamesHitPercentage, 'Last Ten Games': lastTenGamesHitPercentage,
                                           'Last Fifteen Games': lastFifteenGamesHitPercentage, f'Against {opponent}': versusOpponentGamesHitPercentage,
                                           'Season Average': gamesHitPercentage,
                                           'Home Games': homeGamesHitPercentage, 'Away Games': awayGamesHitPercentage,
                                           'Playoffs': playoffGamesHitPercentage}
            roundedDict = {k: round(float(v), 3) if v != 'N/A' else v for k, v in hitPercentagesPrintableDict.items()}


            entry['TotalHitPercentage'] = round(totalHitPercentage, 3)
            entry['HitPercentagesPrintableDict'] = roundedDict

            betList.append(entry)

        elapsedTime = time.time() - startTime
        print(f'{len(betData)}/{len(betData)} player props analyzed. {elapsedTime:.2f} total seconds elapsed')

        sortedBetList = sorted(betList, key=lambda x: x['TotalHitPercentage'], reverse=True)

        topNoRiskBets = []
        topRiskyBets = []
        for entry in copy.deepcopy(sortedBetList):
            if entry['HitPercentagesPrintableDict']['Last Five Games'] < 0.6 or entry['AvgMinOverLastFiveGames'] < 25:
                entry['Risky'] = True

            if entry['Risky'] is False and len(topNoRiskBets) < 20 \
                    and self._checkOccurences(entry['Id'], topNoRiskBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] >= 0.57:
                entry['Decision'] =  'Over'
                topNoRiskBets.append(entry)
            elif entry['Risky'] is True and len(topRiskyBets) < 8 \
                    and self._checkOccurences(entry['Id'], topRiskyBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] >= 0.57:
                entry['Decision'] =  'Over'
                topRiskyBets.append(entry)

            if len(topNoRiskBets) == 20 and len(topNoRiskBets) == 8:
                break

        bottomNoRiskBets = []
        bottomRiskyBets = []
        for entry in reversed(copy.deepcopy(sortedBetList)):
            if entry['AvgMinOverLastFiveGames'] < 25 or entry['HitPercentagesPrintableDict']['Last Five Games'] > 0.4:
                entry['Risky'] = True

            if entry['Risky'] is False and len(bottomNoRiskBets) < 20 \
                    and self._checkOccurences(entry['Id'], bottomNoRiskBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] <= 0.43:
                entry['Decision'] =  'Under'
                bottomNoRiskBets.append(entry)
            elif entry['Risky'] is True and len(bottomRiskyBets) < 8 \
                    and self._checkOccurences(entry['Id'], bottomRiskyBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] <= 0.43:
                entry['Decision'] =  'Under'
                bottomRiskyBets.append(entry)

            if len(bottomNoRiskBets) == 20 and len(bottomRiskyBets) == 8:
                break

        """
        try:
            self._persistToDatabase(topRiskyBets + topNoRiskBets + bottomNoRiskBets + bottomRiskyBets)
        except Exception as e:
            print("Error with database persistence: " + str(e))
        """


        print('\n-----------NON-RISKY BETS WITH HIGHEST HIT PERCENTAGES (OVERS)-----------')

        self._printBets(topNoRiskBets)

        print('\n-----------RISKY BETS WITH HIGHEST HIT PERCENTAGES (OVERS)-----------')

        self._printBets(topRiskyBets)

        print('\n-----------NON-RISKY BETS WITH LOWEST HIT PERCENTAGES (UNDERS)-----------')

        self._printBets(bottomNoRiskBets)

        print('\n-----------RISKY BETS WITH LOWEST HIT PERCENTAGES (UNDERS)-----------')

        self._printBets(bottomRiskyBets)
        displayData = topNoRiskBets + topRiskyBets + bottomNoRiskBets + bottomRiskyBets
        self._displayTksheet(displayData)


if __name__ == '__main__':
    sport = input("Enter the sport you would like to see bets for. (NBA/MLB)\n")
    homeTeams = input("Enter three-letter home teams separated by commas. Press enter for no Home/Away data. Ex: NYK, MIA, BOS\n").split(",")
    homeTeams = [team.strip().upper() for team in homeTeams]
    gamesToConsider = input("Enter games to consider by entering at least one of the teams playing in game. Press enter to consider all. Ex: NYK, BOS\n").split(",")
    gamesToConsider = [team.strip().upper() for team in gamesToConsider]
    
    PPScraper = Scraper()
    nonPrunedBetData = PPScraper.scrapeProps(sport)
    
    # test data
    # nonPrunedBetData = [{'Name': 'Dean Kremer', 'Over': '6.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'BAL', 'Opponent': 'MIN', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 665152}, {'Name': 'Pablo López', 'Over': '6.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'MIN', 'Opponent': 'BAL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 641154}, {'Name': 'Freddy Peralta', 'Over': '6.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'MIL', 'Opponent': 'PIT', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 642547}, {'Name': 'Osvaldo Bido', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'PIT', 'Opponent': 'MIL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 674370}, {'Name': 'James Paxton', 'Over': '5.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'BOS', 'Opponent': 'TOR', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 572020}, {'Name': 'José Berríos', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'TOR', 'Opponent': 'BOS', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 621244}, {'Name': 'Carlos Carrasco', 'Over': '4.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'NYM', 'Opponent': ' SF', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 471911}, {'Name': 'Michael Soroka', 'Over': '4.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'ATL', 'Opponent': 'MIA', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 647336}, {'Name': 'Bryan Hoeing', 'Over': '3.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'MIA', 'Opponent': 'ATL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 663773}, {'Name': 'Jon Gray', 'Over': '5.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'TEX', 'Opponent': 'HOU', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 592351}, {'Name': 'Ronel Blanco', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'HOU', 'Opponent': 'TEX', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 669854}, {'Name': 'Bobby Miller', 'Over': '5.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'LAD', 'Opponent': ' KC', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 676272}, {'Name': 'Austin Gomber', 'Over': '4.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'COL', 'Opponent': 'DET', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 596295}, {'Name': 'Michael Lorenzen', 'Over': 
    # '4.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'DET', 'Opponent': 'COL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 547179}, {'Name': 'Luis Severino', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'NYY', 'Opponent': 'STL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 622663}, {'Name': 'Matthew Liberatore', 'Over': '3.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'STL', 'Opponent': 'NYY', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 669461}, {'Name': 'Griffin Canning', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'LAA', 'Opponent': 'ARI', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 656288}, {'Name': 'Tommy Henry', 'Over': '4.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'ARI', 'Opponent': 'LAA', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 674072}, {'Name': 'Luis Medina', 'Over': '4.5', 'Prop': 'Pitcher Strikeouts', 'Team': 'OAK', 'Opponent': 'CWS', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 665622}, {'Name': 'Bryce Miller', 'Over': '5.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'SEA', 'Opponent': ' TB', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 682243}, {'Name': 'Shane McClanahan', 'Over': '7.0', 'Prop': 'Pitcher Strikeouts', 'Team': 'TB ', 'Opponent': 'SEA', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 663556}, {'Name': 'Joey Gallo', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'MIN', 'Opponent': 'BAL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 608336}, {'Name': 'Austin Hedges', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'PIT', 'Opponent': 'MIL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 595978}, {'Name': 'Jack Suwinski', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'PIT', 'Opponent': 'MIL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 669261}, {'Name': 'Bo Bichette', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'TOR', 'Opponent': 'BOS', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 666182}, {'Name': 'Vladimir Guerrero Jr.', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'TOR', 'Opponent': 'BOS', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 665489}, {'Name': 'Bryan De La Cruz', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'MIA', 'Opponent': 'ATL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 650559}, {'Name': 'Luis Arraez', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'MIA', 'Opponent': 'ATL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 650333}, {'Name': 'Ozzie Albies', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'ATL', 'Opponent': 'MIA', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 645277}, {'Name': 'Corey Seager', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'TEX', 'Opponent': 'HOU', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 608369}, {'Name': 'Marcus Semien', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'TEX', 'Opponent': 'HOU', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 543760}, {'Name': 'Freddie Freeman', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'LAD', 'Opponent': ' KC', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 518692}, {'Name': 'Mookie Betts', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'LAD', 'Opponent': ' KC', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 605141}, {'Name': 'C.J. Cron', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'COL', 'Opponent': 'DET', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 543068}, {'Name': 'Javier Báez', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'DET', 'Opponent': 'COL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 595879}, {'Name': 'Spencer Torkelson', 'Over': '1.5', 'Prop': 'Total Bases', 'Team': 'DET', 'Opponent': 'COL', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 679529}, {'Name': 'Chad Wallach', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'LAA', 'Opponent': 'ARI', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 595453}, {'Name': 'Cal Raleigh', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'SEA', 'Opponent': ' TB', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 663728}, {'Name': 'Eugenio Suárez', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'SEA', 'Opponent': ' TB', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 553993}, {'Name': 'Jarred Kelenic', 
    # 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'SEA', 'Opponent': ' TB', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 672284}, {'Name': 'Jose Siri', 'Over': '0.5', 'Prop': 'Total Bases', 'Team': 'TB ', 'Opponent': 'SEA', 'PlayerType': 'hitting', 'Date': '06/30/2023', 'Id': 642350}, {'Name': 'Dean Kremer', 'Over': '2.5', 'Prop': 'Earned Runs Allowed', 'Team': 'BAL', 'Opponent': 'MIN', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 665152}, {'Name': 'José Berríos', 'Over': '2.5', 'Prop': 'Earned Runs Allowed', 'Team': 'TOR', 'Opponent': 'BOS', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 621244}, {'Name': 'James Paxton', 'Over': '2.5', 'Prop': 'Earned Runs Allowed', 'Team': 'BOS', 'Opponent': 'TOR', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 572020}, {'Name': 'Austin Gomber', 'Over': '3.0', 'Prop': 'Earned Runs Allowed', 'Team': 'COL', 'Opponent': 'DET', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 596295}, {'Name': 'Bryce Miller', 'Over': '2.5', 'Prop': 'Earned Runs Allowed', 'Team': 'SEA', 'Opponent': ' TB', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 682243}, {'Name': 'Dean Kremer', 'Over': '5.0', 'Prop': 'Hits Allowed', 'Team': 'BAL', 'Opponent': 'MIN', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 665152}, {'Name': 'Pablo López', 'Over': '5.5', 'Prop': 'Hits Allowed', 'Team': 'MIN', 'Opponent': 'BAL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 641154}, {'Name': 'Freddy Peralta', 'Over': '4.5', 'Prop': 'Hits Allowed', 'Team': 'MIL', 'Opponent': 'PIT', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 642547}, {'Name': 'Osvaldo Bido', 'Over': '5.0', 'Prop': 'Hits Allowed', 'Team': 'PIT', 'Opponent': 'MIL', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 674370}, {'Name': 'José Berríos', 'Over': '5.5', 'Prop': 'Hits Allowed', 'Team': 'TOR', 'Opponent': 'BOS', 'PlayerType': 'pitching', 'Date': '06/30/2023', 'Id': 621244}]

    prunedBetData = []
    for entry in nonPrunedBetData:
        if entry['Team'] in gamesToConsider or entry['Opponent'] in gamesToConsider:
            prunedBetData.append(entry)
        if gamesToConsider[0] == '':
            prunedBetData.append(entry)

    # True: include playoffs / False: only regular season
    betAssist = BetAssist(False, homeTeams, sport)
    betAssist.findGoodBets(prunedBetData)

# Written by Ethan Roush
import copy

from nba_api.stats.endpoints import playergamelog

#from MongoPersister import MongoPersister
from Scraper import Scraper
import sys
import time

# GLOBALS
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

NUM_MULTI_PLAYERS = 2

class BetAssist:
    includePlayoffs = False
    playerGames = {}
    homeTeams = []
    numAPICalls = 0

    def __init__(self, includePlayoffs, homeTeams):
        self.includePlayoffs = includePlayoffs
        self.playerGames = {}
        self.homeTeams = homeTeams
        self.numAPICalls = 0

    def _getGames(self, playerID):
        if playerID not in self.playerGames:
            regularSeasonGamelogs = playergamelog.PlayerGameLog(playerID)
            self.numAPICalls += 1
            regularSeasonGames = regularSeasonGamelogs.get_dict()['resultSets'][0]['rowSet']
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


    def _getPlayerStatlines(self, playerID):
        games = self._getGames(playerID)
        seasonStatlines = []
        for i in range(0, len(games)):

            isHomeGame = True
            if '@' in games[i][OPPONENT_IND]:
                isHomeGame = False

            isPlayoffGame = False
            if games[i][GAME_TYPE_IND] == '42022':
                isPlayoffGame = True

            game_dict = {'opp': games[i][OPPONENT_IND][-3:], 'min': games[i][MIN_IND],'home': isHomeGame, 'playoff': isPlayoffGame,
                         'pts': games[i][POINT_IND], 'asts': games[i][ASSIST_IND], 'rebs': games[i][REB_IND],
                         '3pm': games[i][THREE_POINT_MAKE_IND], 'stls': games[i][STEAL_IND],
                         'blks': games[i][BLOCK_IND], 'fga': games[i][FGA_IND], 'tos': games[i][TO_IND],
                         'pfs': games[i][PF_IND], 'ftm': games[i][FTM_IND]}

            seasonStatlines.append(game_dict)

        return seasonStatlines

    def _calculateHitPercentage(self, statlines, overAmnt, category):
        numHits = 0
        totalMin = 0
        for statline in statlines:
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
            elif category == '3-PT Made' and threePointMakes > overAmnt:
                numHits += 1
            elif category == 'Blks+Stls' and (blks + stls) > overAmnt:
                numHits += 1
            elif category == 'Blocked Shots' and blks > overAmnt:
                numHits += 1
            elif category == 'Steals' and stls > overAmnt:
                numHits += 1
            elif category == 'Turnovers' and tos > overAmnt:
                numHits += 1
            elif category == 'Free Throws Made' and ftm > overAmnt:
                numHits += 1
            elif category == 'FG Attempted' and fga >= overAmnt:
                numHits += 1
            elif category == 'Personal Fouls' and pfs > overAmnt:
                numHits += 1
            elif category == 'Fantasy Score' and fantasyScore >= overAmnt:
                numHits += 1

        avgMin = totalMin / len(statlines) if len(statlines) != 0 else 0
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

    '''
    def _persistToDatabase(self, entries):
        persister = MongoPersister()
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

            alreadyInDB = False
            for dbBet in dbBets:
                if dbBet['Id'] == unpersistedBetId and dbBet['Date'] == unpersistedBetDate and dbBet['Prop'] == unpersistedBetCategory \
                    and dbBet['Over'] == unpersistedBetOver and dbBet['Decision'] == unpersistedBetDecision:
                    alreadyInDB = True

            if not alreadyInDB:
                unpersistedBets.append({'Id': unpersistedBetId, 'Name': unpersistedBetName, 'Date': unpersistedBetDate,
                                        'TotalHitPercentage': unpersistedBetTotalHitPercentage,
                                        'Prop': unpersistedBetCategory, 'HitPercentagesPrintableDict': unpersistedBetHitPercentagesPrintableDict,
                                        'Over': unpersistedBetOver, 'Decision': unpersistedBetDecision, 'Risky': unpersistedBetRisk, 'Team': unpersistedBetTeam})

        persister.batchWrite(unpersistedBets)
        '''


    def findGoodBets(self, betData):
        print("Finding Good Bets.")
        betList = []
        startTime = time.time()
        for i in range(len(betData)):

            # necessary so API calls for game data do not cause HTTP Timeout
            if self.numAPICalls % 8 == 0:
                time.sleep(5)

            if i % 30 == 0:
                elapsedTime = time.time() - startTime
                print(f'{i}/{len(betData)} player props analyzed. {elapsedTime:.2f} seconds elapsed')

            entry = betData[i]
            playerName = entry['Name']
            playerID = entry['Id']
            overAmnt = float(entry['Over'])
            category = entry['Prop']
            team = entry['Team']
            opponent = entry['Opponent']
            entry['AvgMinOverLastFiveGames'] = 0
            entry['Risky'] = False

            games = self._getPlayerStatlines(playerID)

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

            if entry['Risky'] is False and len(bottomNoRiskBets) < 10 \
                    and self._checkOccurences(entry['Id'], bottomNoRiskBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] <= 0.43:
                entry['Decision'] =  'Under'
                bottomNoRiskBets.append(entry)
            elif entry['Risky'] is True and len(bottomRiskyBets) < 3 \
                    and self._checkOccurences(entry['Id'], bottomRiskyBets) < NUM_MULTI_PLAYERS and entry['TotalHitPercentage'] <= 0.43:
                entry['Decision'] =  'Under'
                bottomRiskyBets.append(entry)

            if len(bottomNoRiskBets) == 10 and len(bottomRiskyBets) == 3:
                break

        '''
        try:
            self._persistToDatabase(topRiskyBets + topNoRiskBets + bottomNoRiskBets + bottomRiskyBets)
        except Exception as e:
            print("Error with database persistence: " + str(e))
        '''

        print('\n-----------NON-RISKY BETS WITH HIGHEST HIT PERCENTAGES (OVERS)-----------')

        self._printBets(topNoRiskBets)

        print('\n-----------RISKY BETS WITH HIGHEST HIT PERCENTAGES (OVERS)-----------')

        self._printBets(topRiskyBets)

        print('\n-----------NON-RISKY BETS WITH LOWEST HIT PERCENTAGES (UNDERS)-----------')

        self._printBets(bottomNoRiskBets)

        print('\n-----------RISKY BETS WITH LOWEST HIT PERCENTAGES (UNDERS)-----------')

        self._printBets(bottomRiskyBets)


if __name__ == '__main__':
    homeTeams = input("Enter three-letter home teams separated by commas.\nOnly the games these teams are playing will be considered in the output.\nExample input format: NYK, MIA, BOS\n").split(",")
    homeTeams = [team.strip().upper() for team in homeTeams]
    NBAScraper = Scraper()
    nonPrunedBetData = NBAScraper.scrapeNBAProps()

    prunedBetData = []
    for entry in nonPrunedBetData:
        if entry['Team'] in homeTeams or entry['Opponent'] in homeTeams:
            prunedBetData.append(entry)

    if len(sys.argv[1]) > 1 and sys.argv[1] == '--playoffs':
        betAssist = BetAssist(True, homeTeams)
        betAssist.findGoodBets(prunedBetData)
    else:
        betAssist = BetAssist(False, homeTeams)
        betAssist.findGoodBets(prunedBetData)

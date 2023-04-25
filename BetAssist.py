# Written by Ethan Roush
import time

import requests
from nba_api.stats.endpoints import playergamelog
from Scraper import Scraper

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

NUM_GAMES_WEIGHT = 0.5
SEASON_WEIGHT = 0.25
SEASON_WEIGHT_NO_OPPONENT = 1 - NUM_GAMES_WEIGHT
VERSUS_OPPONENT_WEIGHT = 0.25


class BetAssist:
    def _getGames(self, playerID):
        regularSeasonGamelogs = playergamelog.PlayerGameLog(playerID)
        playoffGameLogs = playergamelog.PlayerGameLog(playerID, season_type_all_star="Playoffs")
        regularSeasonGames = regularSeasonGamelogs.get_dict()['resultSets'][0]['rowSet']
        playoffGames = playoffGameLogs.get_dict()['resultSets'][0]['rowSet']
        playoffGames.extend(regularSeasonGames)
        return playoffGames

    def _getPlayerStatlines(self, playerID, numGames):
        games = self._getGames(playerID)
        abridgedStatlines = []
        for i in range(0, numGames):
            game_dict = {'opp': games[i][OPPONENT_IND], 'pts': games[i][POINT_IND], 'asts': games[i][ASSIST_IND], 'rebs': games[i][REB_IND]}
            abridgedStatlines.append(game_dict)
        seasonStatlines = []
        for i in range(0, len(games)):
            game_dict = {'opp': games[i][OPPONENT_IND], 'pts': games[i][POINT_IND], 'asts': games[i][ASSIST_IND], 'rebs': games[i][REB_IND]}
            seasonStatlines.append(game_dict)
        return abridgedStatlines, seasonStatlines

    def _getPlayerTotals(self, playerID, numGames, opponent):
        abridgedPlayerTotals = {'Points': 0.0, 'Rebounds': 0.0, 'Assists': 0.0, 'Pts+Rebs+Asts': 0.0, 'Pts+Rebs': 0.0,
                        'Pts+Asts': 0.0, 'Rebs+Asts': 0.0}
        seasonPlayerTotals = {'Points': 0.0, 'Rebounds': 0.0, 'Assists': 0.0, 'Pts+Rebs+Asts': 0.0, 'Pts+Rebs': 0.0,
                        'Pts+Asts': 0.0, 'Rebs+Asts': 0.0}
        versusOpponentPlayerTotals = {'Points': 0.0, 'Rebounds': 0.0, 'Assists': 0.0, 'Pts+Rebs+Asts': 0.0, 'Pts+Rebs': 0.0,
                              'Pts+Asts': 0.0, 'Rebs+Asts': 0.0}
        timesPlayedOpponent = 0
        abridgedStatlines, seasonStatlines = self._getPlayerStatlines(playerID, numGames)

        for statline in abridgedStatlines:
            abridgedPlayerTotals['Points'] += statline['pts']
            abridgedPlayerTotals['Pts+Rebs+Asts'] += statline['pts']
            abridgedPlayerTotals['Pts+Rebs'] += statline['pts']
            abridgedPlayerTotals['Pts+Asts'] += statline['pts']
            abridgedPlayerTotals['Rebounds'] += statline['rebs']
            abridgedPlayerTotals['Pts+Rebs'] += statline['rebs']
            abridgedPlayerTotals['Pts+Rebs+Asts'] += statline['rebs']
            abridgedPlayerTotals['Rebs+Asts'] += statline['rebs']
            abridgedPlayerTotals['Assists'] += statline['asts']
            abridgedPlayerTotals['Pts+Rebs+Asts'] += statline['asts']
            abridgedPlayerTotals['Pts+Asts'] += statline['asts']
            abridgedPlayerTotals['Rebs+Asts'] += statline['asts']

        abridged_player_totals = {key: value / numGames for key, value in abridgedPlayerTotals.items()}

        for statline in seasonStatlines:
            seasonPlayerTotals['Points'] += statline['pts']
            seasonPlayerTotals['Pts+Rebs+Asts'] += statline['pts']
            seasonPlayerTotals['Pts+Rebs'] += statline['pts']
            seasonPlayerTotals['Pts+Asts'] += statline['pts']
            seasonPlayerTotals['Rebounds'] += statline['rebs']
            seasonPlayerTotals['Pts+Rebs'] += statline['rebs']
            seasonPlayerTotals['Pts+Rebs+Asts'] += statline['rebs']
            seasonPlayerTotals['Rebs+Asts'] += statline['rebs']
            seasonPlayerTotals['Assists'] += statline['asts']
            seasonPlayerTotals['Pts+Rebs+Asts'] += statline['asts']
            seasonPlayerTotals['Pts+Asts'] += statline['asts']
            seasonPlayerTotals['Rebs+Asts'] += statline['asts']
            if opponent in statline['opp']:
                timesPlayedOpponent += 1
                versusOpponentPlayerTotals['Points'] += statline['pts']
                versusOpponentPlayerTotals['Pts+Rebs+Asts'] += statline['pts']
                versusOpponentPlayerTotals['Pts+Rebs'] += statline['pts']
                versusOpponentPlayerTotals['Pts+Asts'] += statline['pts']
                versusOpponentPlayerTotals['Rebounds'] += statline['rebs']
                versusOpponentPlayerTotals['Pts+Rebs'] += statline['rebs']
                versusOpponentPlayerTotals['Pts+Rebs+Asts'] += statline['rebs']
                versusOpponentPlayerTotals['Rebs+Asts'] += statline['rebs']
                versusOpponentPlayerTotals['Assists'] += statline['asts']
                versusOpponentPlayerTotals['Pts+Rebs+Asts'] += statline['asts']
                versusOpponentPlayerTotals['Pts+Asts'] += statline['asts']
                versusOpponentPlayerTotals['Rebs+Asts'] += statline['asts']


        season_player_totals = {key: value / len(seasonStatlines) for key, value in seasonPlayerTotals.items()}

        if timesPlayedOpponent != 0:
            versus_opponent_player_totals = {key: value / timesPlayedOpponent for key, value in versusOpponentPlayerTotals.items()}
        else:
            versus_opponent_player_totals = {}


        return abridged_player_totals, season_player_totals, versus_opponent_player_totals, timesPlayedOpponent

    # betData must be in the format: [(playerID, overNum, category), ...]
    # where overNum is the over/under and category is the statistical combination
    # of the over/under (pts, rebs, asts, pts_asts_rebs, pts_rebs, pts_asts, rebs_asts)
    # betThreshold is a float between 0.0 and 1.0
    def findGoodBets(self, betData, overBetThreshold, underBetThreshold, numGames):
        print("Beginning to find \"Good\" Bets.")
        goodBetListNumGames = []
        betListAllCategories = []
        for i in range(len(betData)):
            if i % 4 == 0:
                time.sleep(5)
            entry = betData[i]
            playerID = entry['id']
            overNum = float(entry['Over'])
            category = entry['Prop']
            opponent = entry['Team']

            abridgedPlayerTotals, seasonPlayerTotals, versusOpponentPlayerTotals, timesPlayedOpponent = self._getPlayerTotals(playerID, numGames, opponent)

            numGamesAverage = abridgedPlayerTotals[category]

            numGamesOverage = numGamesAverage / overNum - 1

            numGamesUnderage = 1 - numGamesAverage / overNum

            #Calculating good bets considering numGames average only
            if numGamesOverage > overBetThreshold:
                betInfo = [entry['Name'], category, "OVER", round(numGamesOverage, 3), overNum]
                goodBetListNumGames.append(betInfo)

            if numGamesUnderage > underBetThreshold:
                betInfo = [entry['Name'], category, "UNDER", round(numGamesUnderage, 3), overNum]
                goodBetListNumGames.append(betInfo)

            #Calculating good bets considering numGames average, season average, and versus opponent average
            if timesPlayedOpponent != 0:
                seasonAverage = seasonPlayerTotals[category]
                versusOpponentAverage = versusOpponentPlayerTotals[category]

                seasonOverage = seasonAverage / overNum - 1
                versusOpponentOverage = versusOpponentAverage / overNum - 1

                seasonUnderage = 1 - seasonAverage / overNum
                versusOpponentUnderage = 1 - versusOpponentAverage / overNum

                numGamesOverage *= NUM_GAMES_WEIGHT
                seasonOverage *= SEASON_WEIGHT
                versusOpponentOverage *= VERSUS_OPPONENT_WEIGHT
                totalOverage = numGamesOverage + seasonOverage + versusOpponentOverage

                numGamesUnderage *= NUM_GAMES_WEIGHT
                seasonUnderage *= SEASON_WEIGHT
                versusOpponentUnderage *= VERSUS_OPPONENT_WEIGHT
                totalUnderage = numGamesUnderage + seasonUnderage + versusOpponentUnderage

                if(entry['Name'] == 'Dorian Finney-Smith'):
                    print('\n' + category)
                    print(abridgedPlayerTotals)
                    print(seasonPlayerTotals)
                    print(versusOpponentPlayerTotals)
                    print(numGamesOverage)
                    print(seasonOverage)
                    print(versusOpponentOverage)

                betInfo = [entry['Name'], category, "OVER", round(totalOverage, 3), overNum]
                betListAllCategories.append(betInfo)
                betInfo = [entry['Name'], category, "UNDER", round(totalUnderage, 3), overNum]
                betListAllCategories.append(betInfo)

            elif timesPlayedOpponent == 0:
                seasonAverage = seasonPlayerTotals[category]

                seasonOverage = seasonAverage / overNum - 1

                seasonUnderage = 1 - seasonAverage / overNum

                numGamesOverage *= NUM_GAMES_WEIGHT
                seasonOverage *= SEASON_WEIGHT_NO_OPPONENT
                totalOverage = numGamesOverage + seasonOverage

                numGamesUnderage *= NUM_GAMES_WEIGHT
                seasonUnderage *= SEASON_WEIGHT_NO_OPPONENT
                totalUnderage = numGamesUnderage + seasonUnderage

                betInfo = [entry['Name'], category, "OVER", round(totalOverage, 3), "NO VS. OPP DATA", overNum]
                betListAllCategories.append(betInfo)
                betInfo = [entry['Name'], category, "UNDER", round(totalUnderage, 3), "NO VS. OPP DATA", overNum]
                betListAllCategories.append(betInfo)


        sortedGoodBetListNumGames = sorted(goodBetListNumGames, key=lambda x: x[3], reverse=True)
        print()
        print(f"BET LIST CONSIDERING {numGames} GAMES BACK AVERAGES WITH A WEIGHT OF 1.0: ")
        print(sortedGoodBetListNumGames)
        sortedBetListAllCategories = sorted(betListAllCategories, key=lambda x: x[3], reverse=True)[0:101]
        print()
        print(f"BET LIST CONSIDERING {numGames} GAMES BACK WITH WEIGHT {NUM_GAMES_WEIGHT}, SEASON AVERAGE WITH WEIGHT {SEASON_WEIGHT}, VERSUS OPPONENT AVERAGE WITH WEIGHT {VERSUS_OPPONENT_WEIGHT}: ")
        print(sortedBetListAllCategories)
        print()
        return sortedGoodBetListNumGames, sortedBetListAllCategories


if __name__ == '__main__':
    NBAScraper = Scraper()
    betData = NBAScraper.scrapeNBAProps()
    betAssist = BetAssist()
    betAssist.findGoodBets(betData, 0.2, 0.25, 5)

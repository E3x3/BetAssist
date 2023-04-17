# Written by Ethan Roush
import time

import requests
from nba_api.stats.endpoints import playergamelog
from Scraper import Scraper

# GLOBALS
POINT_IND = 24
REB_IND = 18
ASSIST_IND = 19


class BetAssist:
    def _getGames(self, playerID):
        gamelogs = playergamelog.PlayerGameLog(playerID)
        return gamelogs.get_dict()['resultSets'][0]['rowSet']

    # TODO: take into account missed games
    def _getPlayerStatlines(self, playerID, numGames):
        games = self._getGames(playerID)
        statlines = []
        for i in range(0, numGames):
            game_dict = {'pts': games[i][POINT_IND], 'asts': games[i][ASSIST_IND], 'rebs': games[i][REB_IND]}
            statlines.append(game_dict)
        return statlines

    def _getPlayerTotals(self, playerID, numGames):
        print(playerID)
        playerTotals = {'Points': 0.0, 'Rebounds': 0.0, 'Assists': 0.0, 'Pts+Rebs+Asts': 0.0, 'Pts+Rebs': 0.0,
                        'Pts+Asts': 0.0, 'Rebs+Asts': 0.0}
        statlines = self._getPlayerStatlines(playerID, numGames)

        for statline in statlines:
            playerTotals['Points'] += statline['pts']
            playerTotals['Pts+Rebs+Asts'] += statline['pts']
            playerTotals['Pts+Rebs'] += statline['pts']
            playerTotals['Pts+Asts'] += statline['pts']
            playerTotals['Rebounds'] += statline['rebs']
            playerTotals['Pts+Rebs'] += statline['rebs']
            playerTotals['Pts+Rebs+Asts'] += statline['rebs']
            playerTotals['Rebs+Asts'] += statline['rebs']
            playerTotals['Assists'] += statline['asts']
            playerTotals['Pts+Rebs+Asts'] += statline['asts']
            playerTotals['Pts+Asts'] += statline['asts']
            playerTotals['Rebs+Asts'] += statline['asts']

        player_totals = {key: value / numGames for key, value in playerTotals.items()}

        return player_totals

    # betData must be in the format: [(playerID, overNum, category), ...]
    # where overNum is the over/under and category is the statistical combination
    # of the over/under (pts, rebs, asts, pts_asts_rebs, pts_rebs, pts_asts, rebs_asts)
    # betThreshold is a float between 0.0 and 1.0
    def findGoodBets(self, betData, overBetThreshold, underBetThreshold, numGames):
        goodBetList = []
        for i in range(len(betData)):
            if i % 10 == 0:
                time.sleep(5)
            entry = betData[i]
            playerID = entry['id']
            overNum = float(entry['Over'])
            category = entry['Prop']

            playerTotals = self._getPlayerTotals(playerID, numGames)
            playerStat = playerTotals[category]

            overageAmount = playerStat / overNum - 1

            underageAmount = 1 - playerStat / overNum

            if overageAmount > overBetThreshold:
                betInfo = [entry['Name'], category, "OVER", round(overageAmount, 3), overNum]
                goodBetList.append(betInfo)

            if underageAmount > underBetThreshold:
                betInfo = [entry['Name'], category, "UNDER", round(underageAmount, 3), overNum]
                goodBetList.append(betInfo)

        return goodBetList


if __name__ == '__main__':
    NBAScraper = Scraper()
    betData = NBAScraper.scrapeNBAProps()
    betAssist = BetAssist()
    print(betAssist.findGoodBets(betData, 0.2, 0.25, 5))

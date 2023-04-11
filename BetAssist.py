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
    #bets = [['Bam Adebayo', 'Points', 'UNDER', 0.323, 19.5], ['Bogdan Bogdanovic', 'Points', 'OVER', 0.304, 11.5], ['Saddiq Bey', 'Points', 'OVER', 0.368, 9.5], ['Onyeka Okongwu', 'Points', 'OVER', 0.36, 7.5], ['Mike Conley', 'Points', 'OVER', 0.255, 14.5], ['Austin Reaves', 'Points', 'OVER', 0.29, 15.5], ['Rui Hachimura', 'Points', 'OVER', 0.707, 7.5], ['Malik Beasley', 'Points', 'OVER', 0.52, 7.5], ['Scottie Barnes', 'Points', 'UNDER', 0.406, 15.5], ['Coby White', 'Points', 'OVER', 0.453, 9.5], ['Patrick Williams', 'Points', 'OVER', 0.547, 7.5], ['Herbert Jones', 'Points', 'OVER', 0.4, 11.0], ['Dorian Finney-Smith', 'Points', 'OVER', 0.3, 8.0], ['Donovan Mitchell', 'Points', 'OVER', 0.252, 30.5], ['Ivica Zubac', 'Points', 'OVER', 0.352, 10.5], ['Chris Paul', 'Points', 'OVER', 0.289, 13.5], ['Jimmy Butler', 'Rebounds', 'UNDER', 0.486, 7.0], ['Tyler Herro', 'Rebounds', 'UNDER', 0.28, 5.0], ['Austin Reaves', 'Rebounds', 'UNDER', 0.314, 3.5], ['Kyle Anderson', 'Rebounds', 'UNDER', 0.4, 8.0], ['Jarred Vanderbilt', 'Rebounds', 'UNDER', 0.273, 5.5], ['DeMar DeRozan', 'Rebounds', 'UNDER', 0.32, 5.0], ['Scottie Barnes', 'Rebounds', 'UNDER', 0.486, 7.0], ['Luguentz Dort', 'Rebounds', 'OVER', 0.273, 5.5], ['James Harden', 'Rebounds', 'UNDER', 0.4, 6.0], ['Evan Mobley', 'Rebounds', 'OVER', 0.25, 8.0], ['Stephen Curry', 'Rebounds', 'UNDER', 0.267, 6.0], ['Harrison Barnes', 'Rebounds', 'UNDER', 0.4, 4.0], ['Devin Booker', 'Rebounds', 'UNDER', 0.28, 5.0], ['Trae Young', 'Assists', 'OVER', 0.422, 9.0], ['Jimmy Butler', 'Assists', 'OVER', 0.233, 6.0], ['Austin Reaves', 'Assists', 'OVER', 0.35, 4.0], ['Zach LaVine', 'Assists', 'OVER', 0.2, 4.5], ['CJ McCollum', 'Assists', 'UNDER', 0.309, 5.5], ['Spencer Dinwiddie', 'Assists', 'OVER', 0.333, 9.0], ["Royce O'Neale", 'Assists', 'OVER', 0.92, 2.5], ['Devin Booker', 'Assists', 'OVER', 0.28, 5.0], ['Chris Paul', 'Assists', 'UNDER', 0.326, 9.5], ['Bam Adebayo', 'Pts+Rebs+Asts', 'UNDER', 0.275, 32.0], ['Tyler Herro', 'Pts+Rebs+Asts', 'UNDER', 0.261, 29.5], ['Taurean Prince', 'Pts+Rebs+Asts', 'UNDER', 0.282, 19.5], ['Scottie Barnes', 'Pts+Rebs+Asts', 'UNDER', 0.396, 27.5], ['Herbert Jones', 'Pts+Rebs+Asts', 'OVER', 0.243, 18.5], ['Ivica Zubac', 'Pts+Rebs+Asts', 'OVER', 0.22, 20.5], ['Bam Adebayo', 'Pts+Rebs', 'UNDER', 0.295, 29.5], ['Tyler Herro', 'Pts+Rebs', 'UNDER', 0.255, 25.5], ['Bogdan Bogdanovic', 'Pts+Rebs', 'OVER', 0.304, 13.5], ['Saddiq Bey', 'Pts+Rebs', 'OVER', 0.304, 13.5], ['Onyeka Okongwu', 'Pts+Rebs', 'OVER', 0.259, 13.5], ['Rui Hachimura', 'Pts+Rebs', 'OVER', 0.652, 11.5], ['Scottie Barnes', 'Pts+Rebs', 'UNDER', 0.431, 22.5], ['Coby White', 'Pts+Rebs', 'OVER', 0.6, 11.5], ['Patrick Williams', 'Pts+Rebs', 'OVER', 0.505, 10.5], ['Herbert Jones', 'Pts+Rebs', 'OVER', 0.277, 15.5], ['Dorian Finney-Smith', 'Pts+Rebs', 'OVER', 0.248, 12.5], ['Donovan Mitchell', 'Pts+Rebs', 'OVER', 0.252, 34.5], ['Ivica Zubac', 'Pts+Rebs', 'OVER', 0.2, 20.5], ['Bam Adebayo', 'Pts+Asts', 'UNDER', 0.307, 22.5], ['Tyler Herro', 'Pts+Asts', 'UNDER', 0.257, 24.5], ['Bogdan Bogdanovic', 'Pts+Asts', 'OVER', 0.333, 13.5], ['Saddiq Bey', 'Pts+Asts', 'OVER', 0.448, 10.5], ['Austin Reaves', 'Pts+Asts', 'OVER', 0.27, 20.0], ['Taurean Prince', 'Pts+Asts', 'UNDER', 0.29, 15.5], ['Scottie Barnes', 'Pts+Asts', 'UNDER', 0.366, 20.5], ['Coby White', 'Pts+Asts', 'OVER', 0.424, 12.5], ['Herbert Jones', 'Pts+Asts', 'OVER', 0.329, 14.0], ['Ivica Zubac', 'Pts+Asts', 'OVER', 0.27, 11.5], ['Trae Young', 'Rebs+Asts', 'OVER', 0.217, 12.0], ['Scottie Barnes', 'Rebs+Asts', 'UNDER', 0.357, 11.5], ['James Harden', 'Rebs+Asts', 'UNDER', 0.261, 16.5], ['Spencer Dinwiddie', 'Rebs+Asts', 'OVER', 0.296, 12.5], ['Evan Mobley', 'Rebs+Asts', 'OVER', 0.255, 11.0]]
    #sorted_list = sorted(bets, key = lambda x: x[3], reverse=True)
    #print(sorted_list)


    NBAScraper = Scraper()
    betData = NBAScraper.scrapeNBAProps()

    '''
    playerIDs = [entry['id'] for entry in betData]
    print(len(playerIDs))
    url = f"https://www.balldontlie.io/api/v1/stats?seasons=2023"
    for id in playerIDs:
        url += f"&player_ids[]={str(id)}"
    print(url)
    response = requests.get(url)
    print(response)
    '''



    betAssist = BetAssist()
    print(betAssist.findGoodBets(betData, 0.2, 0.25, 5))

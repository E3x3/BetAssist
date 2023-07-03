# https://www.actowizsolutions.com/scrape-sports-betting-props-from-prizepicks.php
# Written by Ethan Roush
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time
import datetime
from nba_api.stats.static import players
import statsapi


class Scraper:
    def scrapeProps(self, sport):
        options = webdriver.ChromeOptions()
        options.headless = True
        driver = uc.Chrome(options=options, version_main=113)
        driver.get("https://app.prizepicks.com/")

        time.sleep(8)
        driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div/div[3]/button").click()
        time.sleep(1)

        ppPlayers = []
        
        if sport == "NBA":
            driver.find_element(By.XPATH, "//div[@class='name'][normalize-space()='NBA']").click()
        if sport == "MLB":
            driver.find_element(By.XPATH, "//div[@class='name'][normalize-space()='MLB']").click()
        time.sleep(2)

        # stats_container = WebDriverWait(driver, 1).until(EC.visibility_of_element_located())

        categories = driver.find_element(By.CSS_SELECTOR, ".stat-container").text.split("\n")
        time.sleep(2)

        MLB_pitching_categories = ["Pitches Thrown", "Pitcher Strikeouts", "Pitching Outs", "Hits Allowed", "Walks Allowed", "Earned Runs Allowed"]
        MLB_hitting_categories = ["Total Bases", "Hitter Strikeouts", "Runs"]

        for category in categories:
            if (category == 'Points' or category == 'Rebounds' or category == 'Assists' or category == "3-PT Made"
                    or category == "FG Attempted" or category == "Personal Fouls" or category == "Free Throws Made"
                    or category == "Blks+Stls" or category == "Blocked Shots" or category == "Steals" or category == "Turnovers"
                    or category == 'Pts+Rebs+Asts' or category == 'Pts+Rebs'
                    or category == 'Pts+Asts' or category == 'Rebs+Asts') or category == 'Fantasy Score' or category in MLB_pitching_categories or category in MLB_hitting_categories:
            
                print("scraping category: " + category)
                driver.find_element(By.XPATH, f"//div[text()='{category}']").click()

                projectionsPP = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".projection"))
                )

                for projections in projectionsPP:
                    playerType = ""
                    if category in MLB_pitching_categories:
                        playerType = "pitching"
                    if category in MLB_hitting_categories:
                        playerType = "hitting"

                    names = projections.find_element(By.CLASS_NAME, "name").text
                    pts = projections.find_element(By.CLASS_NAME, "presale-score").get_attribute("textContent")
                    prototype = projections.find_element(By.CLASS_NAME, "text").get_attribute("textContent")
                    team = projections.find_element(By.CLASS_NAME, "team-position").text[:3]
                    opponent = projections.find_element(By.CLASS_NAME, "opponent").text[-3:]
                    current_date = datetime.date.today()
                    formatted_date = current_date.strftime("%m/%d/%Y")

                    playerInfo = {
                        'Name': names,
                        'Over': pts,
                        'Prop': category,
                        'Team': team,
                        'Opponent': opponent,
                        'PlayerType': playerType,
                        'Date': formatted_date
                    }

                    ppPlayers.append(playerInfo)

        ppPlayersTrimmed = []
        for player in ppPlayers:
            player_name = player['Name']
            playerlist = []
            if sport == "MLB":
                playerlist = []
                while playerlist == []:
                    try:
                        playerlist = statsapi.lookup_player(player_name)
                        break
                    except:
                        print("Connection refused by the server...")
                        print("Sleeping for 5 seconds.")
                        time.sleep(5)
                        print("Continue...")
            if sport == "NBA":
                playerlist = []
                while playerlist == []:
                    try:
                        playerlist = list(players.find_players_by_full_name(player_name))
                        break
                    except:
                        print("Connection refused by the server...")
                        print("Sleeping for 5 seconds.")
                        time.sleep(5)
                        print("Continue...")

            if len(playerlist) == 1:
                newPlayer = player
                newPlayer['Id'] = playerlist[0]['id']
                ppPlayersTrimmed.append(newPlayer)

        print(f"SCRAPING DONE. {str(len(ppPlayersTrimmed))} player props found on PrizePicks.")
        driver.close()
        return ppPlayersTrimmed

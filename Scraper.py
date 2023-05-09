# https://www.actowizsolutions.com/scrape-sports-betting-props-from-prizepicks.php
# Written by Ethan Roush
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from nba_api.stats.static import players
import datetime


class Scraper:
    def scrapeNBAProps(self):
        PATH = "/Users/ethanroush/Documents/chromedriver_mac64/chromedriver"
        driver = webdriver.Chrome(PATH)

        driver.get("https://app.prizepicks.com/")

        # wait = WebDriverWait(driver, 15).until(EC.presence_of_element_located(By.C))
        time.sleep(1)
        driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div/div[3]/button").click()
        time.sleep(1)

        ppPlayers = []

        driver.find_element(By.XPATH, "//div[@class='name'][normalize-space()='NBA']").click()
        time.sleep(2)

        # stats_container = WebDriverWait(driver, 1).until(EC.visibility_of_element_located())
        time.sleep(2)

        categories = driver.find_element(By.CSS_SELECTOR, ".stat-container").text.split("\n")

        for category in categories:
            if (category == 'Points' or category == 'Rebounds' or category == 'Assists' or category == "3-PT Made"
                    or category == "FG Attempted" or category == "Personal Fouls" or category == "Free Throws Made"
                    or category == "Blks+Stls" or category == "Blocked Shots" or category == "Steals" or category == "Turnovers"
                    or category == 'Pts+Rebs+Asts' or category == 'Pts+Rebs'
                    or category == 'Pts+Asts' or category == 'Rebs+Asts') or category == 'Fantasy Score':
                print("scraping category: " + category)
                driver.find_element(By.XPATH, f"//div[text()='{category}']").click()

                projectionsPP = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".projection"))
                )

                for projections in projectionsPP:
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
                        'Date': formatted_date
                    }

                    ppPlayers.append(playerInfo)

        ppPlayersTrimmed = []
        for player in ppPlayers:
            player_name = player['Name']
            playerlist = list(players.find_players_by_full_name(player_name))
            if len(playerlist) != 0:
                newPlayer = player
                newPlayer['Id'] = playerlist[0]['id']
                ppPlayersTrimmed.append(newPlayer)

        print(f"SCRAPING DONE. {str(len(ppPlayersTrimmed))} player props found on PrizePicks.")
        return ppPlayersTrimmed

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
            if (category == 'Points' or category == 'Rebounds' or category == 'Assists'
                    or category == 'Pts+Rebs+Asts' or category == 'Pts+Rebs'
                    or category == 'Pts+Asts' or category == 'Rebs+Asts'):
                print("doing category: " + category)
                driver.find_element(By.XPATH, f"//div[text()='{category}']").click()

                projectionsPP = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".projection"))
                )

                for projections in projectionsPP:
                    names = projections.find_element(By.CLASS_NAME, "name").text
                    pts = projections.find_element(By.CLASS_NAME, "presale-score").get_attribute("textContent")
                    prototype = projections.find_element(By.CLASS_NAME, "text").get_attribute("textContent")
                    team = projections.find_element(By.CLASS_NAME, "opponent").text
                    team = team[-3:]

                    playerInfo = {
                        'Name': names,
                        'Over': pts,
                        'Prop': category,
                        'Team': team,
                    }

                    ppPlayers.append(playerInfo)

        ppPlayersTrimmed = []
        for player in ppPlayers:
            player_name = player['Name']
            playerlist = list(players.find_players_by_full_name(player_name))
            if len(playerlist) != 0:
                newPlayer = player
                newPlayer['id'] = playerlist[0]['id']
                ppPlayersTrimmed.append(newPlayer)

        print(f"Scraping done. {str(len(ppPlayersTrimmed))} over/unders found on PrizePicks.")
        return ppPlayersTrimmed

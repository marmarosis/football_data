import time
from datetime import datetime
import re
import requests
import bs4
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from selenium import webdriver
from openpyxl import load_workbook

# the web page fbref contains historical data about the Bundesliga
web_page = 'https://fbref.com'
league = '/en/comps/20/history/Bundesliga-Seasons'

# obtain the html code as a string
response = requests.get(web_page + league)
html = response.text

# create a BeautifulSoup object
soup = bs4.BeautifulSoup(html, "html.parser")
df_scores_for = pd.DataFrame()
df_scores_against = pd.DataFrame()

# define a function to find only the Bundesliga Stats links
def season_stats(href):
    return href and re.compile("Bundesliga-Stats").search(href)

# loop through the anchor tags
for anchor in soup.find_all(href=season_stats):
    
    # get the linked URL and the text of the anchor tag
    page = anchor.get('href')
    season = anchor.text
  
    # obtain the html code as a string
    response = requests.get(web_page + page)
    html = response.text

    # create a BeautifulSoup object
    soup = bs4.BeautifulSoup(html, "html.parser")
    
    # obtain the tables containing the season's "for" and "against" stats
    table_for = soup.select("#stats_squads_standard_for")
    table_against = soup.select("#stats_squads_standard_against")
    
    df_stats_for = pd.read_html(str(table_for))[0]
    df_stats_against = pd.read_html(str(table_against))[0]
    
    # add the season - anchor text and append the data frame to df_scores_for/against
    df_stats_for['season'] = season
    df_scores_for = df_scores_for.append(df_stats_for)

    df_stats_against['season'] = season
    df_scores_against = df_scores_against.append(df_stats_against)
    
    time.sleep(0.2)

# write the scraped data to an Excel file
with pd.ExcelWriter('bundesliga_stats.xlsx') as writer:
    df_scores_for.to_excel(writer, sheet_name="stats-for")
    df_scores_against.to_excel(writer, sheet_name="stats-against")
print('For/against stats written to file!')

# for red/yellow cards, we use transfermarkt instead of fbref
driver = webdriver.Chrome()
df_scores_cards = pd.DataFrame()
base = 'https://www.transfermarkt.co.uk/bundesliga/fairnesstabelle/wettbewerb/L1/saison_id/'

# create a list containing all the years from 1980 to the current year
years = []
start_year = 1980
current_year = datetime.now().year

while start_year < current_year:
    years.append(start_year)
    start_year = start_year + 1

# loop through all the years
for year in years:

    # get the URL of the season
    page = base + str(year)
    season = str(year)+'-'+str(year+1)
    
    # obtain the html code as a string
    response = driver.get(page)
    html = driver.page_source
    
    # obtain the table containing the season's stats
    tables = pd.read_html(html, attrs = {'class':'items'})
    df_cards = tables[0]
    
    # add the season - anchor text and append the data frame to df_scores_cards
    df_cards['season'] = season
    df_scores_cards = df_scores_cards.append(df_cards)
    
    time.sleep(0.2)
    year = year + 1

# print the scraped data frame to a new sheet in the same Excel file
df_scores_cards.to_excel(writer, sheet_name="fairplay")

print('Fair play data written to file!')

# for goals for and against, we also use transfermarkt
df_scores_goals = pd.DataFrame()
base = 'https://www.transfermarkt.co.uk/bundesliga/tabelle/wettbewerb/L1/saison_id/'

# loop through all the years
for year in years:

    # get the URL of the season
    page = base + str(year)
    season = str(year)+'-'+str(year+1)

    # obtain the html code as a string
    response = driver.get(page)
    html = driver.page_source
    
    # obtain the table containing the season's stats
    tables = pd.read_html(html)
    df_goals = tables[3]
    
    # add the season - anchor text and append the data frame to df_scores_goals 
    df_goals['season'] = season
    df_scores_goals = df_scores_goals.append(df_goals)
    
    time.sleep(0.2)
    year = year + 1

# print the scraped data frame to a new sheet in the same Excel file
df_scores_goals.to_excel(writer, sheet_name="goals")

driver.quit()

print('Goals data written to file, stats scraping complete!')

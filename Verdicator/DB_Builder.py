import json
import os
import subprocess
import pandas as pd
import sqlite3
from search_alg import catch_verdict, all_verdicts
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import re
from summarizer import sum
from franchises import TitleTree

def create():
    api_token = {"username": "nadavzvulun", "key": "53fcf81243a27d02561d91d8b8101f26"}

    os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)
    with open(os.path.expanduser("~/.kaggle/kaggle.json"), "w") as f:
        json.dump(api_token, f)

    os.chmod(os.path.expanduser("~/.kaggle/kaggle.json"), 0o600)

    subprocess.run(["kaggle", "datasets", "download", "-d", "tamber/steam-video-games"])
    subprocess.run(["unzip", "steam-video-games.zip", "-d", "./database"])

    df = pd.read_csv('./database/steam-200k.csv', usecols=[1])  # Column index 1 = name
    df.columns = ['name']  # Rename column to "Name"
    df = df.drop_duplicates()
    for site in ['IGN','Gamespot','Game_Rant', 'PC_Gamer']:
        df[f'{site}_rating'] = None
        df[f'{site}_title'] = None
        df[f'{site}_link'] = None
        df[f'{site}_text'] = None
        df[f'{site}_visited'] = False
    df['Verdict_Sum'] = None
    df['Visited'] = False
    print(df.head())
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('Video_Games.db')

    # Write DataFrame to table named 'games'
    df.to_sql('Video_Games', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def build(limit):
    conn = sqlite3.connect('Video_Games.db')
    df = pd.read_sql("SELECT * FROM Video_Games", conn)

    i = 0
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        fail_count = 10
    except Exception as e:
        print(e)
        return
    for index, row in df.iterrows():
        if i > limit:
            break
        elif i != 0 and i % 30 == 0: #Avoids first save and auto-saves when completes 50 rows
            print('\n----------------------------------------\nAuto-Saving after 30 rows\n----------------------------------------')
            df.to_sql('Video_Games', conn, if_exists='replace', index=False)
        game = row['name']
        sites = ['IGN', 'Gamespot', 'Game_Rant','PC_Gamer']
        if row['IGN_visited']:
            sites.remove('IGN')
        if row['Gamespot_visited']:
            sites.remove('Gamespot')
        if row['Game_Rant_visited']:
            sites.remove('Game_Rant')
        if row['PC_Gamer_visited']:
            sites.remove('PC_Gamer')
        if sites:
            i += 1
        try:
            verdicts = all_verdicts(game, driver, sites)
        except Exception as e:
            try:
                fail_count -= 1
                if fail_count <= 0:
                    break
                driver.quit()
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            except:
                print(e)
                continue
        for site in sites:
            row[f'{site}_rating'] = verdicts[site][0]
            row[f'{site}_title'] = verdicts[site][1]
            row[f'{site}_link'] = verdicts[site][2]
            row[f'{site}_text'] = verdicts[site][3]
            row[f'{site}_visited'] = True

        print(f'Game number {index}: "{game}", ratings: {verdicts}')
    driver.quit()
    print(df.dtypes)
    print(df.head())
    df.to_sql('Video_Games', conn, if_exists='replace', index=False)

def clean_name(name):
    if pd.isna(name):
        return ''
    # Lowercase, remove punctuation, and extra spaces
    return re.sub(r'[^a-z0-9]', '', name.lower())

def rating_counter(df):
    cols = ['IGN_rating', 'Gamespot_rating', 'Game_Rant_rating', 'PC_Gamer_rating']
    df['rating_count'] = df[cols].notna().sum(axis=1)

def add_data_set_hugging(df, hugging_face_url = 'https://huggingface.co/datasets/ItzRoBeerT/video-games-sales?library=pandas'):
    #Adds from url: https://huggingface.co/datasets/ItzRoBeerT/video-games-sales?library=pandas ,
    new_df = pd.read_parquet(hugging_face_url)
    new_df = new_df.rename(columns={'Name': 'name'})
    new_df = new_df.drop_duplicates()
    new_df = new_df[['name']]
    df_all_names = pd.merge(df, new_df, on='name', how='outer')
    df_all_names['Clean_names'] = df_all_names['name'].apply(lambda x: clean_name(x))
    df_all_names = df_all_names.drop_duplicates(subset='Clean_names')
    df_all_names = df_all_names.drop(columns=['Clean_names'])
    return df_all_names

def make_avg_score(df):
    cols = ['IGN_rating', 'Gamespot_rating', 'Game_Rant_rating', 'PC_Gamer_rating']
    df_ratings = df[cols].apply(pd.to_numeric, errors='coerce')  # Convert strings to numbers or NaN

    df['Average_Score'] = round(df_ratings.mean(axis=1),2)  # Automatically ignores NaNs

def sum_text(limit):
    conn = sqlite3.connect('Video_Games.db')
    df = pd.read_sql("SELECT * FROM Video_Games", conn)
    i = 0
    for index, row in df.iterrows():
        if i > limit:
            break
        elif i != 0 and i % 8 == 0: #Avoids first save and auto-saves when completes 50 rows
            try:
                df.to_sql('Video_Games', conn, if_exists='replace', index=False)
            except Exception as e:
                print("Error saving to SQL:", e)
            print('\n----------------------------------------\nAuto-Saving after 10 rows\n----------------------------------------')
        print(f'Game number {index + 1}: {row["name"]}')
        sites = ['IGN', 'Gamespot', 'Game_Rant','PC_Gamer']
        final_text = ''
        if row['Verdict_Sum'] is not None:
            continue
        for site in sites:
            txt = row[site + '_text']
            if txt is not None and len(txt)>9:
                final_text += txt
        print(f'Raw verdict: {final_text}')
        if len(final_text)<20:
            continue
        summed_txt = sum(final_text)
        i+=1
        print(f'New verdict: {summed_txt} type: {type(summed_txt)}')
        df.at[index,'Verdict_Sum']= summed_txt

conn = sqlite3.connect('Video_Games.db')
df = pd.read_sql("SELECT * FROM Video_Games", conn)
tree = TitleTree("*",df["name"])


if not os.path.exists('Video_Games.db'):
    create()
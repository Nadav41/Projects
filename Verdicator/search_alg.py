from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

def get_pcgamer(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    score_tag = soup.find('span', class_='score score-long')
    score = int(score_tag.text.strip())
    verdict_txt = soup.find('p', class_='game-verdict')
    if verdict_txt:
        verdict_txt = verdict_txt.text.strip()
    if score_tag:
        return int(score/10) if float(score/10).is_integer() else float(score/10) , verdict_txt if verdict_txt else '-'
    else:
        return 'Score not found', '-'

def get_gamerant(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    score_tag = soup.find('div', class_='rate-number')
    if score_tag:
        try:
            score_tag = score_tag.text.strip()[:score_tag.text.strip().index('/')]
            score_tag = float(score_tag)
            return int(score_tag) if score_tag.is_integer() else score_tag, '-' #Impossible to catch verdict text.
        except ValueError:
            return score_tag.text.strip()
    else:
        return 'Score not found', '-'

def get_gamespot(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    score_tag = soup.find('div', class_='review-ring-score__score')
    points = soup.select('ul.review-breakdown__list li')
    verdict_text = ''
    # Extract and clean text
    for point in points:
        text = point.get_text(strip=True)
        verdict_text += (text + '. ')

    if score_tag:
        score_tag = float(score_tag.text.strip())
        return int(score_tag) if score_tag.is_integer() else score_tag , verdict_text if verdict_text else '-'
    else:
        return 'Not Found', '-'

def get_ign(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    for i in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            score_tag = soup.select_one('span[data-cy="review-score-hexagon-content-wrapper"] figcaption')
            verdict_txt = soup.select_one('p[data-cy="article-verdict-paragraph"]')
            if verdict_txt:
                verdict_txt = verdict_txt.text.strip()
            if score_tag:
                score = score_tag.text.strip()
                if score == 'NR':
                    return 'Not Found', None
                score = float(score)
                return int(score) if score.is_integer() else score , verdict_txt if verdict_txt else '-'
        except Exception as e:
            print(f'Attempt {i + 1} out of 3 \nFail: {e}')

    return 'Not Found', '-'

def catch_verdict(product, driver, site, site_func):
    global headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    query = f'{product} review site:{site}'
    driver.get(f"https://duckduckgo.com/?q={query.replace(' ', '+')}")
    time.sleep(3)
    # Print page title to confirm load
    print("Page Title:", driver.title)
    verdict_tup = ('Not Found', None, None, '-')
    # Try to extract results
    results = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="result-title-a"]')
    title = ''

    for res in results[:6]:  # just first result
        title = res.text
        lowered_title = title.lower().replace(':','').replace("'",'').replace(',','').replace('!','').replace('?','')
        if 'review' in lowered_title and 'reviews' not in lowered_title and lowered_title.startswith(product.lower().replace(':','').replace(',','').replace("'",'').replace('!','').replace('?','')) and abs((title.lower().index('review')) - len(product)) <= 5: #considers lengths of 'Review - IGN'
            if lowered_title[len(product) + 1].isdigit() or "i" in lowered_title[len(product) + 1:len(product) + 3]: #Avoids searching for predeccesors
                continue
            verdict = site_func(res.get_attribute("href"))
            # verdict = get_score(results[0].get_attribute("href"),driver)
            link = res.get_attribute("href")
            print("Title:", title)
            print("Link:", link)
            print(f'Verdict: {verdict}')
            verdict_tup = verdict[0], title, res.get_attribute("href"), verdict[1]
            break

    return verdict_tup

def all_verdicts(product, driver, sites):
    verdicts = {}
    verdicts = {'Gamespot': (None,None,None,None), 'IGN':(None,None,None,None),'Game_Rant':(None,None,None,None),'PC_Gamer':(None,None,None,None)}
    if 'IGN' in sites:
        verdicts['IGN'] = catch_verdict(product, driver, 'ign.com', get_ign)
    if 'Gamespot' in sites:
        verdicts['Gamespot'] = catch_verdict(product, driver, 'gamespot.com', get_gamespot)
    if 'Game_Rant' in sites:
        verdicts['Game_Rant'] = catch_verdict(product, driver, 'gamerant.com', get_gamerant)
    if 'PC_Gamer' in sites:
        verdicts['PC_Gamer'] = catch_verdict(product, driver, 'pcgamer.com', get_pcgamer)
    return verdicts
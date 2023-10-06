from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time, os, psycopg2
from datetime import datetime, date
import pandas as pd
from sqlalchemy import create_engine
from config import settings
from var import exe_path, rel_exe_path

statexcept_messgs = {}


def stats_loader(dataframe):
    #PostgreSQL database connection parameters
    connection_params = {
        "host": settings.database_hostname,
        "port": settings.database_port,
        "database": settings.database_name,
        "user": settings.database_user,
        "password": settings.database_password
    }

    #Connect to PostgreSQL
    connection = psycopg2.connect(**connection_params)

    # Create a SQLAlchemy engine
    engine = create_engine(f'postgresql+psycopg2://{settings.database_user}:{settings.database_password}@{settings.database_hostname}/{settings.database_name}')

    dataframe.to_sql('pre-game_stats', engine, if_exists='append', index=False)

    connection.commit()
    connection.close()
    print('Push to database successfully')


def stats_reader():
    #PostgreSQL database connection parameters
    connection_params = {
        "host": settings.database_hostname,
        "port": settings.database_port,
        "database": settings.database_name,
        "user": settings.database_user,
        "password": settings.database_password
    }

    #Connect to PostgreSQL
    connection = psycopg2.connect(**connection_params)
    cursor = connection.cursor()

    query = f"SELECT * FROM pre-game_stats"
    cursor.execute(query)

    result = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    cursor.close()
    connection.close()

    # Create a DataFrame from the fetched data
    from_db = pd.DataFrame(result, columns=column_names)
    return from_db


# Define a function to convert the date string to the desired format
def convert_date(date_str):
    try:
        # Parse the input date string and convert it to a datetime object
        date_obj = datetime.strptime(date_str, "%d/%m/%y")
        
        # Format the datetime object to the desired format "%d/%m/%Y"
        formatted_date = date_obj.strftime("%d/%m/%Y")
    except:
        current_date = date.today()

        # Convert the date to the desired format ("%d/%m/%Y")
        formatted_date = current_date.strftime("%d/%m/%Y")
    return formatted_date


def match_stat_extraction(league_list, today, tomorrow):
    leagues_dataset = {} #Created the empyt dictionary that will be used to concatenate all table from all leagues
    
    for key in list(league_list.keys()):
        league_url = league_list[key][2]
        league_counter = 0
        try:
            if league_url == '': 
                #Checks for empty league links and skips
                continue
            else:
                print(league_url)

                service = Service(executable_path=exe_path)
                #service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
                options = Options()
                ua = UserAgent()
                userAgent = ua.random
                options.add_argument(f'user-agent={userAgent}')
                #options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                options.add_argument('--blink-settings=imagesEnabled=false')
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-gpu")
                options.add_argument("--incognito")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-dev-shm-usage")

                driver = webdriver.Chrome(service=service,options=options)

                driver.get(league_url)
                #current_url = driver.current_url
                #print(current_url)
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@class='sc-fqkvVR clkedU']/div/a")))
                driver.execute_script("window.stop();")
                matches =driver.find_elements(By.XPATH,"//div[@class='sc-fqkvVR clkedU']/div/a")
                #print(len(matches))
                match = [con.get_attribute('innerText') for con in matches]
                time.sleep(2)
                #print(match)
                #print('Level 1: League level')
                match_links =driver.find_elements(By.XPATH,"//div[@class='sc-fqkvVR clkedU']/div/a[@href]")
                match_link = [con.get_attribute('href') for con in match_links] 
                #print(match_link)
                #time.sleep(2)
                # elements = driver.find_elements(By.CLASS_NAME, 'sc-aXZVg.dIaSSb')
                # print(len(elements))
                # elements[1].click()
                # matches2 =driver.find_elements(By.XPATH,"//div[@class='sc-fqkvVR clkedU']/div/a")
                # match2 = [con.get_attribute('innerText') for con in matches2]
                # print('Level 1: League level next page')
                # match_links2 =driver.find_elements(By.XPATH,"//div[@class='sc-fqkvVR clkedU']/div/a[@href]")
                # match_link2 = [con.get_attribute('href') for con in match_links2]
                driver.quit()
                # #print(match2)
                # match = match + match2
                # match_link = match_link + match_link2
                match  = [item.replace('\n', ',').split(',') for item in match]
                #print(match)
                data = [sublist[:4] for sublist in match]
                df = pd.DataFrame(data, columns=['Date', 'Time', 'Home_Team', 'Away_Team'])
                df['match_links'] = match_link
                df['Date'] = df['Date'].apply(convert_date)
                df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
                #print (df.Date)
                today_df = df[(df['Date'].dt.date == today) | (df['Date'].dt.date == tomorrow)]
                today_df = today_df.copy(deep=True)
                curr_league = [key for i in range(len(today_df['match_links']))]
                today_df['league'] = curr_league
                df = today_df.copy(deep=True)
                #print(df.Date)

                def matches_get(url):
                    service = Service(executable_path=exe_path)
                    #service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
                    options = Options()
                    ua = UserAgent()
                    userAgent = ua.random
                    options.add_argument(f'user-agent={userAgent}')
                    #options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                    options.add_argument('--blink-settings=imagesEnabled=false')
                    options.add_argument("--headless")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--incognito")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--window-size=1920,1080")

                    driver = webdriver.Chrome(service=service,options=options)

                    driver.get(url)
                    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@class='sc-jlZhew kgghii']/div/div")))
                    driver.execute_script("window.stop();")
                    team_links =driver.find_elements(By.XPATH,"//div[@class='sc-fqkvVR gWLOaC']/div/a[@href]")
                    team_link = [con.get_attribute('href') for con in team_links]
                    #print(team_link)
                    #print('Level 2: Match level')
                    team_titles = driver.find_elements(By.CLASS_NAME,"sc-fqkvVR.gWLOaC")
                    team_title = [con.get_attribute('innerText') for con in team_titles]
                    #print(team_title)

                    driver.quit()

                    def ind_team_stats(url):
                        service = Service(executable_path=exe_path)
                        #service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
                        options = Options()
                        ua = UserAgent()
                        userAgent = ua.random
                        options.add_argument(f'user-agent={userAgent}')
                        #options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                        options.add_argument('--blink-settings=imagesEnabled=false')
                        options.add_argument("--headless")
                        options.add_argument("--no-sandbox")
                        options.add_argument("--disable-gpu")
                        options.add_argument("--incognito")
                        options.add_argument("--disable-dev-shm-usage")
                        options.add_argument("--window-size=1920,1080")

                        driver = webdriver.Chrome(service=service,options=options)

                        driver.get(url)
                        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@class='sc-fqkvVR Ksgce']/div")))
                        driver.execute_script("window.stop();")
                        team_ages =driver.find_elements(By.CLASS_NAME,"sc-fqkvVR.sc-dcJsrY.jqdASS.ijIoLB")
                        team_age = [con.get_attribute('innerText') for con in team_ages]
                        team_age = team_age[1]
                        team_age = [team_age.replace('\n', ',')]
                        values = team_age[0].split(',')
                        df_team_age = pd.DataFrame([values])
                        #print(df_team_age)
                        for col in [1,3,5,6,7]:
                            if col in list(df_team_age.columns):
                                df_team_age =df_team_age.drop([col], axis=1)
                        df_team_age.rename(columns = {0:'Total Players', 2:'Average player age',
                                                    4:'Foreign players'}, inplace = True)

                        #print('Level 3: Individual matches level')
                        team_summarys =driver.find_elements(By.CLASS_NAME,"sc-fqkvVR.Ksgce")
                        team_summary = [con.get_attribute('innerText') for con in team_summarys]
                        driver.quit()
                        df_team_summary = pd.DataFrame()
                        # Loop through the list and split each element by '\n'
                        for item in team_summary:
                            values = item.split('\n')
                            headers = values[::2]
                            values = values[1::2]
                            # Create a temporary DataFrame from the current item
                            temp_df = pd.DataFrame([values], columns=headers)
                            # Append the temporary DataFrame to the main DataFrame
                            df_team_summary = pd.concat([df_team_summary, temp_df], axis=1)
                        df_team_summary = df_team_summary.transpose()
                        df_team_summary.index.name = 'Metric'
                        df_team_summary.rename(columns = {0:'Values'}, inplace = True)
                        df_team_summary = df_team_summary.transpose()

                        #print(df_team_age)
                        return df_team_summary

                    home_url = team_link[0]
                    away_url = team_link[1]

                    # Fetch data for the home team
                    home_df = ind_team_stats(home_url)
                    home_df.reset_index(drop=True, inplace=True)
                    home_df.columns = ['Home_' + col for col in home_df.columns]

                    away_df = ind_team_stats(away_url)
                    away_df.reset_index(drop=True, inplace=True)
                    away_df.columns = ['Away_' + col for col in away_df.columns]

                    # Concatenate the home and away DataFrames horizontally
                    teams_df = pd.concat([home_df, away_df], axis=1)
                    teams_df.columns =teams_df.columns.str.replace(' ', '_')
                    return teams_df

                combined_df = []
                index_list = list(df.index)
                limit = df.shape[0]
                df_2 = df.copy(deep=True)
                for i in range(limit):
                    try:
                        url = list(df['match_links'])[i]
                        data_df = matches_get(url)
                        combined_df.append(data_df)
                    except Exception as e:
                        statexcept_messgs[str(key)+f": {league_counter} (Match Pre-game Stats Extraction)"] = f"{type(e).__name__}: {str(e).split('Stacktrace:')[0]}" #Catches and Records Error
                        league_counter += 1
                        df_2.drop(index_list[i], axis=0, inplace=True)

                combined = pd.concat(combined_df, join='outer', ignore_index=True)
                move_to_database = pd.concat([df_2.reset_index(drop=True), combined], axis=1, ignore_index=False)
                # Drop duplicate columns
                move_to_database = move_to_database.loc[:, ~move_to_database.columns.duplicated(keep='first')]

                #Loads the extracted league to the database
                for i in range(2): #Tries twice to load data in case of any unforeseen connection issue
                    try:
                        stats_loader(move_to_database) #If try is successful, breaks the loop
                        print("All daily matches of {} have been loaded!".format(key))
                        break
                    except Exception as e:
                        statexcept_messgs[str(key)+f": {league_counter} (Database Loading)"] = f"{type(e).__name__}: {str(e).split('Stacktrace:')[0]}" #Catches and Records Error
                        league_counter += 1
                        print("All daily matches of {} couldn't be loaded!".format(key))
                        if i < 1: #If try isn't successful but it's the first time, then it tries again
                            continue
                        else: #If try isn't successful the second time, it adds the dataframe to the dictionary to try later.
                            leagues_dataset[key] = move_to_database
        except Exception as e:
            statexcept_messgs[str(key)+f": {league_counter} (Full League Extraction)"] = f"{type(e).__name__}: {str(e).split('Stacktrace:')[0]}" #Catches and Records Error
            league_counter += 1
            try:
                driver.quit()
                print("Daily matches of {} couldn't be extracted!".format(key))
                continue
            except:
                print("Daily matches of {} couldn't be extracted!".format(key))
                continue
                
    #All the dataframe of the daily matches for all the leagues extracted are concatenated vertically
    list_of_keys = list(leagues_dataset.keys())
    if len(list_of_keys) > 0:
        for i in range(len(list_of_keys)):
            if i == 0:
                key = list_of_keys[i]
                final_dataset = leagues_dataset[key].copy(deep=True)
            else:
                key = list_of_keys[i]
                final_dataset = pd.concat([final_dataset, leagues_dataset[key]], join='outer', axis=0)

        #Retries to load all the previous data that couldn't be loaded during extraction into the database
        for i in range(2): #Tries twice to load data in case of any unforeseen connection issue
            try:
                stats_loader(final_dataset) #If try is successful, breaks the loop
                break
            except Exception as e:
                statexcept_messgs[f"(Final Database Loading): {i}"] = f"{type(e).__name__}: {str(e).split('Stacktrace:')[0]}" #Catches and Records Error
                league_counter += 1
                continue #If try isn't successful but it's the first time, then it tries again

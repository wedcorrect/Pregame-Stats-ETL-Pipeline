from datetime import date, timedelta
from pregame_stat_utilities import match_stat_extraction, statexcept_messgs
from var import testleagues_list, leagues_list
from config import settings
import smtplib, os, schedule, time
from email.message import EmailMessage

def main():
    '''Main function the runs the entire app workflow, from extraction of the individual team's
    match history to the referee's history and loads the data into the database.
    
    It also records the error log and sends it to the dev's/client's email.'''
    yesterday = date.today() + timedelta(days=-1)
    today = date.today()
    tomorrow = date.today() + timedelta(days=1)
    print(yesterday, today, tomorrow)
    if (today.day % 2) == 0:
        match_stat_extraction(leagues_list, today, yesterday)

        #Concatenating error logs to send to email.
        email = f"Error Logs for {today} and {tomorrow} Stat Extraction.\n\n"
        email = email + f"Teams' Pre-Game Statistics\n"
        for item in list(statexcept_messgs.keys()):
            if item == list(statexcept_messgs.keys())[-1]:
                email = email + f"{item}: {statexcept_messgs[item]}\n\n"
            else:
                email = email + f"{item}: {statexcept_messgs[item]}\n"
        
        #Sends error message to Email for recording or review
        msg = EmailMessage()
        msg['Subject'] = f"Error Logs for {today} and {tomorrow} Stat Extraction."
        msg['From'] = settings.email_address
        msg['To'] = "michaeligbomezie@gmail.com"
        msg.set_content(email)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(settings.email_address, settings.email_password)
            smtp.send_message(msg)


if __name__ == '__main__':
    # Schedule the task to run daily at a specific time (e.g., 10:30 AM)
    schedule.every().day.at("01:30").do(main)

    while True:
        # Run the pending scheduled tasks
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 second (adjust as needed)
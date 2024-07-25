from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from datetime import date
import smtplib, ssl
import re
import random

#Credentials and URLs
EMAIL_SENDER = "your email here"
EMAIL_PASSWORD = "your email code here"
EMAIL_RECEIVER = 'receiving email here'
LOGIN_EMAIL = "visa login mail"
LOGIN_PASSWORD = "visa login password"
CHROMEDRIVER_PATH = 'chrome_driver path'

def send_alert_mail(city, date):
    port = 465
    smtp_server = "smtp.gmail.com"

    subject = "US-VISA APPOINTMENT ALERT"
    body = f"{city}: {date}"
    message = f"Subject: {subject}\n\n{body}"

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, message)

def login(driver, wait):
    driver.get('https://ais.usvisa-info.com/en-tr/niv/users/sign_in')
    
    wait.until(EC.presence_of_element_located((By.ID, 'user_email'))).send_keys(LOGIN_EMAIL)
    wait.until(EC.presence_of_element_located((By.ID, 'user_password'))).send_keys(LOGIN_PASSWORD)

    check_box = wait.until(EC.presence_of_element_located((By.ID, 'policy_confirmed')))
    driver.execute_script("arguments[0].click();", check_box)

    sign_in = wait.until(EC.presence_of_element_located((By.NAME, 'commit')))
    driver.execute_script("arguments[0].click();", sign_in)

def get_current_appointment_info(driver, wait):
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/div[3]/div[1]/div/div[1]/div[1]/div[2]/ul/li/a')))
    current_appointment_info = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.consular-appt")))

    date_pattern = re.compile(r'(\d{1,2})\s([A-Za-z]+),\s(\d{4})')
    match = date_pattern.search(current_appointment_info.text)

    current_day = int(match.group(1))
    current_month = time.strptime(match.group(2), "%B").tm_mon
    current_year = int(match.group(3))

    current_date = date(current_year, current_month, current_day)
    return current_date

def check_appointments(driver, wait, current_date):

    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="appointments_consulate_appointment_facility_id"]/option[1]'))).click()

    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="appointments_consulate_appointment_facility_id"]/option[3]'))).click()

    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#appointments_consulate_appointment_date'))).click()

    while True:
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td[data-handler="selectDay"][data-event="click"]')))
            element.click()

            istanbul_month = int(element.get_attribute("data-month")) + 1
            istanbul_year = int(element.get_attribute("data-year"))
            istanbul_day = int(element.text)

            istanbul_date = date(istanbul_year, istanbul_month, istanbul_day)

            if current_date < istanbul_date:
                print("NO CLOSER APPOINTMENTS IN ISTANBUL.")
            else:
                print(f"ISTANBUL Closest appointment day: {istanbul_day}/{istanbul_month}/{istanbul_year}")

                time.sleep(5)
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="appointments_consulate_appointment_time"]/option[2]'))).click()
                wait.until(EC.presence_of_element_located((By.NAME, 'commit'))).click()
                wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div/div/a[2]'))).click()

                send_alert_mail("ISTANBUL", istanbul_date)
            break
        except:
            year = driver.find_element(By.CLASS_NAME, "ui-datepicker-year")
            if int(year.text) > current_date.year:
                print("ENOUGH FOR ISTANBUL.")
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="header"]/nav/div/div/div[2]/div[1]/ul/li[2]'))).click()
                break
            forward_button = WebDriverWait(driver, 0.1).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ui-datepicker-div"]/div[2]/div/a')))
            forward_button.click()

def run_program():
    options = Options()
    #options.add_argument('--headless')  # Uncomment to run in headless mode
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    is_error = False

    wait = WebDriverWait(driver, 2)
    WAIT_INTERVAL = random.randint(480, 3600) #Wait between 8 minutes and 1 hour
    CHECK_LIMIT = random.randint(10,30) #Check for a random time between 10 and 30
    check_count = 0

    try:
        login(driver, wait)
        current_date = get_current_appointment_info(driver, wait)
        print(f"Current appointment day: {current_date.day}/{current_date.month}/{current_date.year}")

        continue_button = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/div[3]/div[1]/div/div[1]/div[1]/div[2]/ul/li/a')))
        driver.execute_script("arguments[0].click();", continue_button)

        appoin_button = wait.until(EC.presence_of_element_located((By.XPATH, '//*[text()="Reschedule Appointment"]')))
        driver.execute_script("arguments[0].click();", appoin_button)

        wait.until(EC.presence_of_element_located((By.ID, 'appointments_consulate_appointment_date')))

        while check_count < CHECK_LIMIT:
            check_appointments(driver, wait, current_date)
            check_count += 1
            time.sleep(5)
        
         ##Actions Menu
        actions_menu = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="header"]/nav/div/div/div[2]/div[1]/ul/li[3]/a'))).click()
        #Log-out
        log_out = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="header"]/nav/div/div/div[2]/div[1]/ul/li[3]/ul/li[4]/a')))
        driver.execute_script("arguments[0].click();", log_out)
        time.sleep(5)
    except:
        is_error = True
    finally:
        driver.quit()
        if is_error:
            run_program()
        else:
            print(f"Waiting for {WAIT_INTERVAL} seconds before restarting...")
            time.sleep(WAIT_INTERVAL)
            run_program()

if __name__ == "__main__":
    run_program()
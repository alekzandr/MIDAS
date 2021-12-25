import schedule
import time

def job_1():
    print("test")

schedule.every().sunday.at("22:04").do(job_1)

while True:
    schedule.run_pending()
    time.sleep(1)


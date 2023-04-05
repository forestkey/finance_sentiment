import time
from scrape_xueqiu_home import ScrapeXueqiuHome
import schedule

def scrape_xueqiu():
    scrape = ScrapeXueqiuHome()
    outlines_save_path = scrape.scrape(scroll_times=20, details=False)
    print('Scraped xueqiu output:', outlines_save_path)

end_time = '2023-04-06 8:00'
job_scrape_0 = schedule.every().hour.at(":00").until(end_time).do(scrape_xueqiu)
job_scrape_1 = schedule.every().hour.at(":10").until(end_time).do(scrape_xueqiu)
job_scrape_2 = schedule.every().hour.at(":20").until(end_time).do(scrape_xueqiu)
job_scrape_3 = schedule.every().hour.at(":30").until(end_time).do(scrape_xueqiu)
job_scrape_4 = schedule.every().hour.at(":40").until(end_time).do(scrape_xueqiu)
job_scrape_5 = schedule.every().hour.at(":50").until(end_time).do(scrape_xueqiu)
while schedule.jobs:
    schedule.run_pending()
    time.sleep(1)

print('Done')


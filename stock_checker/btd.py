import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from utils.notify import SendEmail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock-checker")

PERCENT_CHANGE_THRESHOLD = 5.0
URL = "https://www.marketwatch.com/investing/fund/spy/download-data"


def buy_the_dip():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "lxml")
    current_price = float(soup.find("bg-quote", {"field": "Last"}).text)

    table = soup.find("table", {"aria-label": "Historical Quotes data table"})
    historical_price_rows = table.find_all("tr", {"class": "table__row"})
    historical_prices = [float(row.find_all("td")[3].text.replace("$", "")) for row in historical_price_rows[1:]]
    highest_price = max(historical_prices)

    percent_change_from_high = round(((highest_price - current_price) / current_price) * 100, 2)
    logger.info(percent_change_from_high)
    if percent_change_from_high >= PERCENT_CHANGE_THRESHOLD:
        title = f"S&P500 {PERCENT_CHANGE_THRESHOLD}% DROP WARNING - {datetime.utcnow().strftime('%m-%d-%Y')}"
        message = f"S&P500 is currently -{percent_change_from_high}% below the 30-day high: {URL}"
        logger.info(message)
        email = SendEmail()
        email.dispatch_simple_email(f"<h1>{message}</h1>", title=title)


if __name__ == "__main__":
    buy_the_dip()

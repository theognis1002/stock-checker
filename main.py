import concurrent.futures
import json
import logging
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils.notify import dispatch_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock-checker")


def get_sp500_stocks():
    """grab all current stocks from S&P500 from wikipedia"""
    logger.info("Collecting S&P500 stock tickers...")

    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table", {"id": "constituents"})
    stocks = []
    for row in table.findAll("tr"):
        cells = row.findAll("td")
        if len(cells):
            stock = {"stock": cells[0].text.replace("\n", ""), "name": cells[1].text}
            stocks.append(stock)
    return stocks


def get_gurufocus_stats(stock_data):
    """grab stock's return on capital, earnings yield, and misc. figures"""
    logger.info(f"    [+] ${stock_data['stock']}")

    res = requests.get(f"https://www.gurufocus.com/stock/{stock_data['stock']}/summary")
    soup = BeautifulSoup(res.text, "lxml")

    # return on capital
    roc_data_node = soup.find("td", text=re.compile("ROC (Joel Greenblatt)"))
    if roc_data_node:
        return_on_capital = float(roc_data_node.findNext("td").text.strip())
        stock_data["return_on_capital"] = return_on_capital

    # earnings yield
    ey_data_node = soup.find("td", text=re.compile("Earnings Yield"))
    if ey_data_node:
        earnings_yield = float(ey_data_node.findNext("td").text.strip())
        stock_data["earnings_yield"] = earnings_yield

    # p/e ratio
    pe_data_node = soup.find("td", text=re.compile("PE Ratio"))
    if pe_data_node:
        pe_ratio = float(pe_data_node.findNext("td").text.strip())
        stock_data["pe_ratio"] = pe_ratio
    return stock_data


def main():
    """script entrypoint"""
    start_time = time.time()
    stocks = get_sp500_stocks()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:

        futures = []
        for stock in stocks:
            futures.append(executor.submit(get_gurufocus_stats, stock))

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    stock_results = sorted(
        results, key=lambda k: k.get("earnings_yield", 9999), reverse=True
    )

    csv_filename = f"{datetime.utcnow().strftime('%m-%d-%Y')}.csv"
    # with open(f"sp500_{datetime.utcnow().strftime('%m-%d-%Y')}.json", "w") as outfile:
    #     json.dump(stock_results, outfile)

    df = pd.DataFrame.from_records(stock_results)
    df.to_csv(csv_filename)

    logging.info(df.head())
    dispatch_email(df, csv_filename)

    end_time = time.time()
    logging.info(f"Took {round(end_time-start_time, 3)} secs to execute.")


if __name__ == "__main__":
    main()

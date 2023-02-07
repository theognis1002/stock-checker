from __future__ import annotations

import concurrent.futures
import logging
import os
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from decouple import config

from utils.notify import SendEmail

from .interest_rates import get_hurdle_rate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock-checker")
MAX_EARNINGS_YIELD = config("MAX_EARNINGS_YIELD", default=10, cast=int)


def get_sp500_stocks() -> list[str]:
    """Retrieve all current stocks from S&P500 from wikipedia

    Returns:
        list[str]: current S&P500 stock tickers
    """
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


def get_gurufocus_stats(stock_data: dict) -> dict:
    """Retrieve stock's return on capital, earnings yield, and misc. figures

    Args:
        stock_data (dict): dict of stock data

    Returns:
        dict: stock data with additional figures

    """
    res = requests.get(f"https://www.gurufocus.com/stock/{stock_data['stock']}/summary")
    soup = BeautifulSoup(res.text, "lxml")

    # return on capital
    roc_data_node = soup.find(lambda tag: tag.name == "td" and "ROC (Joel Greenblatt)" in tag.text)
    if roc_data_node:
        return_on_capital = float(roc_data_node.findNext("td").text.strip())
        stock_data["return_on_capital"] = return_on_capital

    # earnings yield
    ey_data_node = soup.find("td", text=re.compile("Earnings Yield"))
    if ey_data_node:
        earnings_yield = float(ey_data_node.findNext("td").text.strip())
        stock_data["earnings_yield"] = earnings_yield

    # debt/equity
    de_data_node = soup.find("td", text=re.compile("Debt-to-Equity"))
    if de_data_node:
        try:
            debt_to_equity = float(de_data_node.findNext("td").text.strip())
        except ValueError:
            debt_to_equity = None
        stock_data["debt_to_equity"] = debt_to_equity

    # p/e ratio
    pe_data_node = soup.find("td", text=re.compile("PE Ratio"))
    if pe_data_node:
        pe_ratio = float(pe_data_node.findNext("td").text.strip())
        stock_data["pe_ratio"] = pe_ratio

    logger.info(
        f"    [+] ${stock_data['stock']} -- P/E: {stock_data.get('pe_ratio')} - EY: {stock_data.get('earnings_yield')} - ROC: {stock_data.get('return_on_capital')}"
    )

    return stock_data


def sp500() -> int:
    """Stock Checker Entrypoint function

    Returns:
        int: 0 indicating successful exit.
    """
    start_time = time.time()
    stocks = get_sp500_stocks()
    hurdle_rate = get_hurdle_rate()

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for stock in stocks:
            futures.append(executor.submit(get_gurufocus_stats, stock))

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    stock_results = sorted(results, key=lambda k: k.get("earnings_yield", 9999), reverse=True)

    # convert unfiltered dataframe to csv
    csv_filename = f"{datetime.utcnow().strftime('%m-%d-%Y')}.csv"
    df = pd.DataFrame.from_records(stock_results)
    csv_df = df.copy()
    csv_df.to_csv(csv_filename)

    # filter values
    df = df.dropna(subset=["return_on_capital"])
    df = df.dropna(subset=["pe_ratio"])
    df = df.loc[(df["earnings_yield"] >= hurdle_rate) & (df["earnings_yield"] <= MAX_EARNINGS_YIELD)]

    logging.info(df.head())

    # send email notification
    email = SendEmail()
    email.dispatch_email_w_dataframe(df, csv_filename)

    # remove csv
    os.remove(csv_filename)

    end_time = time.time()
    logging.info(f"Took {round(end_time-start_time, 3)} secs to execute.")

    return 0

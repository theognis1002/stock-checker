## S&P500 Stock Checker

Simple Python script that crawls financial pages for current fundamental ratios and figures. Warren Buffett, through his writings and over the years, has mentioned the following ratios as important:

1. Return on Tangible Capital
    - Operating Income / (Net Working Capital + Net Fixed Assets)
1. Earnings Yield
    - EBIT/EV (Earnings before interest and taxes / Enterprise Value)

_Note: See TODO list for future additional figures._

The script gets the current S&P500 stocks and collects the above figures for each company. The data is then exported as a CSV file and emailed to the recipient.

---

### TODO

-   [x] Return on Tangible Capital
-   [x] Earnings Yield
-   [x] P/E (financials stocks)
-   [ ] Share price
-   [ ] Return on Equity
-   [ ] Debt / Equity
-   [ ] 10YR Interest Rate
-   [ ] Estimated Valuation

---

### Technologies Used

1. Python3.8
1. pandas
1. smtp
1. crontab

---

### Setup

1. Create `.env` using `.env.sample` as reference
    - Email app credentials needed (ie; Gmail)
1. `virtualenv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`

---

### Run

1. `python main.py`

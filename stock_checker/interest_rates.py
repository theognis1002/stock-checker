import requests
from bs4 import BeautifulSoup


def get_10yr_treasury_rate():
    res = requests.get("https://www.gurufocus.com/yield_curve.php")
    soup = BeautifulSoup(res.text, "lxml")
    treasury_rate = float(soup.find("a", {"title": "10-year yield"}).find_parent("td").find_next("td").text.replace("%", "").strip())
    return treasury_rate


def get_hurdle_rate():
    treasury_rate = get_10yr_treasury_rate()
    return max(treasury_rate * 1.5, 4.0)

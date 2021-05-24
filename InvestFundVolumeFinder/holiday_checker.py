import holidays
from datetime import datetime, timedelta


def get_latest_market_open_date():
    _today = datetime.today()
    today_date = _today.date()
    today_week_day = today_date.weekday()

    # if the time turns midnight, today's date should be one day less before 9 am for calculation below
    # weekends should be considered
    if _today.hour < 15.5 and today_week_day < 5:
        today_date = today_date - timedelta(days=1)
    else:
        today_date = today_date

    if today_week_day == 5:
        today_date = today_date - timedelta(days=1)
    elif today_week_day == 6:
        today_date = today_date - timedelta(days=2)

    korean_holidays = holidays.KR()
    while True:
        if today_date in korean_holidays:
            today_date = today_date - timedelta(days=1)
        # korean stock market closes at the end of a year
        elif today_date.month == 12 and today_date.day == 31:
            today_date = today_date - timedelta(days=1)
        else:
            break

    return today_date


def is_market_open():
    _today = datetime.today()
    today_date = _today.date()
    today_week_day = today_date.weekday()

    if 9 <= _today.hour < 15.5 and today_week_day < 5:
        korean_holidays = holidays.KR()
        if today_date in korean_holidays or (today_date.month == 12 and today_date.day == 31):
            return False
        return True
    return False

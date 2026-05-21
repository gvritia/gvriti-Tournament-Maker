from datetime import datetime, time, timedelta


def start_of_day(value: datetime) -> datetime:
    return datetime.combine(value.date(), time.min, tzinfo=value.tzinfo)


def start_of_week(value: datetime) -> datetime:
    day_start = start_of_day(value)
    return day_start - timedelta(days=day_start.weekday())

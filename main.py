import itertools
from io import TextIOWrapper
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import re
from datetime import datetime, timedelta
import pytz

BASE_URL = "https://www.thebostoncalendar.com"
time_format = "%Y-%m-%d %I:%M%p EST"
est = pytz.timezone("US/Eastern")

write_lock = threading.Lock()

# set up by date
today = datetime.today().date()
days_until_sunday = (6 - today.weekday()) % 7 or 7

## setup dict by day
events_by_day = {}
for i in range(days_until_sunday + 1):
    events_by_day[today + timedelta(days=i)] = []


def addEventTimePeriod(start_time, end_time, event_description):
    start_day, end_day = start_time.date(), end_time.date()
    while start_day <= end_day:
        events_by_day[start_day].append(event_description)
        start_day += timedelta(days=1)


def getEventsLists(n: int):
    content = requests.get(BASE_URL).text
    soup = BeautifulSoup(content, "lxml")
    events = soup.find(id="events")  # ul of events
    n_events = events.find_all(class_="event")[:n]
    event_list_links = []
    for event in n_events:
        link = str(event.find("a").get("href"))
        event_list_links.append(link)
    return event_list_links


def getDescriptionText(soup: BeautifulSoup) -> str:
    text = soup.find(id="event_description")
    return text.getText() if text is not None else ""


def getTimePeriod(soup: BeautifulSoup) -> tuple[datetime, datetime]:
    time_frame = soup.find_all(id="startdate")
    start_time = time_frame[0].get("content")
    end_time = time_frame[1].get("content")

    start_time = est.localize(datetime.strptime(start_time, time_format))
    end_time = est.localize(datetime.strptime(end_time, time_format))

    return (start_time, end_time)


def addEventPageToFile(link: str):
    # get soup
    content = requests.get(link).text
    soup = BeautifulSoup(content, "lxml")
    full_description = getDescriptionText(soup)
    event_name = soup.find("h1").text.strip()

    shortened_description = re.match(
        r"^[^.!?].{40,}?[.!?]", full_description, re.IGNORECASE
    )
    description = (
        shortened_description.group(0).strip()
        if shortened_description
        else full_description
    )

    event = (
        "### "
        + event_name
        + "\n\n"
        + description
        + "  \n"
        + '<a href="'
        + link
        + '" target="_blank">info link</a>\n\n'
    )

    addEventTimePeriod(*getTimePeriod(soup), event)


def addEventPage(url: str):
    content = requests.get(url).text

    soup = BeautifulSoup(content, "lxml")

    links = soup.find(id="event_description").find_all("a")
    links = [
        i.get("href")
        for i in links
        if re.search(r".*thebostoncalendar.*", i.get("href"))
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(
            addEventPageToFile,
            links,
        )


if __name__ == "__main__":
    filename = "README"
    by_day_filename = "events_by_day"

    event_list_urls = getEventsLists(2)
    for event_url in event_list_urls:
        addEventPage(BASE_URL + event_url)
    with open(filename + ".md", "w") as file:
        for day, events in events_by_day.items():
            file.write("# " + day.strftime("%A, %B %d, %Y") + "\n\n")
            for event in events:
                file.write(event)

import itertools
from io import TextIOWrapper
from bs4.element import Tag
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re

## todo: get dynamically from https://www.thebostoncalendar.com
url = "https://www.thebostoncalendar.com/events/80-free-things-to-do-in-boston-this-week-feb-18-23-2025"

BASE_URL = "https://www.thebostoncalendar.com"


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


def getDescriptionText(bitly_link: str) -> str:
    content = requests.get(bitly_link).text
    soup = BeautifulSoup(content, "lxml")
    text = soup.find(id="event_description")
    return text.getText() if text is not None else ""


def addToFile(item: Tag, file: TextIOWrapper):
    if re.match(r"[0-9]+\)*", item.text):
        text = item.text
        event_name = re.search(r"[0-9]+\)\s+(.+)\s+", text).group(1).strip()
        link = str(item.find("a").get("href"))
        match = re.match(r"^[^.!?]*[.!?]", getDescriptionText(link))
        description = match.group(0).strip() if match else ""

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
        file.write(event)


def addEvent(url: str, file: TextIOWrapper):
    content = requests.get(url).text
    soup = BeautifulSoup(content, "lxml")

    header = soup.find("h1").text.strip()

    items = soup.find(id="event_description")
    file.write("# " + header + "\n\n")

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(addToFile, items.findChildren(), itertools.repeat(file))


if __name__ == "__main__":
    filename = datetime.now().strftime("%m-%d-%Y")

    event_list_urls = getEventsLists(2)
    with open(filename + ".md", "w") as file:
        for event_url in event_list_urls:
            addEvent(BASE_URL + event_url, file)

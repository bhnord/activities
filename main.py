import itertools
from io import TextIOWrapper
from bs4.element import Tag
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re

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


def addNumberedEventToFile(item: Tag, file: TextIOWrapper, events_file: TextIOWrapper):
    if re.match(r"[0-9]+\)*", item.text):
        text = item.text
        event_name = re.search(r"[0-9]+\)\s+(.+)\s+", text).group(1).strip()
        link = str(item.find("a").get("href"))
        descriptionText = getDescriptionText(link)
        match = re.match(r"^[^.!?].{40,}?[.!?]", descriptionText, re.IGNORECASE)
        description = match.group(0).strip() if match else descriptionText

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
        raw_event = "### " + event_name + "\n\n" + description + "\n\n"

        file.write(event)
        events_file.write(raw_event)


def addEventToFile(item: str, file: TextIOWrapper, events_file: TextIOWrapper):
    soup = BeautifulSoup(item, "lxml")

    link = ""
    event_name = ""
    # when, where, description
    info = []

    title_seen = False
    for elem in soup.find_all("p"):
        # title
        if elem.find("a"):
            link = elem.find("a").get("href")
            # remove numebring if it's there
            event_name = re.sub(r"^\d+\)", "", elem.text).strip()
            title_seen = True
        # where, when, info
        elif title_seen:
            sub_title = elem.find("strong")
            if re.match(r"(where|when|info)", sub_title.text, re.IGNORECASE):
                sub_title.decompose()
                info.append(elem.text.strip())

    event = (
        "### "
        + event_name
        + " @ "
        + info[1]
        + "\n\n"
        + "##### "
        + info[0]
        + "\n\n"
        + info[2]
        + "  \n"
        + '<a href="'
        + link
        + '" target="_blank">info link</a>\n\n'
    )

    raw_event = (
        "### "
        + event_name
        + " @ "
        + info[1]
        + "\n\n"
        + "##### "
        + info[0]
        + "\n\n"
        + info[2]
        + "\n\n"
    )
    file.write(event)
    events_file.write(raw_event)


def addEventPage(url: str, file: TextIOWrapper, events_file: TextIOWrapper):
    content = requests.get(url).text

    soup = BeautifulSoup(content, "lxml")

    header = soup.find("h1").text.strip()

    items = soup.find(id="event_description")
    file.write(f"# {header}\n\n")

    # check which format the list is in
    text = soup.text
    regex = re.findall(r"[0-9]+\)\s+(.+?) bit\.ly", text)
    if regex and len(regex) > 5:
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(
                addNumberedEventToFile,
                items.find_all(),
                itertools.repeat(file),
                itertools.repeat(events_file),
            )
    else:
        events = re.findall(r"<p>.+?<a.+?Where.+?Info.+?</p>", content)
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(
                addEventToFile,
                events,
                itertools.repeat(file),
                itertools.repeat(events_file),
            )


if __name__ == "__main__":
    filename = "README"
    raw_events_filename = "events.md"

    event_list_urls = getEventsLists(2)
    with open(filename + ".md", "w") as file, open(
        raw_events_filename, "w"
    ) as events_file:
        file.write("scraped from: " + BASE_URL + "\n\n")
        for event_url in event_list_urls:
            addEventPage(BASE_URL + event_url, file, events_file)

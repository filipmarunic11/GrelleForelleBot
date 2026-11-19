
import requests
import asyncio
import re

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from telegram import Bot

URL = "https://www.grelleforelle.com/programm/"

BOT_TOKEN = "YOUR-TOKEN"
CHAT_ID = -1004499241915


def get_event_time(link):
    response = requests.get(
        link,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    lines = [
        line.strip()
        for line in soup.stripped_strings
        if line.strip()
    ]

    for i, line in enumerate(lines):
        if line.upper() == "DOORS":
            for next_line in lines[i + 1:i + 5]:
                match = re.search(r"\b\d{1,2}:\d{2}\b", next_line)

                if match:
                    return match.group()

    return "Not listed"


def scrape_events():
    print("Checking Grelle Forelle website...")

    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    seen_links = set()
    events = []

    for heading in soup.find_all(["h2", "h3", "h4"]):
        title = heading.get_text(" ", strip=True)

        if not title:
            continue

        current = heading

        for level in range(4):
            if current is None:
                break

            links = current.find_all("a", href=True)

            event_link = None

            for link in links:
                href = urljoin(URL, link["href"])

                if "/project/" in href:
                    event_link = href
                    break

            if event_link:
                if event_link not in seen_links:
                    seen_links.add(event_link)

                    date_match = re.match(
                        r"(\d{2})/(\d{2})",
                        title
                    )

                    date = (
                        f"{date_match.group(1)}."
                        f"{date_match.group(2)}."
                        if date_match
                        else "Not listed"
                    )

                    print("Getting time:", title)

                    try:
                        event_time = get_event_time(event_link)
                    except Exception as error:
                        print("Could not get time:", error)
                        event_time = "Not listed"

                    events.append({
                        "title": title,
                        "date": date,
                        "time": event_time,
                        "link": event_link
                    })

                break

            current = current.parent

    return events


async def send_events():
    bot = Bot(token=BOT_TOKEN)

    try:
        events = scrape_events()

        print(f"\nFound {len(events)} events.\n")

        for event in events:
            print(event["title"])
            print("Date:", event["date"])
            print("Time:", event["time"])
            print("Link:", event["link"])
            print()

        for event in events:
            message = (
                "GRELLE FORELLE EVENT\n\n"
                f"Title: {event['title']}\n"
                f"Date: {event['date']}\n"
                f"Time: {event['time']}\n"
                f"Link: {event['link']}"
            )

            await bot.send_message(
                chat_id=CHAT_ID,
                text=message
            )

            print("Sent:", event["title"])

            await asyncio.sleep(1)

        print("\nFinished!")

    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(send_events())

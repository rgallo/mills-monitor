import sys
import requests
import argparse
import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed


def output(webhookurl, message):
    # print(message)
    webhook = DiscordWebhook(url=webhookurl.split(";"), content=message)
    return webhook.execute()


def handleItem(name, itemlist, dataurl, funcs, pingrole=None):
    data = requests.get(dataurl).json()
    sorted_items = funcs["sorted_items"](data)
    count = funcs["count"](data)
    s = (f"__**{name}:**__\nCurrent {name}: {count}, "
         f"Progress to Next: {funcs['to_next'](data)*100.0:.2f}%\n"
         f"Top Renovations: ")
    for idx, item in enumerate(sorted_items, start=1):
        item_id, item_pct = funcs['id'](item), funcs['percent'](item)
        if idx == count + 1:
            s += "\n----------"
        if idx <= len(itemlist) and item_id not in itemlist:
            s += f"\n{idx}. {item_id} ({item_pct}%) :x:"
            if pingrole:
                s += f" <@&{pingrole}>"
        else:
            s += f"\n{idx}. {item_id} ({item_pct}%)"
            if item_id in itemlist:
                s += " :white_check_mark:" if idx <= count else " :pray:"
    return s


def handleRenos(renolist, pingrole=None):
    funcs = {
        "sorted_items": lambda data: sorted(data["stats"], key=lambda x: float(x["percent"]), reverse=True),
        "count": lambda data: data['progress']['total'],
        'to_next': lambda data: data['progress']['toNext'],
        "id": lambda item: item['id'],
        "percent": lambda item: item['percent']
    }
    return handleItem("Renovations", renolist, "https://www.blaseball.com/database/renovationProgress?id=ba794e99-4d6b-4e12-9450-6522745190f8", funcs, pingrole=pingrole)


def handleGifts(giftlist, pingrole=None):
    funcs = {
        "sorted_items": lambda data: sorted(data["teamWishLists"]["36569151-a2fb-43c1-9df7-2df512424c82"], key=lambda x: float(x["percent"]), reverse=True),
        "count": lambda data: data["teamProgress"]["36569151-a2fb-43c1-9df7-2df512424c82"]['total'],
        'to_next': lambda data: data["teamProgress"]["36569151-a2fb-43c1-9df7-2df512424c82"]['toNext'],
        "id": lambda item: item['bonus'],
        "percent": lambda item: f"{item['percent'] * 100.0:.2f}"
    }
    return handleItem("Gifts", giftlist, "https://www.blaseball.com/database/giftProgress", funcs, pingrole=pingrole)


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--webhook', help="webhook url")
    parser.add_argument('--gifts', help="top gift list comma separated")
    parser.add_argument('--renos', help="top reno list comma separated")
    parser.add_argument('--pingrole', help="id of role to ping")
    args = parser.parse_args()
    return args

def main():
    day = requests.get("https://www.blaseball.com/database/simulationData").json()["day"]
    if not 26 <= day <= 71:
        sys.exit()
    args = handle_args()
    outputstr = f"{'-'*30}**{datetime.datetime.now().strftime('%I:%m %p')}**{'-'*30}\n"
    outputstr += handleRenos(args.renos.split(","), args.pingrole)
    outputstr += "\n\n"
    outputstr += handleGifts(args.gifts.split(","), args.pingrole)
    output(args.webhook, outputstr)
    

if __name__ == "__main__":
    main()

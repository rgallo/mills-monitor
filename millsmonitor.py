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
    names = funcs["names"]([funcs['id'](item) for item in sorted_items])
    s = (f"__**{name}:**__\nCurrent {name}: {count}, "
         f"Progress to Next: {funcs['to_next'](data)*100.0:.2f}%\n"
         f"Top {name}: ")
    all_wanted = all(item in [funcs['id'](si) for si in sorted_items[:count]] for item in itemlist)
    for idx, item in enumerate(sorted_items, start=1):
        item_id, item_pct = funcs['id'](item), funcs['percent'](item)
        if idx == count + 1:
            s += "\n----------"
        if idx <= len(itemlist) and item_id not in itemlist:
            s += f"\n{idx}. {names[item_id]} ({item_pct}%) {':question:' if all_wanted else ':x:'}"
            if pingrole and not all_wanted:
                s += f" <@&{pingrole}>"
        else:
            s += f"\n{idx}. {names[item_id]} ({item_pct}%)"
            if item_id in itemlist:
                s += " :white_check_mark:" if idx <= count else " :pray:"
    return s


def handleRenos(teamid, renolist, pingrole=None):
    stadiums = requests.get("https://api.sibr.dev/chronicler/v1/stadiums").json()["data"]
    stadium_id = None
    for stadium in stadiums:
        if stadium["data"]["teamId"] == teamid:
            stadium_id = stadium["data"]["id"]
            break
    if not stadium_id:
        raise Exception("invalid team id")
    funcs = {
        "sorted_items": lambda data: sorted(data["stats"], key=lambda x: float(x["percent"]), reverse=True),
        "count": lambda data: data['progress']['total'],
        'to_next': lambda data: data['progress']['toNext'],
        "id": lambda item: item['id'],
        "percent": lambda item: item['percent'],
        "names": lambda ids: {attr["id"]: attr["title"] for attr in requests.get(f"https://www.blaseball.com/database/renovations?ids={','.join(ids)}").json()}
    }
    return handleItem("Renovations", renolist, f"https://www.blaseball.com/database/renovationProgress?id={stadium_id}", funcs, pingrole=pingrole)


def handleGifts(teamid, giftlist, pingrole=None):
    print(teamid)
    funcs = {
        "sorted_items": lambda data: sorted(data["teamWishLists"][teamid], key=lambda x: float(x["percent"]), reverse=True),
        "count": lambda data: data["teamProgress"][teamid]['total'],
        'to_next': lambda data: data["teamProgress"][teamid]['toNext'],
        "id": lambda item: item['bonus'],
        "percent": lambda item: f"{item['percent'] * 100.0:.2f}",
        "names": lambda ids: {gift["id"]: gift["title"] for gift in requests.get("https://www.blaseball.com/database/offseasonSetup").json()["gifts"]}
    }
    return handleItem("Gifts", giftlist, "https://www.blaseball.com/database/giftProgress", funcs, pingrole=pingrole)


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--webhook', help="webhook url")
    parser.add_argument('--gifts', help="top gift list comma separated")
    parser.add_argument('--renos', help="top reno list comma separated")
    parser.add_argument('--pingrole', help="id of role to ping")
    parser.add_argument('--pingday', help="when to start pinging", default="27")
    parser.add_argument('--minutemode', help="don't run on 5s", action='store_true')
    parser.add_argument('--teamid', help="team id", default="36569151-a2fb-43c1-9df7-2df512424c82")
    args = parser.parse_args()
    return args

def main():
    day = requests.get("https://www.blaseball.com/database/simulationData").json()["day"]
    if not 26 <= day <= 72:
        sys.exit()
    args = handle_args()
    if args.minutemode and not datetime.datetime.now().minute % 5 and day < 71:
        sys.exit()
    pingrole = args.pingrole if day > int(args.pingday) else None
    renos = args.renos.split(",") if args.renos else []
    gifts = args.gifts.split(",") if args.gifts else []
    sep = '-' * 20
    outputstr = f"{sep}**{datetime.datetime.now().strftime('%I:%M %p')}**{sep}\n"
    outputstr += handleRenos(args.teamid, renos, pingrole)
    outputstr += "\n\n"
    outputstr += handleGifts(args.teamid, gifts, pingrole)
    output(args.webhook, outputstr)
    

if __name__ == "__main__":
    main()

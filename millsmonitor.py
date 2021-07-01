import sys
import requests
import argparse
import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
import yaml


def output(webhookurl, message, discord=True):
    if discord:
        webhook = DiscordWebhook(url=webhookurl.split(";"), content=message)
        return webhook.execute()
    else:
        return print(message)
        


def handleItem(name, gooditems, baditems, dataurl, funcs, pingrole=None):
    data = requests.get(dataurl).json()
    sorted_items = funcs["sorted_items"](data)
    count = funcs["count"](data)
    names = funcs["names"]([funcs['id'](item) for item in sorted_items])
    s = (f"__**{name}:**__\nCurrent {name}: {count}, "
         f"Progress to Next: {funcs['to_next'](data)*100.0:.2f}%\n"
         f"Top {name}: ")
    for idx, item in enumerate(sorted_items, start=1):
        item_id, item_pct = funcs['id'](item), funcs['percent'](item)
        if idx == count + 1:
            s += "\n----------"
        s += f"\n{idx}. {names[item_id]} ({item_pct}%)"
        above_line = idx <= count
        is_good = item_id in gooditems
        is_bad = item_id in baditems
        if above_line:
            if is_good:
                s += " :white_check_mark:"
            elif is_bad:
                s += " :x:"
                if pingrole:
                    s += f" <@&{pingrole}>"
            elif gooditems or baditems:
                s += " :neutral_face:"
        else:
            if is_good:
                s += " :pray:"
            elif is_bad:
                s += " :no_entry_sign:"
    return s


def handleRenos(teamid, goodrenos, badrenos, pingrole=None):
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
    return handleItem("Renovations", goodrenos, badrenos, f"https://www.blaseball.com/database/renovationProgress?id={stadium_id}", funcs, pingrole=pingrole)


def handleGifts(teamid, goodgifts, badgifts, pingrole=None):
    funcs = {
        "sorted_items": lambda data: sorted(data["teamWishLists"][teamid], key=lambda x: float(x["percent"]), reverse=True),
        "count": lambda data: data["teamProgress"][teamid]['total'],
        'to_next': lambda data: data["teamProgress"][teamid]['toNext'],
        "id": lambda item: item['bonus'],
        "percent": lambda item: f"{item['percent'] * 100.0:.2f}",
        "names": lambda ids: {gift["id"]: gift["title"] for gift in requests.get("https://www.blaseball.com/database/offseasonSetup").json()["gifts"]}
    }
    return handleItem("Gifts", goodgifts, badgifts, "https://www.blaseball.com/database/giftProgress", funcs, pingrole=pingrole)


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--webhook', help="webhook url")
    parser.add_argument('--configurl', help="config url")
    parser.add_argument('--goodgifts', help="good gift list comma separated")
    parser.add_argument('--goodrenos', help="good reno list comma separated")
    parser.add_argument('--badgifts', help="bad gift list comma separated")
    parser.add_argument('--badrenos', help="bad reno list comma separated")
    parser.add_argument('--pingrole', help="id of role to ping")
    parser.add_argument('--pingday', help="when to start pinging", default="27")
    parser.add_argument('--minutemode', help="don't run on 5s", action='store_true')
    parser.add_argument('--teamid', help="team id", default="36569151-a2fb-43c1-9df7-2df512424c82")
    parser.add_argument('--print', help="print instead of discord", action='store_true')
    args = parser.parse_args()
    if args.configurl and (args.goodgifts or args.badgifts or args.goodrenos or args.badrenos):
        print("Do not specify both config url and good/bad lists")
    return args

def main():
    day = requests.get("https://www.blaseball.com/database/simulationData").json()["day"]
    if not 26 <= day <= 72:
        sys.exit()
    args = handle_args()
    if args.minutemode and not datetime.datetime.now().minute % 5 and day < 71:
        sys.exit()
    pingrole = args.pingrole if day > int(args.pingday) else None
    if args.configurl:
        config = yaml.load(requests.get(args.configurl).text, Loader=yaml.BaseLoader)
        goodrenos = config.get("goodrenos", [])
        goodgifts = config.get("goodgifts", [])
        badrenos = config.get("badrenos", [])
        badgifts = config.get("badgifts", [])
    else:
        goodrenos = args.goodrenos.split(",") if args.goodrenos else []
        goodgifts = args.goodgifts.split(",") if args.goodgifts else []
        badrenos = args.badrenos.split(",") if args.badrenos else []
        badgifts = args.badgifts.split(",") if args.badgifts else []
    sep = '-' * 20
    outputstr = f"{sep}**{datetime.datetime.now().strftime('%I:%M %p')}**{sep}\n"
    outputstr += handleRenos(args.teamid, goodrenos, badrenos, pingrole)
    outputstr += "\n\n"
    outputstr += handleGifts(args.teamid, goodgifts, badgifts, pingrole)
    output(args.webhook, outputstr, discord=not args.print)
    

if __name__ == "__main__":
    main()

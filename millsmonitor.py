import requests
import argparse
from discord_webhook import DiscordWebhook, DiscordEmbed


def output(webhookurl, message):
    # print(message)
    webhook = DiscordWebhook(url=webhookurl, content=message)
    return webhook.execute()


def handleRenos(webhookurl, renolist, pingrole=None):
    renodata = requests.get("https://www.blaseball.com/database/renovationProgress?id=ba794e99-4d6b-4e12-9450-6522745190f8").json()
    sorted_renos = sorted(renodata["stats"], key=lambda x: float(x["percent"]), reverse=True)
    renocount = renodata['progress']['total']
    s = (f"__**Renovations:**__\nCurrent Renos: {renocount}, "
         f"Progress to Next: {renodata['progress']['toNext']*100.0:.2f}%\n"
         f"Top Renovations: ")
    for idx, reno in enumerate(sorted_renos, start=1):
        if idx == renocount + 1:
            s += "\n----------"
        if idx <= len(renolist) and reno['id'] not in renolist:
            s += f"\n{idx}. ~~{reno['id']} ({reno['percent']}%)~~"
            if pingrole:
                s += f" <@&{pingrole}>"
        else:
            s += f"\n{idx}. {reno['id']} ({reno['percent']}%)"
    output(webhookurl, s)


def handleGifts(webhookurl, giftlist, pingrole=None):
    giftdata = requests.get("https://www.blaseball.com/database/giftProgress").json()
    millsprogress = giftdata["teamProgress"]["36569151-a2fb-43c1-9df7-2df512424c82"]
    giftcount = millsprogress['total']
    millswishlist = sorted(giftdata["teamWishLists"]["36569151-a2fb-43c1-9df7-2df512424c82"], key=lambda x: float(x["percent"]), reverse=True)
    s = (f"__**Gifts:**__\nCurrent Gifts: {giftcount}, "
         f"Progress to Next: {millsprogress['toNext']*100.0:.2f}%\n"
         f"Top Gifts: ")
    for idx, gift in enumerate(millswishlist, start=1):
        if idx == giftcount + 1:
            s += "\n----------"
        if idx <= len(giftlist) and gift['bonus'] not in giftlist:
            s += f"\n{idx}. ~~{gift['bonus']} ({gift['percent']*100.0:.2f}%)~~"
            if pingrole:
                s += f" <@&{pingrole}>"
        else:
            s += f"\n{idx}. {gift['bonus']} ({gift['percent']*100.0:.2f}%)"
    output(webhookurl, s)


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--webhook', help="webhook url")
    parser.add_argument('--gifts', help="top gift list comma separated")
    parser.add_argument('--renos', help="top reno list comma separated")
    parser.add_argument('--pingrole', help="id of role to ping")
    args = parser.parse_args()
    return args

def main():
    args = handle_args()
    handleRenos(args.webhook, args.renos.split(","), args.pingrole)
    handleGifts(args.webhook, args.gifts.split(","), args.pingrole)
    

if __name__ == "__main__":
    main()

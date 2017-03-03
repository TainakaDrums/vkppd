import vk
import os
import time
import threading
from etaprogress.progress import ProgressBar
import sys
from urllib import request
import logging
from concurrent.futures import ThreadPoolExecutor
from itertools import count


"""
1. Open url in browser.
https://oauth.vk.com/authorize?client_id=5033073&redirect_uri=https://oauth.vk.com/blank.html&scope=offline,messages&response_type=token&v=5.62
2. Allow acsess
3. Сopy access_token value
4. Paste it to TOKEN variable
"""


TOKEN=""


def download_pics(url, dirname, bar):

    filename=url.split("/")[-1]
    path = os.path.join(dirname, filename)

    if not os.path.exists(path) :

        try:
            res=request.urlopen(url)
            if res.getcode() != 200:
                return

            pic=res.read()
            with open(path, "wb") as f:
                f.write(pic)
        except Exception as e:
            logger.error("{0}.  URL IS {1}".format(e, url))

    bar.numerator += 1
    print(bar, end='\r')
    sys.stdout.flush()


def get_msgs(api, id):

    for number in count(0, 200):

        msgs=api.messages.get(offset=number, count=200)[1:]
        for msg in msgs:
            if ( not msg.get("chat_id") and msg.get("uid") == id ) or msg.get("chat_id") == id:
                yield msg

        time.sleep(0.5)

def get_urls(msgs):

    for msg in msgs:
        if msg.get("attachments"):
            for attachment in msg.get("attachments"):
                url=attachment.get("photo", {}).get("src_big")
                if url:
                    yield url

def mkdir(vk_user_name):

    dirname=os.path.join(os.environ.get("USERPROFILE", os.environ.get("HOME")), "vk_pics", vk_user_name)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    return dirname


def get_dialogs(api):

    dialogs=enumerate(api.messages.getDialogs()[1:], 1)
    user_ids_names={}

    for (number, dialog) in dialogs:
        user=api.users.get(user_ids=dialog["uid"])[0]

        time.sleep(0.3)

        user_ids_names[number]={
            "id":dialog.get("chat_id", user["uid"]),
            "name": dialog["title"]  if dialog.get("users_count") else  " ".join( (user["first_name"], user["last_name"] ))
        }

    return user_ids_names


def show_prompt(user_ids_names):

    for number in user_ids_names:
        if os.name == "nt":
            print(str(number) + ". " + user_ids_names[number]["name"].encode("cp866", errors="ignore").decode("cp866", errors="ignore") )
        else:
            print(str(number) + ". "+ user_ids_names[number]["name"])

    while True:
        selected_number= input("Select a dialog ").strip()
        if selected_number.isdigit():
            selected_number=int(selected_number)
            if selected_number in user_ids_names.keys():
                return selected_number
        elif selected_number in ["exit", "quit"]:
            exit()
        else:
            print("Try again")


def main():

    session = vk.Session(TOKEN)
    api = vk.API(session)

    user_ids_names=get_dialogs(api)

    selected_number = show_prompt(user_ids_names)
    id=user_ids_names[selected_number]["id"]
    dirname=mkdir(user_ids_names[selected_number]["name"] )
    msgs= get_msgs(api, id)
    urls =  get_urls(msgs)

    bar = ProgressBar(0, max_width=60)
    bar.numerator = 0

    with ThreadPoolExecutor(max_workers=5) as executor:        
        executor.map(lambda url: download_pics(url, dirname, bar), urls)

if __name__ == "__main__" :

    logger = logging.getLogger()

    if not TOKEN:
        logger.error("TOKEN variable is empty")
        exit()

    main()

    print() #NEED FOR PROGRESS BAR

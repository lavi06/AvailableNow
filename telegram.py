import requests
from db import print_and_log



'''
Create a Telegram channel and Join below Channel
Channel_Name = "Sasha_Nicole_Updates"

You will recieve notification when Ad is Posted or Refreshed
'''

bot = "7146880684:AAHgAp_5O0rKYCoBCYj3RkP_BTzh5WQTcNo"
botname = "t.me/availalable_now_sasha_bot"

Channel_Name = "Sasha_Nicole_Updates"
channel_id = "@Sasha_Nicole_Updates"

def broadcast(msg):

    to_url = f"https://api.telegram.org/bot{bot}/sendMessage?chat_id={channel_id}&text={msg}&parse_mode=HTML"

    resp = requests.get(to_url)
    print_and_log("")
    print_and_log(resp.text)
    print_and_log("")
    return resp.text


# Refreshed Ad/ Created Ad/ Completed Scheduled Ad 
# broadcast()
# html = f"""
# ------------------
# Refreshed Ad 
# ------------------
# Scheduled Ad : {1}
# Start  : 12:00 PM
# End    : 2:00 PM
# Status : Running
# """
# # broadcast(html)

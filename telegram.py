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


### BREVO - SIGN IN WITH GOOGLE
def send_email(message):
    API_key = "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"

    headers = {
        'accept': 'application/json',
        'api-key': API_key,
        'content-type': 'application/json',
    }

    json_data = {
        'sender': {
            'name': 'AvailableNow-BOT',
            'email': 'sashanicole.availablenow@gmail.com',
        },
        'to': [
            {
                'email': 'minxl@protonmail.com',
                'name': 'Sasha Nicole',
            },
        ],
        'subject': "AvailableNow : Message Alerts" ,
        'htmlContent': '<html><head></head><body><p>' + message +'</p></body></html>',
    }

    response = requests.post('https://api.brevo.com/v3/smtp/email', headers=headers, json=json_data)
    print(response.content)



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

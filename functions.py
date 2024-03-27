import json
import random
import time
from datetime import datetime, timedelta

import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# from db import update_db, update_previous_data_db, update_scheduletask_db, update_scheduletask_db_stopped, \
#                get_previous_data_db, db_get_pending_tasks, db_add_pending_schedule, db_add_pending_tasks, \
#                db_get_all_scheduled_ads, db_get_all_completed_ads, db_delete_scheduled_ads, \
#                db_init

from exceptions import OperationalException, UserException, AlreadyScheduleException
# from forms import InitialForm, CreateForm, ScheduleForm
# from handle_login import validate_creds
# from telegram import broadcast
from db import print_and_log

####################################################################

def break_time_slot(schedule_at, ending_at, refreshing_time, refreshing_time_2):
    current_time = schedule_at
    time_blocks = {}

    while current_time < ending_at:
        if len(time_blocks) == 0:
            action = "Create"
        else:
            action = "Refresh"

        # Generate a random duration between refreshing_time and refreshing_time_2
        duration = random.randint(refreshing_time, refreshing_time_2)

        end_time = min(current_time + timedelta(minutes=duration), ending_at)
        time_blocks[len(time_blocks)] = {
            "task_id": len(time_blocks),
            "start": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "action": action,
            "status": "Pending"
        }

        current_time = end_time

    time_blocks[len(time_blocks)] = {
        "task_id" : len(time_blocks),
        "start" : ending_at.strftime('%Y-%m-%d %H:%M:%S'),
        "end" : current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "action" : "Delete",
        "status" : "Pending"
    }

    return time_blocks


def give_json_request(form):

    json_data = {
        # Select Your Location
        "city_id": form.city_id.data,
        "state": form.state.data,
        "country": form.country.data,
        "country_id": form.country_id.data,
        "state_id": form.state_id.data,
        "city": form.city.data,
        "visiting": form.visiting.data,

        # Select Your Donation
        "by_request": form.by_request.data,
        "currency": form.currency.data if form.by_request.data == 'RATES' else None,
        "donation_1": form.donation_1.data if form.by_request.data == 'RATES' else None,
        "donation_1_duration": form.donation_1_duration.data if form.by_request.data == 'RATES' else None,
        "donation_2": form.donation_2.data if form.by_request.data == 'RATES' else None,
        "donation_2_duration": form.donation_2_duration.data if form.by_request.data == 'RATES' else None,

        # In-calls / Out-calls
        "in_calls": form.in_calls.data,
        "out_calls": form.out_calls.data,

        # Select Your Available Time for TODAY Only
        "today_anytime": form.today_anytime.data,

        # "today_available_to": form.today_available_to.data if not form.today_anytime.data else None,
        # "today_available_from": form.today_available_from.data if not form.today_anytime.data else None,

        # Reviews
        "show_reviews": form.show_reviews.data,

        # Website
        "show_website": form.show_website.data,

        # Ask Me About
        "face_time": form.face_time.data,
        "private_calls": form.private_calls.data,
        "specials": form.specials.data,
        "cancellation_policy": form.cancellation_policy.data,
        "private_text": form.private_text.data,
        "two_girls": form.two_girls.data,
        "menu": form.menu.data,
        "skype": form.skype.data,

        # Photos
        "show_photos": form.show_photos.data,
    }
    try:
        json_data["today_available_to"] = form.today_available_to.data
    except:
        pass
    try:
        json_data["today_available_from"] = form.today_available_from.data
    except:
        pass

    if form.in_calls.data:
        try:
            sub_city_id = int(form.sub_city_id.data)
            json_data["sub_city_id"] = form.sub_city_id.data
            # "sub_city": form.sub_city.data if form.in_calls.data else None,
        except:
            pass
    else:
        pass

    return json_data


def get_auth_header(access_token):
    headers = {
        'authority': 'api.preferred411.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'authorization': 'Bearer ' + access_token,
        'origin': 'https://preferred411.com',
        'referer': 'https://preferred411.com/',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/121.0.0.0 Safari/537.36',
    }
    return headers


def get_user_details(access_token, _id):
    _id = str(_id)

    try:
        headers = {
            'authorization': 'Bearer ' + access_token,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }

        response = requests.get(f'https://api.preferred411.com/api/companions/{_id}/availableNowAds/create', headers=headers)
        if response.status_code == 200:
            return response.json()["data"]

        else:
            raise UserException("Got 400/500 status code: " + str(response.status_code) + ", response: " +
                                str(response.json()))

    except requests.exceptions.RequestException as e:

        print_and_log(f"ERROR: Exception while fetching user details: {str(e)}")

        raise UserException("Error fetching details for user with ID: {}".format(_id)) from e

    except Exception as e:
        print_and_log(f"ERROR: Unexpected exception while fetching user details: {str(e)}")
        raise UserException("Error fetching details for user with ID: {}".format(_id)) from e


def check_status(access_token, _id):

    try:
        headers = get_auth_header(access_token)
        response = requests.get(f'https://api.preferred411.com/api/companions/availableNowAds/{_id}/myPost', headers=headers)

        data = response.json()

        if str(data["data"]["post"]) == "null" or data["data"]["post"] is None:
            return False
        else:
            return True

    except requests.exceptions.RequestException as e:
        print_and_log(f"ERROR: Could Not check status due to network issues: {str(e)}")
        raise OperationalException("ERROR: Could Not Check status due to network: " + str(e))

    except Exception as e:
        print_and_log(f"ERROR: Could Not check status with following error: {str(e)}")
        raise OperationalException("ERROR: Could Not check status with following error: " + str(e))


def delete_ad(access_token, _id):
    try:
        headers = get_auth_header(access_token)

        response = requests.delete(f'https://api.preferred411.com/api/companions/{_id}/availableNowAds',
                                   headers=headers)

        data = response.json()

        if data["status"] == "success":
            return data, True
        else:
            return data, False

    except requests.exceptions.RequestException as e:
        print_and_log(f"ERROR: Could Not delete ad due to network issues: {str(e)}")
        raise OperationalException("ERROR: Could Not delete ad due to network: " + str(e))

    except Exception as e:
        print_and_log(f"ERROR: Could Not delete ad with following error: {str(e)}")
        raise OperationalException("ERROR: Could Not delete ad with following error: " + str(e))


def create_ad(access_token, _id, form=None, json_data=None):

    headers = get_auth_header(access_token)

    if json_data is None:
        json_data = give_json_request(form)

    userdata = get_user_details(access_token, _id)
    json_data["website"]: userdata.get("website")
    json_data["reviews"]: userdata.get("reviews")
    json_data["photos"]: userdata.get("photos")
    json_data["symbol"]: userdata.get("symbol")
    json_data["companion_id"]: _id

    response = requests.post(f'https://api.preferred411.com/api/companions/{_id}/availableNowAds', headers=headers, json=json_data)

    data = response.json()

    if data["status"] == "success":
        return data, response.status_code, "Success"
    else:
        return data, response.status_code, "Failed"


#################################
#################################









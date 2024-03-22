import json
import random
import threading
import time
from datetime import datetime, timedelta
import os

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from db import update_db, update_previous_data_db, update_scheduletask_db, update_scheduletask_db_stopped, \
               get_previous_data_db, db_get_pending_tasks, db_add_pending_schedule, db_add_pending_tasks, \
               db_get_all_scheduled_ads, db_get_all_completed_ads, db_delete_scheduled_ads, \
               db_init

from exceptions import OperationalException, UserException, AlreadyScheduleException
from forms import InitialForm, CreateForm, ScheduleForm
from handle_login import validate_creds
from telegram import broadcast
from db import print_and_log

####################################################################

app = Flask(__name__)
CORS(app)
app.config['WTF_CSRF_ENABLED'] = False
db_init()


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
        "sub_city_id": form.sub_city_id.data if form.in_calls.data else None,
        "sub_city": form.sub_city.data if form.in_calls.data else None,
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

@app.route("/check_status", methods=["POST"])
def status():

    initialform = InitialForm(request.form)

    if not initialform.validate():
        errors = initialform.errors
        return jsonify({'message': 'Form validation failed', 'errors': errors}), 400

    username = initialform.username.data
    password = initialform.password.data

    try:
        _id, logged, access_token = validate_creds(username, password)
        if not logged:
            raise UserException("User login failed, Invalid credentials")

        print_and_log(f"Logged In {_id} : {access_token}")

        is_done = check_status(access_token, _id)

        return jsonify(data={"status": is_done}), 200

    except Exception as e:
        return jsonify({'message': 'Internal Server Error', 'errors': str(e)}), 500



@app.route("/get_user_fields", methods=["POST"])
def user_fields():


    initialform = InitialForm(request.form)

    if not initialform.validate():
        errors = initialform.errors
        return jsonify({'message': 'Form validation failed', 'errors': errors}), 400

    username = initialform.username.data
    password = initialform.password.data

    try:
        _id, logged, access_token = validate_creds(username, password)
        if not logged:
            raise UserException("User login failed, Invalid credentials")

        print_and_log(f"Logged In {_id} : {access_token}")

        data = get_user_details(access_token, _id)

        return jsonify({'data': data}), 200

    except Exception as e:

        return jsonify({'message': 'Internal Server Error', 'errors': str(e)}), 500



@app.route("/schedule", methods=["POST"])
def schedule():

    scheduler_form = ScheduleForm(request.form)

    if not scheduler_form.validate():
        return jsonify(
            {
                "message": "Failed to validate the form",
                "errors": scheduler_form.errors
            }), 403

    try:
        schedule_at = scheduler_form.schedule_at.data
        ending_at   = scheduler_form.ending_at.data
        refreshing  = scheduler_form.refreshing.data
        refreshing_2 = scheduler_form.refreshing_2.data

        local_schedule_at = scheduler_form.local_schedule_at.data
        local_ending_at   = scheduler_form.local_ending_at.data

        username = scheduler_form.username.data

        status = "Scheduled"

        time_blocks = break_time_slot(schedule_at, ending_at, refreshing, refreshing_2)

        subprocesses = json.dumps(time_blocks)
        json_data = give_json_request(scheduler_form)


        ### ADD Json Fields to a file
        update_previous_data_db(username, json.dumps(json_data))

        #### SCEHDULE DATA TO DATABASE
        data = {"username": username , "password": scheduler_form.password.data, "refreshing": refreshing,
                "schedule_at": schedule_at, "ending_at": ending_at, 
                "local_schedule_at": local_schedule_at, "local_ending_at": local_ending_at, 
                "json_data": json_data, "status" : status,
                "sub_processes" : subprocesses
                }

        _id = db_add_pending_schedule(**data)

        #### Add Tasks to Database 
        for block in time_blocks:
            block = time_blocks[block]

            data = {"schedule_id" : _id,
                    "username": scheduler_form.username.data, "password": scheduler_form.password.data, "json_data": json_data,
                    "start": block.get("start"), "end": block.get("end"), "action": block.get("action"),
                    "status":"Scheduled", "task_status": block.get("status"), "task_id": block.get("task_id")
                    }

            db_add_pending_tasks(**data)

        return jsonify({"message": f"Successfully added: Schedule ID {_id} | Tasks {len(time_blocks)}"}), 200


    except AlreadyScheduleException as e:
        return jsonify({"message": "found already scheduled task", "errors": str(e)}), 403

    except Exception as e:
        print_and_log(f"run scheduler error: {str(e)}")
        return jsonify({"message": "run scheduler error", "errors": str(e)}), 403


@app.route("/stop_ad/<username>/<int:schedule_id>", methods=["POST"])
def delete_running_ad(username, schedule_id):

    initialform = InitialForm(request.form)

    if not initialform.validate():
        errors = initialform.errors
        return jsonify({'message': 'Form validation failed', 'errors': errors}), 400

    username = initialform.username.data
    password = initialform.password.data

    try:

        _id, logged, access_token = validate_creds(username, password)
        if not logged:
            raise UserException("User login failed, Invalid credentials")

        print_and_log(f"Logged In {_id} : {access_token}")

        delete_content, delete_status = delete_ad(access_token, str(_id))
        print_and_log(f"Stopped ad: {delete_status} | {delete_content}")


        update_scheduletask_db_stopped(schedule_id, "Completed")

        #### Delete
        db_delete_scheduled_ads(username, schedule_id, False)

        return jsonify(data={"status": delete_content}), 200

    except Exception as e:
        return jsonify({'message': 'Internal Server Error', 'errors': str(e)}), 500


@app.route("/completed_ads/<username>/<int:page>", methods=["GET"])
def completed_ads(username, page):
    '''
    LIST OF ALL Completed Ads
    '''
    try:
        schedule_tasks = db_get_all_completed_ads(username, page)

        for i,each in enumerate(schedule_tasks):
            schedule_tasks[i]["json_data"]   = json.loads(schedule_tasks[i]["json_data"])
            schedule_tasks[i]["sub_processes"] = json.loads(schedule_tasks[i]["sub_processes"])

        return jsonify({'completed_ads': schedule_tasks}), 200
    except Exception as e:
        print_and_log(f"run scheduler error: {str(e)}")
        return jsonify({"message": "run scheduler error", "errors": str(e)}), 403


@app.route("/scheduled_ads/<username>", methods=["GET"])
def scheduled_ads(username):
    '''
    LIST OF ALL SCHEDULED Ads
    '''
    try:
        schedule_tasks = db_get_all_scheduled_ads(username)
        for i,each in enumerate(schedule_tasks):
            schedule_tasks[i]["json_data"]   = json.loads(schedule_tasks[i]["json_data"])
            schedule_tasks[i]["sub_processes"] = json.loads(schedule_tasks[i]["sub_processes"])

        return jsonify({'schedule_ads': schedule_tasks}), 200
    except Exception as e:
        print_and_log(f"run scheduler error: {str(e)}")
        return jsonify({"message": "run scheduler error", "errors": str(e)}), 403


@app.route("/scheduled_ads/<username>/<int:_id>", methods=["DELETE"])
def delete_ads(username, _id):
    '''
    DELETE AN SCHEDULED AD
    '''
    try:
        schedule_tasks, msg = db_delete_scheduled_ads(username, _id, True)

        return jsonify({'status': schedule_tasks, "message":msg}), 200

    except Exception as e:
        print_and_log(f"error: {e}")
        return jsonify({"message": "error", "errors": str(e)}), 403


@app.route("/previous_fields/<username>", methods=["GET"])
def previous_fields(username):
    try:
        ### Get Previous Data From database
        data = get_previous_data_db(username)

        return jsonify({'data': data}), 200
    except:
        return jsonify({'data': {}}), 403


def run_scheduler():

    while True:

        pending_task = db_get_pending_tasks()

        if not pending_task:
            print_and_log("[SCHEDULER]: waiting for 5 sec")
            time.sleep(5)
            continue

        try:
            print_and_log("-------------------------------------------------")
            print_and_log("-------------------------------------------------")
            print_and_log(f"Found one request in pending Task {pending_task}")

            primary_task_id = pending_task.get("id")
            scheduleid      = pending_task["schedule_id"]
            task_id         = pending_task["task_id"]
            username = pending_task["username"]
            password = pending_task["password"]
            action   = pending_task["action"]
            start    = datetime.strptime(pending_task["start"], "%Y-%m-%d %H:%M:%S")
            end      = datetime.strptime(pending_task["end"], "%Y-%m-%d %H:%M:%S")


            if action == "Delete":
                schedule_status = "Completed"
            elif action == "Create" or action == "Refresh":
                schedule_status = "Running"

            if end <= datetime.utcnow() and action != "Delete":
                TASK_STATUS = "Expired"
                ### IF TASK TIME IS EXPIRED

                update_db("TASKS", primary_task_id, "status", schedule_status, "task_status", "Expired")
                local_schedule_start, local_schedule_end = update_scheduletask_db(scheduleid, schedule_status, task_id, "Expired")

            else:


                TASK_STATUS = "Initiated"
                status = "Completed"

                _id, logged, access_token = validate_creds(username, password)
                if not logged:
                    raise UserException("User login failed, Invalid credentials")


                # Create/Refresh/Delete
                if action == "Delete":
                    schedule_status = "Completed"
                    print_and_log("TASK : Delete Ad")

                    delete_content, delete_status = delete_ad(access_token, str(_id))

                    label = "Deleted"
                    print_and_log(f"Ad : {label} | {delete_status} | {delete_content}")
                    TASK_STATUS = "Deleted"

                elif action == "Create" or action == "Refresh":
                    schedule_status = "Running"

                    label = "Creating" if action == "Create" else "Refreshing"
                    print_and_log(f"TASK : {label} Ad")

                    json_data = pending_task["json_data"]
                    json_data = json.loads(json_data)

                    delete_content, delete_status = delete_ad(access_token, str(_id))
                    label = "Deleted"
                    print_and_log(f"Ad : {label} | {delete_status} | {delete_content}")
                    TASK_STATUS = "Deleted"

                    create_content, create_status_code, TASK_STATUS = create_ad(access_token, _id, json_data=json_data)

                    label = "Created" if action == "Create" else "Refreshed"
                    print_and_log(f"Ad : {label} | {create_status_code} : {TASK_STATUS} | {create_content}")


                update_db("TASKS", primary_task_id, "status", schedule_status, "task_status", TASK_STATUS)
                local_schedule_start, local_schedule_end = update_scheduletask_db(scheduleid, schedule_status, task_id, TASK_STATUS)


                ###############
                html = f"""
                ------------------
                {label} Ad - {TASK_STATUS}
                ------------------
                Scheduled Ad : {scheduleid}
                Start  : {local_schedule_start}
                End    : {local_schedule_end}
                Status : {schedule_status}
                """

                broadcast(html)
                ###############

            # print_and_log("TASK Success: 200", create_content, create_status_code, create_status)
            print_and_log("TASK Success: 200")

        except Exception as e:
            TASK_STATUS = "Error"

            update_db("TASKS", primary_task_id, "status", schedule_status, "task_status", TASK_STATUS)
            local_schedule_start, local_schedule_end = update_scheduletask_db(scheduleid, schedule_status, task_id, TASK_STATUS)

            ###############
            html = f"""
            ------------------
            Task : {action}
            Task Status : {TASK_STATUS}
            {str(e)}
            ------------------
            Scheduled Ad : {scheduleid}
            Start  : {local_schedule_start}
            End    : {local_schedule_end}
            Status : {schedule_status}
            """

            broadcast(html)
            ###############
            # print_and_log("TASK Error: ", e)



run_scheduler()
print_and_log("starting the scheduling thread")
scheduling_thread = threading.Thread(target=run_scheduler)
scheduling_thread.daemon = True
scheduling_thread.start()

app.run(host='0.0.0.0', port=5000, debug=True)




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
from functions import *

####################################################################

app = Flask(__name__)
CORS(app)
app.config['WTF_CSRF_ENABLED'] = False
db_init()

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

    return jsonify({'data': {}}), 200

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

        _status = check_status(access_token, _id)

        if _status == False:
            data = get_user_details(access_token, _id, "Create")
        elif _status == True:
            data = get_user_details(access_token, _id, "Edit")

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
        data = {
            "by_request": "ASK",
            "cancellation_policy": True,
            "country": "United States",
            "country_id": 1,
            "state": "Texas",
            "state_id": 45,
            "city": "Houston",
            "city_id": 260,
            "currency": "",
            "donation_1": "",
            "donation_1_duration": "",
            "donation_2": "",
            "donation_2_duration": "",
            "face_time": True,
            "in_calls": True,
            "menu": True,
            "out_calls": True,
            "private_calls": True,
            "private_text": True,
            "show_photos": True,
            "show_reviews": True,
            "show_website": True,
            "skype": True,
            "specials": True,
            "sub_city_id": "",
            "today_anytime": "1",
            "today_available_from": "08:00 AM",
            "today_available_to": "05:00 PM",
            "two_girls": True,
            "visiting": True
        }
        return jsonify({'data': data}), 403


def tail(n=1000):
    """
    Read the last n lines from the file.
    """
    filename = "LOGS.log"

    with open(filename, 'r') as file:
        # Move the file pointer to the end
        file.seek(0, os.SEEK_END)
        # Track the current position in the file

        position = file.tell()

        lines = []
        # Start reading the file from the end
        while position > 0 and len(lines) < n:
            # Move the position backwards by 1
            position -= 1
            # Move the file pointer to the new position
            file.seek(position, os.SEEK_SET)
            # Read the character at the current position
            char = file.read(1)
            # If the character is a newline, we found a line
            if char == '\n':
                lines.append(file.readline().rstrip())

        # Reverse the list to get the lines in correct order
        # lines.reverse()
        return lines


def read_log_file(page_num, page_size, log_lines):

    # Calculate start and end indexes for pagination
    start_index = (page_num - 1) * page_size
    end_index = min(start_index + page_size, len(log_lines))

    # Extract lines for the current page
    page_lines = log_lines[start_index:end_index]

    return page_lines


@app.route('/log/<page_num>')
def get_log(page_num):

    # # Get query parameters for pagination
    # page_num = int(request.args.get('page', 1))
    page_num = int(page_num)
    page_size = 250

    log_lines = tail(page_size*page_num)
    paginated_lines = read_log_file(page_num, page_size, log_lines)
    paginated_lines = "\n".join(reversed(paginated_lines)).replace('\n', '<br>')
    # return jsonify(message="Hello,\nWorld!")
    return paginated_lines


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)




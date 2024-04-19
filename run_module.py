import json
import random
import threading
import time
from datetime import datetime, timedelta
import os

import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS

from db import update_db, update_previous_data_db, update_scheduletask_db, update_scheduletask_db_stopped, \
               get_previous_data_db, db_get_pending_tasks, db_add_pending_schedule, db_add_pending_tasks, \
               db_get_all_scheduled_ads, db_get_all_completed_ads, db_delete_scheduled_ads, \
               db_init

from exceptions import OperationalException, UserException, AlreadyScheduleException
from forms import InitialForm, CreateForm, ScheduleForm
from handle_login import validate_creds
from telegram import broadcast, send_email
from db import print_and_log
from functions import *

####################################################################

# db_init()

#################################
#################################


def run_scheduler():
    i = 0

    while True:

        time.sleep(5)
        if i%20 == 0:
            # print_and_log(f"{i} - [SCHEDULER]: waiting for 5 sec")
            to_print = 1
        else:
            to_print = 0

        pending_task = db_get_pending_tasks(to_print)
        i += 1

        if not pending_task:
            continue

        try:
            print_and_log("-------------------------------------------------")
            print_and_log("-------------------------------------------------")
            print_and_log(f"Found one request in pending Task : {pending_task['action']} | {pending_task}")
            print_and_log("")
            primary_task_id = pending_task.get("id")
            scheduleid      = pending_task["schedule_id"]
            task_id         = pending_task["task_id"]
            username        = pending_task["username"]
            password        = pending_task["password"]
            action          = pending_task["action"]
            start           = datetime.strptime(pending_task["start"], "%Y-%m-%d %H:%M:%S")
            end             = datetime.strptime(pending_task["end"], "%Y-%m-%d %H:%M:%S")


            if action == "Delete":
                schedule_status = "Completed"
            elif action == "Create" or action == "Refresh":
                schedule_status = "Running"


            # if (end == datetime.utcnow() and action != "Delete") or (end < datetime.utcnow() and action == "Delete"):
            if (end <= datetime.utcnow() and action != "Delete"):
                TASK_STATUS = "Expired"
                ### IF TASK TIME IS EXPIRED

                update_db("TASKS", primary_task_id, "status", schedule_status, "task_status", "Expired")
                local_schedule_start, local_schedule_end = update_scheduletask_db(scheduleid, schedule_status, task_id, "Expired")

            elif action == "Check Message":
                ### Code to check message
                schedule_status = "Running"
                TASK_STATUS = "Initiated"                

                print_and_log("Cheching Inbox : ")
                _id, logged, access_token = validate_creds(username, password)
                if not logged:
                    raise UserException("User login failed, Invalid credentials")

                messages = check_message(access_token)
                if messages:
                    if messages > 0:
                        ## Trigger Email
                        send_email(f"{messages} Unread Messages in Inbox")
                        TASK_STATUS = f"{messages} Unread"

                update_db("TASKS", primary_task_id, "status", schedule_status, "task_status", TASK_STATUS)
                local_schedule_start, local_schedule_end = update_scheduletask_db(scheduleid, schedule_status, task_id, TASK_STATUS)

            else:

                TASK_STATUS = "Initiated"
                status      = "Completed"

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

                    label = "Deleted Old Ad"
                    print_and_log(f"Ad : {label} | {delete_status} | {delete_content}")

                    TASK_STATUS = "Deleted Old Ad"

                    create_content, create_status_code, TASK_STATUS = create_ad(access_token, _id, json_data = json_data)

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

                broadcast(html.replace("                ",""))
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

            broadcast(html.replace("            ",""))
            ###############
            print_and_log("TASK Error: ", str(e))


run_scheduler()


# print_and_log("starting the scheduling thread")
# scheduling_thread = threading.Thread(target=run_scheduler)
# scheduling_thread.daemon = True
# scheduling_thread.start()




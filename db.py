import datetime
import json
import sqlite3
from exceptions import DbException, AlreadyScheduleException
from os import path
import logging


DB_NAME = "saved.db"

PENDING_SCHEDULE_COLUMNS = ['id', "schedule_id","task_id", "username", "password", 'json_data', 'start', 'end', 'action', 'status', 'task_status']
SCHEDULE_LIST_COLUMNS    = ['id', 'username', 'created_at', 'schedule_at', 'ending_at', 'refreshing',"json_data", "status", "sub_processes", 'completed_at', 'log']


ROOT = path.dirname(path.realpath(__file__))
DB_NAME = path.join(ROOT, DB_NAME)


logger_file_name = f"LOGS.log"
logging.basicConfig(filename = path.join(ROOT, logger_file_name), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def print_and_log(statement, log_level = logging.INFO):
    print(statement)
    # Log the statement with the specified log level
    if log_level == logging.DEBUG:
        logging.debug(statement)
    elif log_level == logging.INFO:
        logging.info(statement)
    elif log_level == logging.WARNING:
        logging.warning(statement)
    elif log_level == logging.ERROR:
        logging.error(statement)
    elif log_level == logging.CRITICAL:
        logging.critical(statement)
    else:
        logging.info(statement)
        # raise ValueError("Invalid log level")



def _db_get_connection():
    try:
        return sqlite3.connect(DB_NAME)
    except Exception as e:
        print_and_log(f"exception occurred while connecting to database: {DB_NAME}", e)
        return None


def _db_create_table(create_table_query):
    conn = _db_get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # print_and_log(f"create table SQL Query: {create_table_query}")
        cursor.execute(create_table_query)
        conn.commit()

    except Exception as e:
        print_and_log(f"exception occurred while: {str(e)}")
        return
    finally:
        if conn is not None:
            conn.close()


def db_init():
    print_and_log("initializing database")
    create_credentials = (
        "CREATE TABLE IF NOT EXISTS credentials ("
        "username VARCHAR(255) NOT NULL, "
        "password VARCHAR(255) NOT NULL, "
        "cookies TEXT NOT NULL, "
        "PRIMARY KEY (username, password)"
        ");"
    )
    _db_create_table(create_credentials)

    create_schedule_task = (
        "CREATE TABLE IF NOT EXISTS ScheduleTask( "
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username VARCHAR(255) NOT NULL, "
        "password VARCHAR(255) NOT NULL, "
        "refreshing INT DEFAULT 30, "
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
        "schedule_at DATETIME DEFAULT NULL, "
        "ending_at DATETIME DEFAULT NULL, "
        "local_schedule_at DATETIME DEFAULT NULL, "
        "local_ending_at DATETIME DEFAULT NULL, "
        "json_data TEXT, "
        "sub_processes TEXT, "
        "status TEXT, "
        "completed_at DATETIME DEFAULT NULL ,"
        "log TEXT DEFAULT NULL "
        "); "
    )
    _db_create_table(create_schedule_task)

    task = (
        "CREATE TABLE IF NOT EXISTS TASKS( "
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "schedule_id INTEGER NOT NULL, "
        "task_id INTEGER NOT NULL, "
        "username VARCHAR(255) NOT NULL, "
        "password VARCHAR(255) NOT NULL, "
        "json_data TEXT, "
        "start DATETIME DEFAULT NULL, "
        "end DATETIME DEFAULT NULL, "
        "action VARCHAR(255), "
        "status VARCHAR(255), "
        "task_status VARCHAR(255) DEFAULT Pending"
        "); "
    )
    _db_create_table(task)

    previous_data = (
        "CREATE TABLE IF NOT EXISTS previous_data( "
        "username VARCHAR(255) NOT NULL, "
        "data VARCHAR(255)"
        "); "
    )
    _db_create_table(previous_data)


##################################################

def db_get_cookies(username: str, password: str):
    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:
        cookies = None
        cursor = conn.cursor()

        sql_query = "SELECT cookies FROM credentials WHERE username = ? and password = ?"
        cursor.execute(sql_query, (username, password))
        print_and_log(f"[SQL-QUERY]-[GET-COOKIES] : {sql_query}")

        result = cursor.fetchone()
        if result is not None:
            cookies = result[0]

        return cookies
    except Exception as e:
        raise DbException(f"failed to get the cookies `{username}`, `{password}`: " + str(e))
    finally:
        conn.close()


def db_set_cookies(username: str, password: str, cookies: str):
    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:
        cursor = conn.cursor()

        sql_query = "INSERT OR REPLACE INTO credentials (username, password, cookies) VALUES (?, ?, ?)"
        cursor.execute(sql_query, (username, password, cookies))
        print_and_log(f"[SQL-QUERY]-[SET-COOKIES] {sql_query}")
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        raise DbException(f"failed to set the cookies `{username}`, `{password}`: " + str(e))
    finally:
        conn.close()

#########################

def update_db(database, _id, field1, value1, field2, value2):

    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:

        cursor = conn.cursor()

        sql_query = f"UPDATE {database} SET {field1} = '{value1}', {field2} = '{value2}' WHERE id = {_id}"

        print_and_log(f"[SQL-QUERY]- {sql_query}")
        cursor.execute(sql_query)

        conn.commit()
        return cursor.rowcount

    except Exception as e:
        raise DbException(f"failed to set completed schedule task: " + str(e))

    finally:
        conn.close()


def update_previous_data_db(username, data):

    conn = _db_get_connection()

    if conn is None:
        return DbException("Database connection failed")

    try:

        cursor = conn.cursor()

        sql_query = f"INSERT OR REPLACE INTO previous_data (username, data) VALUES ('{username}', '{data}');"
        print_and_log(f"[SQL-QUERY]-[SET-Previous Data] {sql_query}")

        cursor.execute(sql_query)

        conn.commit()

        return cursor.rowcount

    except Exception as e:
        raise DbException(f"Failed to Update Previous Data: " + str(e))

    finally:
        conn.close()


def update_scheduletask_db(scheduleid, schedule_status, task_id, TaskStatus):

    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:
        cursor = conn.cursor()

        sql_query = f"SELECT local_schedule_at, local_ending_at, sub_processes from ScheduleTask WHERE id = {scheduleid}"
        cursor.execute(sql_query)

        ########
        data = cursor.fetchone()
        local_schedule_start = data[0]
        local_schedule_end   = data[1]

        subprocesses = data[2]
        subprocesses = json.loads(subprocesses)

        subprocesses[str(task_id)]["status"] = TaskStatus 
        subprocesses = json.dumps(subprocesses)


        sql_query = f"UPDATE ScheduleTask SET sub_processes = '{subprocesses}', status = '{schedule_status}' WHERE id = {scheduleid}"

        print_and_log(f"[SQL-QUERY]- {sql_query}")
        cursor.execute(sql_query)

        conn.commit()

        return local_schedule_start, local_schedule_end

    except Exception as e:
        raise DbException(f"Failed To Update Schedule {scheduleid}: " + str(e))
    finally:
        conn.close()


def update_scheduletask_db_stopped(scheduleid, schedule_status):

    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:
        cursor = conn.cursor()

        sql_query = f"SELECT sub_processes from ScheduleTask WHERE id = '{scheduleid}'"
        cursor.execute(sql_query)

        ########
        subprocesses = cursor.fetchone()[0]
        subprocesses = json.loads(subprocesses)

        for subprocess_id in subprocesses:

            subprocess_data = subprocesses[subprocess_id]

            if subprocess_data["status"] in ["Running","Pending"]:
                subprocesses[subprocess_id]["status"] = "Deleted" 

        subprocesses = json.dumps(subprocesses)


        sql_query = f"UPDATE ScheduleTask SET sub_processes = '{subprocesses}', status = '{schedule_status}' WHERE id = '{scheduleid}'"

        print_and_log(f"[SQL-QUERY]-[Ad Stopped] {sql_query}")
        cursor.execute(sql_query)

        conn.commit()
        return cursor.rowcount

    except Exception as e:
        raise DbException(f"Failed To Update Schedule {scheduleid}: " + str(e))
    finally:
        conn.close()


def get_previous_data_db(username):

    conn = _db_get_connection()

    if conn is None:
        return DbException("Database connection failed")

    try:

        cursor = conn.cursor()

        sql_query = f"SELECT * FROM previous_data WHERE username = '{username}'"

        print_and_log(f"[SQL-QUERY]-[GET-Previous Data] : {sql_query}")
        cursor.execute(sql_query)

        try:
            data = cursor.fetchone()[1]
            data = json.loads(data)
        except:
            data = {}

        conn.commit()

        return data

    except Exception as e:
        raise DbException(f"Failed to GET Previous Data: " + str(e))

    finally:
        conn.close()




def db_get_pending_tasks():

    conn = _db_get_connection()
    if conn is None:
        return DbException("Database connection failed")

    try:
        cursor = conn.cursor()

        sql_query = (
            "SELECT * "
            "FROM TASKS "
            "WHERE start <= datetime('now') "
            "AND task_status = 'Pending';"
        )

        print_and_log(f"[SQL_QUERY]-[PENDING-TASK]: {sql_query}")

        cursor.execute(sql_query)
        schedule_tasks = cursor.fetchall()
        schedule_dict = [dict(zip(PENDING_SCHEDULE_COLUMNS, task)) for task in schedule_tasks]
        if schedule_dict:
            return schedule_dict[0]

        return None
    except Exception as e:
        raise DbException(f"failed to set completed schedule task: " + str(e))
    finally:
        conn.close()


def db_add_pending_schedule(**kwargs):
    conn = _db_get_connection()
    if conn is None:
        return DbException(f"Database connection failed")

    try:
        schedule_at = kwargs.get("schedule_at", None)
        ending_at = kwargs.get("ending_at", None)

        kwargs["json_data"] = json.dumps(kwargs["json_data"])

        cursor = conn.cursor()

        sql_query = (
            f"SELECT id, schedule_at, ending_at "
            f"FROM ScheduleTask "
            f"WHERE status = 'Scheduled' AND ("
            f"(schedule_at > '{schedule_at}' AND ending_at < '{ending_at}') "
            f"OR "
            f"(schedule_at < '{schedule_at}' AND ending_at > '{ending_at}') "
            f"OR "
            f"(schedule_at = '{schedule_at}') "
            f"OR "
            f"(ending_at = '{ending_at}') "
            ");"
        )
        print_and_log(f"[SQL-QUERY]-[ADD-PENDING-SCHEDULING]: {sql_query}")

        cursor.execute(sql_query)

        total = cursor.fetchone()

        if total is not None:
            raise AlreadyScheduleException(f"Ad Overlap with ID {total[0]} | {total[1]} - {total[2]}")


        sql_query = "INSERT INTO ScheduleTask ({}) VALUES ({})".format(
            ', '.join(kwargs.keys()),
            ', '.join(['?' for _ in range(len(kwargs))])
        )
        print_and_log(f"[SQL-QUERY]-[ADD-PENDING-SCHEDULING]: {sql_query} {tuple(kwargs.values())}")

        cursor.execute(sql_query, tuple(kwargs.values()))
        conn.commit()

        return cursor.lastrowid
    except Exception as e:
        raise DbException(f"failed to add new schedule task: " + str(e))
    finally:
        conn.close()



def db_add_pending_tasks(**kwargs):
    conn = _db_get_connection()
    if conn is None:
        return DbException(f"Database connection failed")

    try:
        schedule_at = kwargs.get("schedule_at", None)
        kwargs["json_data"] = json.dumps(kwargs["json_data"])

        cursor = conn.cursor()

        sql_query = "INSERT INTO TASKS ({}) VALUES ({})".format(
            ', '.join(kwargs.keys()),
            ', '.join(['?' for _ in range(len(kwargs))])
        )
        # print_and_log(f"[SQL-QUERY]-[ADD-PENDING-SCHEDULING]: {sql_query} {tuple(kwargs.values())}")
        print_and_log(f"[SQL-QUERY]-[ADD-PENDING-SCHEDULING]: {sql_query} {kwargs['task_id']}")

        cursor.execute(sql_query, tuple(kwargs.values()))
        conn.commit()

        return cursor.lastrowid

    except Exception as e:
        raise DbException(f"failed to add new schedule task: " + str(e))
    finally:
        conn.close()



def db_get_all_scheduled_ads(username):

    conn = _db_get_connection()
    if conn is None:
        return DbException(f"Database connection failed")

    try:
        cursor = conn.cursor()
        sql_query = (
            f"""
            select id, username, created_at, schedule_at, ending_at, refreshing, json_data, status, sub_processes, completed_at, log from ScheduleTask 
            WHERE (status = 'Scheduled' OR status = 'Running') AND username = '{username}' 
            ORDER BY schedule_at ASC
            ;"""
        )

        print_and_log(f"[SQL-QUERY]-[GET-ALL-SCHEDULE] {sql_query}")

        cursor.execute(sql_query)
        schedule_tasks = cursor.fetchall()
        schedule_dict = [dict(zip(SCHEDULE_LIST_COLUMNS, task)) for task in schedule_tasks]

        return schedule_dict

    except Exception as e:
        raise DbException(f"failed to add new schedule task: " + str(e))
    finally:
        conn.close()


def db_get_all_completed_ads(username, page):

    conn = _db_get_connection()
    if conn is None:
        return DbException(f"Database connection failed")

    try:
        cursor = conn.cursor()
        sql_query = (
            f"""
            SELECT id, username, created_at, schedule_at, ending_at, refreshing, json_data, status, sub_processes, completed_at, log from ScheduleTask 
            WHERE (status = 'Completed' OR status = 'Expired') AND username = '{username}' 
            ORDER BY schedule_at DESC 
            LIMIT 10 OFFSET {page-1 * 10}
            ;"""
        )

        print_and_log(f"[SQL-QUERY]-[GET-ALL-COMPLETED] {sql_query}")

        cursor.execute(sql_query)
        schedule_tasks = cursor.fetchall()
        schedule_dict = [dict(zip(SCHEDULE_LIST_COLUMNS, task)) for task in schedule_tasks]

        return schedule_dict

    except Exception as e:
        raise DbException(f"failed to add new schedule task: " + str(e))
    finally:
        conn.close()



def db_delete_scheduled_ads(username, _id, delete_scheduled_ad):

    conn = _db_get_connection()
    if conn is None:
        return DbException(f"Database connection failed")

    try:

        cursor = conn.cursor()
        sql_query = f"SELECT * FROM ScheduleTask WHERE id = {_id} AND username = '{username}';"
        cursor.execute(sql_query)

        data = cursor.fetchone()
        if data is None:
            return False, f"ScheduleTask {_id} Does not Exist"


        if delete_scheduled_ad:
            sql_query = f"DELETE FROM ScheduleTask WHERE id = {_id} AND username = '{username}';"

            print_and_log(f"[SQL-QUERY]-[DELETE-ScheduleAd] - {sql_query}")
            cursor.execute(sql_query)

        sql_query = f"DELETE FROM TASKS WHERE schedule_id = {_id};"
        print_and_log(f"[SQL-QUERY]-[DELETE-TASKS] - {sql_query}")
        cursor.execute(sql_query)

        conn.commit()

        return True, f"ScheduleTask {_id} Deleted"

    except Exception as e:
        raise DbException(f"failed to DELETE schedule task {_id}: " + str(e))
    finally:
        conn.close()





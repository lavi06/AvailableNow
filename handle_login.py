import requests
import json
from db import db_set_cookies, db_get_cookies
from exceptions import UserException, InvalidCredentialsError
from db import print_and_log


def login(username, password):

    # Returns Status_Code, Access_Token/Error
    print_and_log("Trying to Log In..")

    try:
        headers = {
            'authority': 'preferred411.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://preferred411.com',
            'pragma': 'no-cache',
            'referer': 'https://preferred411.com/companion/ads/create?type=create',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36',
        }

        s = requests.session()

        json_data = {
            'companion_id': username,
            'password': password,
        }

        url = "https://preferred411.com/api/companions/login"

        response = s.post(url, headers=headers, json=json_data)

        print_and_log(f"Response : {response.status_code}")
        print_and_log(f"Response : {response.text}")

        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print_and_log("Logged In Successfully..")

            cookies = s.cookies.get_dict()

            return response.status_code, cookies["access_token"]

        else:
            print_and_log("ERROR: Could Not login")
            print_and_log(f"Status Code: {response.status_code} Content: {response.content}")
            return 401, "Invalid Credentials"

    except requests.exceptions.RequestException as e:
        print_and_log(f"ERROR: Could Not login due to network issues: {str(e)}")
        raise UserException("Could Not login due to network issues:" + str(e))

    except Exception as e:
        print_and_log(f"ERROR: Could Not login with following error: {str(e)}")
        raise UserException("Could Not login, got an error message:" + str(e))


def check_login(access_token):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.77 Safari/537.36",
            'authorization': 'Bearer ' + access_token
        }

        s = requests.session()

        response = s.get("https://api.preferred411.com/api/authenticated/user", headers=headers)

        if "unauthenticated" in response.text.lower():
            return 0, False
        else:
            data = (response.json())
            return data["data"]["id"], True

    except requests.exceptions.RequestException as e:
        print_and_log(f"ERROR: Could Not check login due to network issues: {str(e)}")
        raise UserException("Could Not check login due to network issues:" + str(e))

    except Exception as e:
        print_and_log(f"ERROR: Could Not check login with following error: {str(e)}")
        return UserException("Could Not check login with following error:" + str(e))


def validate_creds(username, password):

    try:
        access_token = db_get_cookies(username, password)

        _id, logged = check_login(access_token)
        if logged:
            return _id, logged, access_token

    except Exception:
        print_and_log("Error while validating creds from saved file, trying to login with username and password")

    status_code, access_token = login(username, password)
    if status_code == 200:
        _id, logged = check_login(access_token)
        if logged:
            db_set_cookies(username, password, access_token)
            return _id, logged, access_token

    raise InvalidCredentialsError(message="Invalid Credentials")

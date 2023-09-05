import os
import sys
import time
import requests

XOXC_TOKEN = os.environ.get("XOXC_TOKEN")
D_COOKIE = os.environ.get("D_COOKIE", os.environ.get("D_TOKEN"))
SLEEP_TIMEOUT = 1


def get_admins():
    url = "https://slack.com/api/search.modules.people"
    payload = {
        "token": XOXC_TOKEN,
        "module": "people",
        "query": "",
        "page": "1",
        "extracts": "0",
        "highlight": "0",
        "extra_message_data": "1",
        "no_user_profile": "1",
        "count": "50",
        "file_title_only": "false",
        "query_rewrite_disabled": "false",
        "include_files_shares": "1",
        "browse": "standard",
        "max_filter_suggestions": "10",
        "sort": "name",
        "sort_dir": "asc",
        "account_type": "0,1,2",
        "hide_deactivated_users": "1",
        "custom_fields": "{}",
        "team": "T059W3GTFJA",
        "_x_reason": "browser-query",
        "_x_mode": "online",
        "_x_sonic": "true",
        "_x_app_name": "client",
    }
    headers = {"authority": "keephq-workspace.slack.com"}
    files = []
    cookies = {"d": D_COOKIE}
    response = requests.request(
        "POST", url, headers=headers, data=payload, files=files, cookies=cookies
    )
    admins = []
    for u in response.json().get("items", []):
        admins.append(u.get("username"))
    return admins


def send_slack_message(channel_id, message):
    """
    Send a message to a slack channel

    Args:
        channel_id (_type_): _description_
        message (_type_): _description_

    Returns:
        _type_: _description_
    """
    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {XOXC_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel_id, "text": message}
    cookies = {"d": D_COOKIE}

    response = requests.post(
        url, headers=headers, json=payload, cookies=cookies, timeout=5
    )
    return response.json()


def get_channel_users(channel_id, marker=None, admins=[]):
    """
    Get all users in a channel

    Args:
        channel_id (_type_): _description_
    """
    print(f"Getting channel users from channel id: {channel_id}")
    url = "https://edgeapi.slack.com/cache/T044F8YMNF6/users/list?fp=3c"
    headers = {
        "Authorization": f"Bearer {XOXC_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "token": XOXC_TOKEN,
        "include_profile_only_users": True,
        "count": 50,
        "channels": [channel_id],
        "filter": "people",
        "index": "users_by_realname",
        "locale": "en-US",
        "present_first": False,
        "fuzz": 1,
    }
    if marker:
        payload["marker"] = marker
    cookies = {"d": D_COOKIE}
    users = []
    response = requests.post(url, headers=headers, json=payload, cookies=cookies)
    response_json = response.json()
    users.extend(response_json.get("results", []))
    while response_json.get("next_marker"):
        next_marker = response_json.get("next_marker")
        payload = {**payload, "marker": next_marker}
        response = requests.post(url, headers=headers, json=payload, cookies=cookies)
        response_json = response.json()
        users.extend(response_json.get("results", []))
    print(f"Got channel users from channel id: {channel_id} ({len(users)})")

    users_without_admins = [
        u
        for u in users
        if u.get("is_admin") is False
        and u.get("is_owner") is False
        and u.get("is_primary_owner") is False
    ]
    return users_without_admins


def main():
    if not XOXC_TOKEN:
        print("XOXC_TOKEN is not set, get from browser devtools (COMMUNITY.slack.com)")
        sys.exit(1)
    if not D_COOKIE:
        print("D_COOKIE is not set, get from browser devtools (COMMUNITY.slack.com)")
        sys.exit(1)
    if len(sys.argv) < 3:
        print("Usage: python community_spammer.py <channel_id> <message>")
        sys.exit(1)
    channel = sys.argv[1]
    message = sys.argv[2]
    marker = None
    if len(sys.argv == 4):
        marker = sys.argv[3]
    print(f'Message is: "{message}"')
    # admins = get_admins()
    users = get_channel_users(channel_id=channel, marker=marker)
    for user in users:
        real_name = user.get("profile").get("real_name")
        first_name = real_name.split(" ")[0]
        print(f"Sending message to {real_name}")
        formatted_message = message.replace("[name]", first_name)
        try:
            send_slack_message(channel_id=user["id"], message=formatted_message)
        except Exception as e:
            print(f"Failed to send message to {real_name}: {e}")
        print(f"Sent message to {real_name}")
        print(f"Sleeping for {SLEEP_TIMEOUT} seconds")
        time.sleep(SLEEP_TIMEOUT)


if __name__ == "__main__":
    print("Starting...")
    main()
    print("Finished...")

from atomic_queries import _query_high_speed_ticket, _query_normal_ticket, _query_assurances, _query_food, \
    _query_contacts
from utils import random_boolean, random_phone, random_str, random_form_list

import logging
import random
import requests
import time

logger = logging.getLogger("query_and_preserve")
# The UUID of user fdse_microservice is that
uuid = "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f"
date = time.strftime("%Y-%m-%d", time.localtime())

base_address = "http://<TRAIN_TICKET_HOST>:31000"


def query_food(headers):
    _query_food(headers=headers)


if __name__ == '__main__':
    cookie = "JSESSIONID=<REDACTED>; YsbCaptcha=<REDACTED>"
    Authorization = "<REDACTED_JWT>"
    headers = {
        'Connection': 'close',
        "Cookie": f"{cookie}",
        "Authorization": f"Bearer {Authorization}",
        "Content-Type": "application/json"
    }

    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    for i in range(320):
        try:
            query_food(headers=headers)
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")

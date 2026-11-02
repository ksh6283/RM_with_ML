from atomic_queries import _query_high_speed_ticket, _query_normal_ticket, _query_assurances, _query_food, \
    _query_contacts, headers
from utils import random_boolean, random_phone, random_str, random_form_list

import logging
import random
import requests
import time

logger = logging.getLogger("query_and_preserve")
date = time.strftime("%Y-%m-%d", time.localtime())


def query_food(headers):
    _query_food(headers=headers)


if __name__ == '__main__':
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    for i in range(320):
        try:
            query_food(headers=headers)
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")

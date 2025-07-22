from atomic_queries import _query_high_speed_ticket, _query_normal_ticket, _query_high_speed_ticket_parallel
from utils import random_boolean

import logging
import time

logger = logging.getLogger("query_and_preserve")
# The UUID of user fdse_microservice is that
uuid = "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f"
date = time.strftime("%Y-%m-%d", time.localtime())

base_address = "http://<TRAIN_TICKET_HOST>:31000"


def query_travel_left_parallel(headers):
    """
    1. 查票（随机高铁或普通）
    2. 查保险、Food、Contacts
    3. 随机选择Contacts、保险、是否买食物、是否托运
    4. 买票
    :return:
    """
    start = ""
    end = ""
    trip_ids = []
    PRESERVE_URL = ""

    start = "Su Zhou"
    end = "Shang Hai"
    high_speed_place_pair = (start, end)
    trip_ids = _query_high_speed_ticket_parallel(place_pair=high_speed_place_pair, headers=headers, time=date)


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
    print(f"start:{start_time}")

    for i in range(320):
        try:
            query_travel_left_parallel(headers=headers)
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")

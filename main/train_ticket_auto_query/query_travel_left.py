from atomic_queries import _query_high_speed_ticket, _query_normal_ticket, headers
from utils import random_boolean

import logging
import time

logger = logging.getLogger("query_and_preserve")
date = time.strftime("%Y-%m-%d", time.localtime())


def query_travel_left(headers):
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

    high_speed = False
    if high_speed:
        start = "Shang Hai"
        end = "Su Zhou"
        high_speed_place_pair = (start, end)
        trip_ids = _query_high_speed_ticket(place_pair=high_speed_place_pair, headers=headers, time=date)
    else:
        start = "Shang Hai"
        end = "Nan Jing"
        other_place_pair = (start, end)
        trip_ids = _query_normal_ticket(place_pair=other_place_pair, headers=headers, time=date)


if __name__ == '__main__':
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"start:{start_time}")

    for i in range(30):
        try:
            query_travel_left(headers=headers)
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")

import logging
import time

from atomic_queries import _query_admin_basic_config

logger = logging.getLogger("query_and_preserve")
# The UUID of user fdse_microservice is that
uuid = "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f"
date = time.strftime("%Y-%m-%d", time.localtime())

base_address = "http://<TRAIN_TICKET_HOST>:31000"


def query_admin_basic_config(headers):
    _query_admin_basic_config(headers=headers)


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

    for i in range(330):
        try:
            query_admin_basic_config(headers=headers)
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")

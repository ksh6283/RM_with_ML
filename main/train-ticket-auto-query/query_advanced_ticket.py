from atomic_queries import _query_advanced_ticket, _login

import logging
import random
import time

logger = logging.getLogger("query_advanced_ticket")
# The UUID of user fdse_microservice is that
uuid = "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f"
date = time.strftime("%Y-%m-%d", time.localtime())

base_address = "http://<TRAIN_TICKET_HOST>:32677"



if __name__ == '__main__':
    _, token = _login()
    headers = {
        "Cookie": "JSESSIONID=<REDACTED>; YsbCaptcha=<REDACTED>",
        "Authorization": "Bearer <REDACTED_JWT>",
        "Content-Type": "application/json"
    }
    headers["Authorization"] = "Bearer " + token

    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    place_pairs = [("Shang Hai", "Su Zhou"),
                   ("Su Zhou", "Shang Hai"),
                   ("Nan Jing", "Shang Hai")]
    type = "quickest"
    for i in range(200):
        place_pair = random.choice(place_pairs)
        print(f"search {type} between {place_pair[0]} to {place_pair[1]}")
        try:
            trip_ids = _query_advanced_ticket(place_pair=place_pair, headers=headers, time=date, type=type)
            print(f"get {len(trip_ids)} routes.")
            print("*****************************INDEX:" + str(i))
        except Exception as e:
            print(e)

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"start:{start_time} end:{end_time}")
from atomic_queries import _query_advanced_ticket, _login, headers

import logging
import random
import time

logger = logging.getLogger("query_advanced_ticket")
date = time.strftime("%Y-%m-%d", time.localtime())



if __name__ == '__main__':
    _, token = _login()
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
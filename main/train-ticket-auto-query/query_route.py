from atomic_queries import _query_route

if __name__ == '__main__':

    headers = {
        "Cookie": "JSESSIONID=<REDACTED>; YsbCaptcha=<REDACTED>",
        "Authorization": "Bearer <REDACTED_JWT>",
        "Content-Type": "application/json"
    }

    _query_route(headers=headers)

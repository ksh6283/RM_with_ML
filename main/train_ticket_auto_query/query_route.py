from atomic_queries import headers as default_headers
from atomic_queries import _query_route

if __name__ == '__main__':

    headers = dict(default_headers)

    _query_route(headers=headers)

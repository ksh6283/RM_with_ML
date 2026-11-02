from framework.testing.testCollection_once import full_init, start_test
from configs import app
import logging

# 로깅 레벨을 DEBUG로 설정
logging.basicConfig(level=logging.DEBUG)

ports = {"social": 30628, "media": 30092, "hotel": 30096, "train": 32677}
app= "train"
# full_init(app, ports[app])

# Data is saved to <data_path>/<YYYYMMDD_HHMMSS>/ (see framework.utils.files.dated_data_path)
# continues=False: create a new run directory
# continues=True: append to the latest run directory
start_test(continues=False)
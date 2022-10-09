# Copyright 2022 Mikhail Stolpner
# Licensed under Apache 2.0 License https://www.apache.org/licenses/LICENSE-2.0

from Dashboard import Dashboard
from PMS import PMS

# Init PMS sensor
rstpin = 16
setpin = 18
sensor = PMS('/dev/serial0', rstpin, setpin, simulate=False)
dashboard = Dashboard()

try:
    # Init PMS
    sensor.wakeup()
    sensor.setStreamingMode()
    dashboard.monitor(sensor)


finally:
    sensor.release()



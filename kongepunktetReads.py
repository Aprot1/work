import re
import requests

from datetime import datetime, timezone
from influxdb import InfluxDBClient

temp_regex = re.compile(r't1">Temperature</span><span class="t2">(\d+.\d?)')
rh_regex = re.compile(r't1">Relative humidity</span><span class="t2">(\d+.\d?)')

r = requests.get('http://10.0.112.74/index.html', stream=True)
temp = temp_regex.findall(r.text)[0]
rh = rh_regex.findall(r.text)[0]

#print(f'temp = {float(temp)}, rh = {float(rh)}')

# Define measurement name and tags
measurement = 'kongepunktet'
tags = {}

# Define fields and timestamp
fields = {
    'temperature': float(temp),
    'rh': float(rh)
}
time = datetime.now(timezone.utc)

# Create data dictionary
data = [{
    'measurement': measurement,
    'tags': tags,
    'time': time,
    'fields': fields
}]

# Setup InfluxDB client
client = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'testDB')
client.switch_database('testDB')

# Write data to InfluxDB
client.write_points(data)

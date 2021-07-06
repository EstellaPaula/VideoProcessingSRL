import datetime
import requests
import time

# Fetch curent date
date = datetime.date.today()
dt_string = date.strftime("%Y-%m-%d")


# Route to server
url = 'http://rest_api:5000/api/cleanup?time=' + dt_string

time.sleep(86400)

while True:
    print("Attempting clean_up server")
    r = requests.delete(url)
    print(r.status_code)
    print(r.text)

    while r.status_code != 200:
        print("Attempting clean_up server")
        r =requests.delete(url)
        print(r)
    
    time.sleep(86400)

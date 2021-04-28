import requests

# Route to server 
# Replace server IP depending with public IP of server if not run locally

url_server_home = 'http://159.65.181.169:5000/'


while True:
    print("Attempting access of home page") 
    r = requests.get(url_server_home)
    print(r.content)

    '''
    print("Attempting addition of user")
    r = requests.delete(url)
    print(r.status_code)
    print(r.text)

    while r.status_code != 200:
        print("Attempting clean_up server")
        r =requests.delete(url)
        print(r)
    '''
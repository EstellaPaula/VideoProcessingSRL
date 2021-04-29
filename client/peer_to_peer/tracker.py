import requests

class Tracker():
    """
        Required fields: hostname, port
        Optional fields: none

        A class meant to interface the interaction with the tracker
    """

    home=""

    def __init__(self, hostname, port):
        self.home = "http://{hostname}:{port}/".format(hostname = hostname,
         port = port)
        return
    
    def get_users(self):
        """
            Required fields: none
            Optional fields: none
            Returns: list of users

            Return a list of users
        """

        print("\nGet a list of users", flush=True)
        url = self.home + "api/user"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            print("Get users HTTP error:", r.status_code)
            return r.json()
    
    def register_user(self, username, password):
        """
            Required fields: username, password
            Optional fields: none
            Returns: error code or nothing

            Registers an user with username and password
        """

        print("\nRegister user", username, flush=True)
        url = self.home + "api/register"
        r = requests.post(url, json={"username":username, "password":password})
        if r.status_code == 200:
            return r.json()
        else:
            print("Register HTTP error:", r.status_code)
            return r.json()

    def log_in(self, username, password):
        """
            Required fields: username, password
            Optional fields: none
            Returns: error code or nothing

            Logs in user and returns token
        """

        print("\nLog in user", username, flush=True)
        url = self.home + "api/login"
        r = requests.get(url, auth=(username, password))
        if r.status_code == 200:
            token = r.json()["token"]
            return token
        else:
            print("Log in HTTP error:", r.status_code)
            return r.json()

    def 
    


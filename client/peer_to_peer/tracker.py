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
            Returns: request code, request output

            Return a list of users
        """

        print("\nGet a list of users", flush=True)
        url = self.home + "api/user"
        r = requests.get(url)
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Get users HTTP error:", r.status_code)
            return r.status_code, r.json()
    
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
            return r.status_code, r.json()
        else:
            print("Register HTTP error:", r.status_code)
            return r.status_code, r.json()

    def log_in(self, username, password):
        """
            Required fields: username, password
            Optional fields: none
            Returns: error code or token

            Logs in user and returns token
        """

        print("\nLog in user", username, flush=True)
        url = self.home + "api/login"
        r = requests.get(url, auth=(username, password))
        if r.status_code == 200:
            token = r.json()["token"]
            return r.status_code, token
        else:
            print("Log in HTTP error:", r.status_code)
            return r.status_code, r.json()

    def get_boss_list(self):
        """
            Required fields: none
            Optional fields: none
            Returns: error code or nothing

            Gets list of bosses
        """

        print("\nGet a list of bosses", flush=True)
        url = self.home + "api/boss"
        r = requests.get(url)
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Get boss list HTTP error:", r.status_code)
            return r.status_code, r.json()
    
    def get_worker_list(self):
        """
            Required fields: none
            Optional fields: none
            Returns: error code or nothing

            Gets list of workers
        """
        print("\nGet a list of workers", flush=True)
        url = self.home + "api/worker"
        r = requests.get(url)
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Get worker list HTTP error:", r.status_code)
            return r.status_code, r.json()


    def register_boss_session(self, hostname, token):
        """
            Required fields: hostname, token
            Optional fields: none
            Returns: boss instance id or error_code

            Registers a boss session
        """

        print("\nRegister a boss session", flush=True)
        url = self.home + "api/register/boss"
        r = requests.post(url, headers={"Content-Type":"application/json", "x-access-tokens":token}, json={"ip_address":hostname})
        if r.status_code == 200:
            boss_id = r.json()["id"]
            return r.status_code, boss_id
        else:
            print("Boss register HTTP error:", r.status_code)
            return r.status_code, r.json()
    
    def register_worker_session(self, hostname, msg_port, file_port, speeds, token):
        """
            Required fields: hostname, msg_port, file_port, speeds, token
            Optional fields: none
            Returns: worker instance id or error_code

            Registers a worker session
        """

        print("\nRegister a worker session", flush=True)
        url = self.home + "api/register/worker"
        r = requests.post(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"ip_address":hostname, "port_msg":msg_port, "port_file":file_port, "pp_x265":speeds["x265"],
         "pp_vp9":speeds["vp9"], "pp_av1":speeds["av1"]})
        if r.status_code == 200:
            worker_id = r.json()["id"]
            return r.status_code, worker_id
        else:
            print("Worker register HTTP error:", r.status_code)
            return r.status_code, r.json()

    def update_x265_speed(self, worker_id, new_speed, token):
        """
            Required fields: worker_id, new_speed, token
            Optional fields: none
            Returns: nothing or error_code

            Updates x265 speed
        """

        print("\nUpdate x265 speed", flush=True)
        url = self.home + "api/worker/pp_x265"
        r = requests.put(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":worker_id, "pp_x265":new_speed})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Worker x265 speed update HTTP error:", r.status_code)
            return r.status_code, r.json()
    
    def update_vp9_speed(self, worker_id, new_speed, token):
        """
            Required fields: worker_id, new_speed, token
            Optional fields: none
            Returns: nothing or error_code

            Updates vp9 speed
        """

        print("\nUpdate vp9 speed", flush=True)
        url = self.home + "api/worker/pp_vp9"
        r = requests.put(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":worker_id, "pp_vp9":new_speed})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Worker vp9 speed update HTTP error:", r.status_code)
            return r.status_code, r.json()

    def update_av1_speed(self, worker_id, new_speed, token):
        """
            Required fields: worker_id, new_speed, token
            Optional fields: none
            Returns: nothing or error_code

            Updates av1 speed
        """

        print("\nUpdate av1 speed", flush=True)
        url = self.home + "api/worker/pp_av1"
        r = requests.put(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":worker_id, "pp_av1":new_speed})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Worker av1 speed update HTTP error:", r.status_code)
            return r.status_code, r.json()

    def update_speed(self, worker_id, speeds, token):
        """
            Required fields: worker_id, speeds
            Optional fields: none
            Returns: nothing or error_code

            Updates speeds
        """

        for codec in speeds:
            new_speed = speeds[codec]
            if codec == "x265":
                self.update_x265_speed(worker_id, new_speed, token)
            elif codec == "vp9":
                self.update_vp9_speed(worker_id, new_speed, token)
            else:
                self.update_av1_speed(worker_id, new_speed, token)
        return

    def get_workers(self, boss_id, token):
        """
            Required fields: boss_id, token
            Optional fields: none
            Returns: list of workers

            Get a list of workers
        """

        print("\nGet workers", flush=True)
        url = self.home + "api/boss/job"
        r = requests.get(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":boss_id})
        if r.status_code == 200:
            workers = r.json()
            return r.status_code, workers
        else:
            print("Get workers HTTP error:", r.status_code)
            return r.status_code, r.json()

    def boss_finish(self, boss_id, token):
        """
            Required fields: boss_id, token
            Optional fields: none
            Returns: nothing

            Notifies tracker that boss finished job
        """

        print("\nBoss finish", flush=True)
        url = self.home + "api/boss/status"
        r = requests.put(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":boss_id})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Boss finish HTTP error:", r.status_code)
            return r.status_code, ""
    
    def worker_finish(self, worker_id, token):
        """
            Required fields: worker_id, token
            Optional fields: none
            Returns: nothing

            Notifies tracker that boss finished job
        """

        print("\nWorker finish", flush=True)
        url = self.home + "api/worker/status"
        r = requests.put(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":worker_id})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Worker finish HTTP error:", r.status_code)
            return r.status_code, r.json()
    
    def get_worker_owner(self, worker_id, token):
        """
            Required fields: worker_id, token
            Optional fields: none
            Returns: nothing

            Get a worker's legitimate boss
        """

        print("\nGet worker owner", flush=True)
        url = self.home + "api/worker/owner"
        r = requests.get(url, headers={"Content-Type":"application/json", "x-access-tokens":token},
         json={"id":worker_id})
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            print("Worker owner HTTP error:", r.status_code)
            return r.status_code, ""


    

    


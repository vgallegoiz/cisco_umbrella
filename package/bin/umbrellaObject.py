import requests
from typing import List
from datetime import datetime

class Umbrella():
    def __init__(self, client_id, client_secret, url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.url = url
        self.headers = {
            "Accept": "application/json"
        }

    def get_auth_token(self):
        self.headers["Content-Type"] = "application/json"
        response = requests.post(
            'https://api.sse.cisco.com/auth/v2/token',
            auth=(self.client_id, self.client_secret),
            headers=self.headers,
            data={'grant_type': 'client_credentials'}, 
            verify=False
        )
        auth_data = response.json()
        self.headers["Authorization"] = f"Bearer {auth_data['access_token']}"
        self.headers["Content-Type"] = "application/json"

    def get_report_logs_all(self, start_time, end_time):
        response = requests.get(url=f"{self.url}/reports/v2/activity?to={end_time}&from={start_time}&limit=5000", 
            headers=self.headers, verify=False)
        return response

    def get_report_logs_allowed(self, start_time, end_time):
        response = requests.get(url=f"{self.url}/reports/v2/activity?to={end_time}&from={start_time}&limit=5000&verdict=allowed", 
            headers=self.headers, verify=False)
        return response

    def get_report_logs_blocked(self, start_time, end_time):
        response = requests.get(url=f"{self.url}/reports/v2/activity?to={end_time}&from={start_time}&limit=5000&verdict=blocked", 
            headers=self.headers, verify=False)
        return response
    
    def get_report_logs_proxied(self, start_time, end_time):
        response = requests.get(url=f"{self.url}/reports/v2/activity?to={end_time}&from={start_time}&limit=5000&verdict=proxied", 
            headers=self.headers, verify=False)
        return response
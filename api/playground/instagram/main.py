from pprint import pprint

import requests

url = "https://instagram85.p.rapidapi.com/account/12638820603/followings"

headers = {
    'x-rapidapi-host': "instagram85.p.rapidapi.com",
    'x-rapidapi-key': "72e6866dc0mshf8a356cd1a2e562p1490fcjsn0e4810039982"
    }

response = requests.request("GET", url, headers=headers)

pprint(response.text)

if __name__ == '__main__':
    pass

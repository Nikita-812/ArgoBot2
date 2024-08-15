import requests

headers = {
    'accept': 'application/json',
    'X-authUserNumber-Header': '3316197',
}

response = requests.get('https://192.168.0.15/DailyNews/Participant/3316197', headers=headers, verify=False)

print(response.json())

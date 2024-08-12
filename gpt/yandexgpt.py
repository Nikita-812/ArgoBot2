import requests
import json
import os


def gpt(auth_headers):

    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

    with open('../bot/body.json', 'r', encoding='utf-8') as f:
        data = json.dumps(json.load(f))
    resp = requests.post(url, headers=auth_headers, data=data)

    if resp.status_code != 200:
        raise RuntimeError(
            'Invalid response received: code: {}, message: {}'.format(
                {resp.status_code}, {resp.text}
            )
        )
    return resp

if __name__ == "__main__":
    api_key = os.environ['API_KEY']
    headers = {
        'Authorization': 'Api-Key {}'.format(api_key),
    }
    res = gpt(headers).json()
    res = res['result']
    res = res['alternatives']
    res = res[0]
    print(res['message']["text"])
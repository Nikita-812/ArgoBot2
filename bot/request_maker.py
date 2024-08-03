import json

def request_maker(users_answer) -> dict:
    with open('body.json', 'r+') as f:
        data = json.load(f)
    with open('body.json', 'w') as f:
        data['messages'][-1]['text'] = users_answer
        json.dump(data, f)


if __name__ == '__main__':
    st = 'fuck me'
    request_maker(st)
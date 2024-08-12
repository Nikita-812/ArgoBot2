import json
def request_maker(users_answer) -> dict:
    with open('../bot/body.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
    with open('../bot/body.json', 'w', encoding='utf-8') as f:
        data['messages'][-1]['text'] = users_answer
        json.dump(data, f)

if __name__ == '__main__':
    st = 'fuck me'
    request_maker(st)

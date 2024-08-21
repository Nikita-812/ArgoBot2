import requests
import time


def create_participant_data(parent_id=2147483647, name='', status='new', bitrix_id=2147483647, email='',
                            mobile_phone='', birth_date='',
                            registrator_id=0,
                            country_id=0, region_id=0, city_id=0):
    current_time = time.localtime()
    formatted_date = time.strftime('%Y-%m-%d', current_time)
    json_data = {
        'parentId': parent_id,
        'name': name,
        'status': status,
        'bitrixId': bitrix_id,
        'email': email,
        'mobilePhone': mobile_phone,
        'birthDate': birth_date,
        'registratorId': registrator_id,
        'countryId': country_id,
        'regionId': region_id,
        'cityId': city_id,
        'registrationDate': formatted_date,
    }
    return json_data


def post_new_participant(data):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        'https://192.168.0.15/DailyNews/Participant',
        headers=headers,
        json=data,
        verify=False
    )
    return response.status_code, response.json()


# Example usage:
data = create_participant_data(
    parent_id=1,
    name='Никита',
    status='New',
    bitrix_id=1,
    email='nikitospashynin@gmail.com',
    mobile_phone='89231416154',
    birth_date='2005-08-19',
    registrator_id=0,
    country_id=0,
    region_id=0,
    city_id=0
)

if __name__ == '__main__':
    status_code, response_json = post_new_participant(data)
    print(response_json)

from aiogram import types
from email_validator import validate_email, EmailNotValidError


def email_validation_filter(message: types.Message) -> dict[str, str] | None:
    try:
        email = validate_email(message.text)
    except EmailNotValidError as e:
        return None
    return {'email': email.normalized}


def id_validation_filter(s: str):
    s = s.strip().split()
    for i in s:
        if i.isdigit():
            return int(i)
    return 'Ошибка, повторите попытку'

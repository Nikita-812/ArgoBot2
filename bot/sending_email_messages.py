import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def generate_password(length=6):
    return ''.join(random.choices('0123456789', k=length))


def send_email_password(recipient_email, password):
    sender_email = "pasininnikita1@gmail.com"
    sender_password = "smvc sofj wshh dtar"
    subject = "Ваш новый пароль"
    body = f"Ваш сгенерированный пароль: {password}"

    # Создание MIME-сообщения
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Добавление текста сообщения
    msg.attach(MIMEText(body, 'plain'))

    # Настройка SMTP-сервера
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)

    # Отправка письма
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()


if __name__ == "__main__":
    # Пример использования
    recipient = "nikitospashynin@gmail.com"
    password = generate_password()
    send_email_password(recipient, password)
    print(f"Пароль отправлен на {recipient}")

from flask import request


def get_ip_address():
    """
    Получает IP-адрес клиента, учитывая прокси-серверы (X-Forwarded-For).
    """
    # X-Forwarded-For обычно используется, когда приложение находится за прокси/балансировщиком.
    # Он может содержать список IP-адресов через запятую, где первый - реальный клиентский IP.
    if 'X-Forwarded-For' in request.headers:
        # Берём первый IP из списка (если их несколько)
        ip_address = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        # Если нет X-Forwarded-For, используем remote_addr (прямой IP клиента или прокси)
        ip_address = request.remote_addr
    return ip_address

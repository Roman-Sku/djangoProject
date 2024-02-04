
from datetime import datetime


class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        log_string = datetime.now().strftime('%d:%m:%Y %H:%M') + " | " + str(
            request.user) + " | " + "URL=" + request.get_full_path() + "\n"

        with open("usersActivity.log", "a", encoding="utf-8") as file:
            file.write(log_string)

        return response

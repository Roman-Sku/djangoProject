
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render

from .models import Note


class HistoryService:

    def __init__(self, request: WSGIRequest):
        self._session = request.session

        # Если у сессии пользователя нет ключа `favorites`, то мы его создаем
        self._session.setdefault("history", [])

        # Если вдруг это был не список, то задаем его явно.
        if not isinstance(self._session["history"], list):
            self._session["history"] = []

    def add_to_history(self, note: Note) -> None:
        self._session["history"].append(str(note.uuid))
        self.remove_from_history(note.uuid)
        self._session.save()

    def remove_from_history(self, note_uuid: int) -> None:
        history: list = self._session["history"]
        if len(history) > 20:
            history.pop(0)
        if note_uuid in history:
            history.remove(note_uuid)

    @property
    def history_ids(self) -> list[int]:
        return self._session["history"]


def favorite_service_preprocessor(request: WSGIRequest) -> dict[str, list[int]]:
    return {"history_ids": HistoryService(request).history_ids}

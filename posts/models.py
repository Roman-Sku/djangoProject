import uuid

from django.db import models


class Note(models.Model):
    # Стандартный ID для каждой таблицы можно не указывать, Django по умолчанию это добавит.

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    mod_time = models.DateTimeField(default=None, null=True)
    # auto_now_add=True автоматически добавляет текущую дату и время.

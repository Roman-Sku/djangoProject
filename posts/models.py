import pathlib
import uuid

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=11)

    class Meta:
        db_table = 'users'


def upload_to(instance: "Note", filename: str) -> str:
    """Путь для файла относительно корня медиа хранилища."""
    return f"{instance.uuid}/{filename}"


class Note(models.Model):
    # Стандартный ID для каждой таблицы можно не указывать, Django по умолчанию это добавит.

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.FileField(upload_to=upload_to, null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    objects = models.Manager()  # Он подключается к базе.


    class Meta:
        # db_table = 'notes'  # Название таблицы в базе.
        ordering = ['-created_at']  # Дефис это означает DESC сортировку (обратную).


@receiver(post_delete, sender=Note)
def after_delete_note(sender, instance: Note, **kwargs):
    if instance.image:
        note_media_folder: pathlib.Path = (settings.MEDIA_ROOT / str(instance.uuid))

        for file in note_media_folder.glob("*"):
            file.unlink(missing_ok=True)
        note_media_folder.unlink(missing_ok=True)

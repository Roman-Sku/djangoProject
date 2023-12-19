from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone

from .models import Note


def home_page_view(request: WSGIRequest):
    # Обязательно! каждая функция view должна принимать первым параметром request.
    all_notes = Note.objects.all()  # Получение всех записей из таблицы этой модели.
    context: dict = {
        "notes": all_notes
    }
    return render(request, "home.html", context)


def create_note_view(request: WSGIRequest):
    if request.method == "POST":
        note = Note.objects.create(
            title=request.POST["title"],
            content=request.POST["content"],
        )
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    # Вернется только, если метод не POST.
    return render(request, "create_form.html")


def show_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)  # Получение только ОДНОЙ записи.

    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404

    return render(request, "note.html", {"note": note})


def general_info_view(request: WSGIRequest):
    return render(request, "info.html")


def redact_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)

    except Note.DoesNotExist:
        raise Http404

    if request.method == "POST":
        note.content = request.POST["content"]
        note.title = request.POST["title"]
        note.mod_time = timezone.now()
        note.save()
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    return render(request, "redact-note.html", {"note": note})


def delete_note_view(request: WSGIRequest, note_uuid):
    try:
        Note.objects.get(uuid=note_uuid)

    except Note.DoesNotExist:
        raise Http404

    if request.method == "POST":
        Note.objects.get(uuid=note_uuid).delete()
        return HttpResponseRedirect(reverse('home'))

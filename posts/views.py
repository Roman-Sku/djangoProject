import os

from django.utils import timezone
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.decorators import login_required

from project import settings
from .models import Note, User


def home_page_view(request: WSGIRequest):
    # Обязательно! каждая функция view должна принимать первым параметром request.
    all_notes = Note.objects.all()  # Получение всех записей из таблицы этой модели.
    context: dict = {
        "notes": all_notes
    }
    return render(request, "home.html", context)


def filter_notes_view(request: WSGIRequest):
    """
    Фильтруем записи по запросу пользователя.
    HTTP метод - GET.
    Обрабатывает URL вида: /filter/?search=<text>
    """

    search: str = request.GET.get("search", "")  # `get` - получение по ключу. Если такого нет, то - "",

    # Если строка поиска не пустая, то фильтруем записи по ней.
    if search:
        # ❗️Нет обращения к базе❗️
        # Через запятую запросы формируются c ❗️AND❗️
        # notes_queryset = Note.objects.filter(title__icontains=search, content__icontains=search)
        # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
        # FROM "posts_note" WHERE (
        # "posts_note"."title" LIKE %search% ESCAPE '\' AND "posts_note"."content" LIKE %search% ESCAPE '\')

        # ❗️Все импорты сверху файла❗️
        # from django.db.models import Q
        # Оператор - `|` Означает `ИЛИ`.
        # Оператор - `&` Означает `И`.
        notes_queryset = Note.objects.filter(Q(title__icontains=search) | Q(content__icontains=search))

    else:
        # Если нет строки поиска.
        notes_queryset = Note.objects.all()  # Получение всех записей из модели.

    notes_queryset = notes_queryset.order_by("-created_at")  # ❗️Нет обращения к базе❗️

    # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
    # FROM "posts_note" WHERE
    # ("posts_note"."title" LIKE %python% ESCAPE '\' OR "posts_note"."content" LIKE %python% ESCAPE '\')
    # ORDER BY "posts_note"."created_at" DESC

    print(notes_queryset.query)

    context: dict = {
        "notes": notes_queryset,
        "search_value_form": search,
    }
    return render(request, "home.html", context)


@login_required
def create_note_view(request: WSGIRequest):
    if request.method == "POST":
        print(request.FILES)
        note = Note.objects.create(
            title=request.POST["title"],
            content=request.POST["content"],
            user=request.user,
            image=request.FILES.get("noteImage")
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

    if request.user != note.user:
        return HttpResponseForbidden("You do not have permission to")

    if request.method == "POST":
            note.content = request.POST["content"]
            note.title = request.POST["title"]
            note.mod_time = timezone.now()
            note.image = request.FILES.get("noteImage")
            note.save()
            return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    return render(request, "redact-note.html", {"note": note})


def delete_note_view(request: WSGIRequest, note_uuid: str):
    note = Note.objects.get(uuid=note_uuid)
    if request.user != note.user:
        return HttpResponseForbidden("You do not have permission to delete this note")
    if request.method == "POST":
        note.delete()
    return HttpResponseRedirect(reverse("home"))


def register(request: WSGIRequest):
    if request.method != "POST":
        return render(request, "registration/register.html")
    print(request.POST)
    if not request.POST.get("username") or not request.POST.get("email") or not request.POST.get("password1"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Укажите все поля!"}
        )
    print(User.objects.filter(
            Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ))
    # Если уже есть такой пользователь с username или email.
    if User.objects.filter(
            Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ).count() > 0:
        return render(
            request,
            "registration/register.html",
            {"errors": "Если уже есть такой пользователь с username или email"}
        )

    # Сравниваем два пароля!
    if request.POST.get("password1") != request.POST.get("password2"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Пароли не совпадают"}
        )

    # Создадим учетную запись пользователя.
    # Пароль надо хранить в БД в шифрованном виде.
    User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password1"]
    )
    return HttpResponseRedirect(reverse('home'))


def notes_by_user_view(request: WSGIRequest, user_username: str):
    user = User.objects.get(username=user_username)
    queryset = Note.objects.filter(user=user)
    return render(request, "user_posts_list.html", {"notes": queryset, "username": user_username})


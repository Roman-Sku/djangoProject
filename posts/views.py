import os

from django.utils import timezone
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import Q, Case, When
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from .email import ConfirmUserRegisterEmailSender, ConfirmUserResetPasswordEmailSender
from .forms import ResetForm, RegisterForm
from .history_service import HistoryService

from project import settings
from .models import Note, User, Tag


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

    service = HistoryService(request)
    service.add_to_history(note)
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
        Note.objects.get(uuid=note_uuid).delete()
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
    user = User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password1"]
    )

    ConfirmUserRegisterEmailSender(request, user).send_mail()

    if user is not None:
        return HttpResponseRedirect(reverse("login"))

    return HttpResponseRedirect(reverse('home'))


def register_view(request: WSGIRequest):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                is_active=False,
            )

            ConfirmUserRegisterEmailSender(request, user).send_mail()

            return HttpResponseRedirect(reverse("login"))

    return render(request, 'registration/register-form.html', {'form': form})


def confirm_register_view(request: WSGIRequest, uidb64: str, token: str):
    username = force_str(urlsafe_base64_decode(uidb64))

    user = get_object_or_404(User, username=username)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        return HttpResponseRedirect(reverse("login"))

    return render(request, "registration/invalid-email-confirm.html", {"username": user.username})


def notes_by_user_view(request: WSGIRequest, user_username: str):
    user = User.objects.get(username=user_username)
    queryset = Note.objects.filter(user=user)
    return render(request, "user_posts_list.html", {"notes": queryset, "username": user_username})


def profile_view(request: WSGIRequest, username):
    if request.method == 'POST':
        user = User.objects.get(username=username)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        user.save()
        return HttpResponseRedirect(reverse("home",))
    user = User.objects.get(username=username)
    tags_queryset = Tag.objects.filter(notes__user=user).distinct()

    return render(request, 'profile.html', {'tags': tags_queryset})


class ListHistoryView(View):
    def get(self, request: WSGIRequest):
        """
        Метод `get` вызывается автоматический, когда HTTP метод запроса является `GET`.
        """
        history_service = HistoryService(request)
        ids = history_service.history_ids[::-1]
        queryset = Note.objects.filter(uuid__in=ids)
        return render(request, "home.html", {"notes": queryset})


def reset_view(request: WSGIRequest):
    form = ResetForm()

    if request.method == 'POST':

        username = request.POST.get("username")

        form = ResetForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, username=username)
            ConfirmUserResetPasswordEmailSender(request, user).send_mail()
            # Подтверждение по email.
            return HttpResponseRedirect(reverse("login"))

    return render(request, 'registration/reset-form.html', {'form': form})


def confirm_reset_view(request: WSGIRequest, uidb64: str, token: str):
    username = force_str(urlsafe_base64_decode(uidb64))

    user = get_object_or_404(User, username=username)
    if default_token_generator.check_token(user, token):
        new_password = request.POST.get("password1")
        user.set_password(new_password)
        user.save()
        return HttpResponseRedirect(reverse("login"))

    return render(request, "registration/invalid-email-confirm.html", {"username": user.username})

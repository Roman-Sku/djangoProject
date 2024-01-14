"""
URL configuration for Lesson21_Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import serve
from django.conf import settings

from posts import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include("django.contrib.auth.urls")),
    path('accounts/register', views.register, name="register"),

    path("filter", views.filter_notes_view, name="filter-notes"),
    path("", views.home_page_view, name="home"),
    path("create", views.create_note_view, name="create-note"),
    path("post/<note_uuid>", views.show_note_view, name="show-note"),
    path("us", views.general_info_view, name="general_info"),
    path("redact/<note_uuid>", views.redact_note_view, name="redact-note"),
    path("delete/<note_uuid>", views.delete_note_view, name="delete-note"),
    path("user/<user_username>/posts", views.notes_by_user_view, name="notes_by_user"),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

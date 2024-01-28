from django.urls import path

from . import views

# /api/
app_name = 'posts:api'

urlpatterns = [

    path("posts/", views.NoteListCreateAPIView.as_view(), name="note-list-create"),
    path("posts/<uuid:pk>", views.NoteDetailAPIView.as_view(), name="note"),
    path("posts/image", views.UploadImageAPIView.as_view(), name="note-image-upload"),
    path("posts/tags", views.TagListCreateApiView.as_view(), name="tag")

]

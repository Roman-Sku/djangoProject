from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.serializers import ModelSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import uuid

from posts.api.permissions import IsOwnerOrReadOnly
from posts.api.serializers import ImageSerializer, NoteSerializer, NoteListSerializer, \
    TagListSerializer, NoteDetailSerializer, NoteCreateSerializer

from posts.models import Note, Tag


class NoteListCreateAPIView(ListCreateAPIView):
    queryset = Note.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]  # Реагирует на (query) параметр `search`
    search_fields = ['@title', '@content']  # Используем полнотекстовый поиск Postgres
    ordering_fields = ["created_at", "mode_time", "user_username"]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NoteSerializer
        return NoteListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    permission_classes = [IsOwnerOrReadOnly]


class NoteListCreateGenericAPIView(GenericAPIView):
    queryset = Note.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NoteSerializer
        return NoteListSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer: ModelSerializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer: ModelSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(user=self.request.user)
        serializer = NoteDetailSerializer(instance=note)
        return Response(serializer.data, status=201)


class DetailNoteGenericAPIView(GenericAPIView):

    queryset = Note.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NoteDetailSerializer
        return NoteCreateSerializer

    def get(self, request, pk: uuid, *args, **kwargs):
        note = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(instance=note)
        return Response(serializer.data)

    def put(self, request, pk: uuid, *args, **kwargs):
        note = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(data=request.data, instance=note)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk: uuid, *args, **kwargs):
        note = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(data=request.data, instance=note, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk: uuid, *args, **kwargs):
        note = get_object_or_404(self.get_queryset(), pk=pk)
        note.delete()
        return Response(status=204)


class UploadImageAPIView(GenericAPIView):
    serializer_class = ImageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        image: InMemoryUploadedFile = serializer.validated_data["image"]
        with open(f"{settings.MEDIA_ROOT}/images/{image.name}", "bw") as image_file:
            image_file.write(image.read())
        return Response({"name": image.name, "url": "images/" + image.name})


class TagListCreateApiView(ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagListSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticatedOrReadOnly]

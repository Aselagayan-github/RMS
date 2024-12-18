from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),  # Map the root URL to the main page
]

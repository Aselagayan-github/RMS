from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),  # Map the root URL to the main page
    path('menu/', views.menu, name='menu'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('admind/', views.admin_view, name='admind'),  # Define this view
    path('customer/', views.customer_view, name='customer'),  # Define this view
]

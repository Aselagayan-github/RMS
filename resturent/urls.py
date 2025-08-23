from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),  # Map the root URL to the main page
    path('menu/', views.menu, name='menu'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('admindashboard/', views.admin_view, name='admindashboard'),  # Define this view
    path('customerdashboard/', views.customer_view, name='customerdashboard'),  # Define this view
    path('usermanagement/', views.usermanage_view, name='usermanagement'),
    path('save_order/', views.save_order, name='save_order'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('delete_order/<str:order_id>/', views.delete_order, name='delete_order'),

]

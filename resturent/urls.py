from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),
    path('menu/', views.menu, name='menu'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('admindashboard/', views.admin_view, name='admindashboard'),
    path('customerdashboard/', views.customer_view, name='customerdashboard'),
    path('usermanagement/', views.usermanage_view, name='usermanagement'),
    path('order_management/', views.order_management_view, name='order_management'),  # Added for order management page
    path('api/orders/', views.orders_api, name='orders_api'),  # API for GET/POST orders
    path('api/orders/<str:order_id>/', views.order_detail_api, name='order_detail_api'),  # API for GET/PUT/DELETE specific order
    path('api/order_statistics/', views.get_order_statistics, name='get_order_statistics'),  # Added for stats
    path('api/orders/<str:order_id>/status/', views.update_order_status, name='update_order_status'),  # Added for status update
]
# resturent/urls.py
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
    path('order_management/', views.order_management_view, name='order_management'),
    path('api/orders/', views.orders_api, name='orders_api'),
    path('api/orders/<str:order_id>/', views.order_detail_api, name='order_detail_api'),
    path('api/order_statistics/', views.get_order_statistics, name='get_order_statistics'),
    path('api/orders/<str:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('api/bookings/', views.bookings_api, name='bookings_api'),
    path('api/bookings/<str:booking_id>/', views.booking_detail_api, name='booking_detail_api'),
    path('api/menu-items/', views.menu_items_api, name='menu_items_api'),
    path('api/menu-items/<str:item_id>/', views.menu_item_detail_api, name='menu_item_detail_api'),
    path('api/deliveries/', views.deliveries_api, name='deliveries_api'),
    path('api/deliveries/<str:delivery_id>/', views.delivery_detail_api, name='delivery_detail_api'),
    path('api/invoices/', views.invoices_api, name='invoices_api'),
    path('api/invoices/<str:invoice_id>/', views.invoice_detail_api, name='invoice_detail_api'),
    path('api/invoices/<str:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path('api/sales_report/', views.sales_report, name='sales_report'),
    path('api/customer_analytics/', views.customer_analytics, name='customer_analytics'),
]
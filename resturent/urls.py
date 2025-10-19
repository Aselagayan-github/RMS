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
<<<<<<< HEAD
    path('order_management/', views.order_management_view, name='order_management'),
    path('api/orders/', views.orders_api, name='orders_api'),
    path('api/orders/<str:order_id>/', views.order_detail_api, name='order_detail_api'),
    path('api/order_statistics/', views.get_order_statistics, name='get_order_statistics'),
    path('api/orders/<str:order_id>/status/', views.update_order_status, name='update_order_status'),
]
=======
    path('save_order/', views.save_order, name='save_order'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('delete_order/<str:order_id>/', views.delete_order, name='delete_order'),

]
>>>>>>> dc3a1344b186dbf4b22f6d3fb00222429da98b8e

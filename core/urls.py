from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    
    path('skincolor/', views.skincolor, name='skincolor'),
    path('facephoto_delete/<int:id>/', views.facephoto_delete, name='facephoto_delete'),

    path('clothing/', views.clothing, name='clothing'),
    path('clothing_list/<int:id>/delete/', views.clothing_delete, name='clothing_delete'),

    path('bulk_import_clothing/', views.bulk_import_clothing, name='bulk_import_clothing'),

    # recommender
    path('based_on_skintone/', views.based_on_skintone, name='based_on_skintone'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sort-table/', views.sort_table, name='sort_table'),
]


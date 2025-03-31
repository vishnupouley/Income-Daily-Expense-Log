from django.urls import path
from month_log import views

urlpatterns = [
    path('', views.index, name='index'),
]

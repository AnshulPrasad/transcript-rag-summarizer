from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ask/', views.ask, name='ask'),
    path('history/', views.history, name='history'),
    path('clear-history/', views.clear_history, name='clear_history'),
]
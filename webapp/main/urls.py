from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    #lo comento porque ya no hay un def results en views.py
   # path('results', views.results, name='results'),
]
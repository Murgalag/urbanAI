from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('population-heatmap/', views.get_population_heatmap, name='population_heatmap'),
    path('suggest-location/', views.suggest_building_location, name='suggest_building_location'),
    path('history/', views.get_building_history, name='building_history'),
    path('schools/', views.get_schools, name='get_schools'),
    path('districts/', views.get_districts, name='get_districts'), # НОВАЯ СТРОКА
]
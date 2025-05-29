from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Существующие API
    path('population-heatmap/', views.get_population_heatmap, name='population_heatmap'),
    path('suggest-location/', views.suggest_building_location, name='suggest_building_location'),
    path('history/', views.get_building_history, name='building_history'),
    path('schools/', views.get_schools, name='get_schools'),
    path('districts/', views.get_districts, name='get_districts'),
    
    # НОВЫЕ API для Google Maps
    path('enhanced-heatmap/', views.get_enhanced_heatmap_data, name='enhanced_heatmap'),
    path('residential-buildings/', views.get_residential_buildings, name='residential_buildings'),
    path('commercial-places/', views.get_commercial_places, name='commercial_places'),
    path('enhanced-school-info/', views.get_enhanced_school_info, name='enhanced_school_info'),
    path('analyze/', views.analyze_districts, name='analyze_districts'),
]

urlpatterns += [
    # Gemini AI анализ
    path('ai/analyze-scenario/', views.analyze_school_scenario, name='analyze_scenario'),
    path('ai/analyze-district/', views.analyze_bishkek_district, name='analyze_district'),
    path('ai/districts/', views.get_bishkek_districts, name='bishkek_districts'),
    path('ai/scenario/<int:scenario_id>/', views.get_scenario_data, name='scenario_data'),
]

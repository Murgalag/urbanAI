from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import OpenStreetMapService, GeminiService, PopulationService
from .models import BuildingRequest, PopulationData
from .enhanced_gemini_service import EnhancedGeminiService
from .ai.gemini_service import GeminiAnalysisService
import json
import random

def index(request):
    """Главная страница"""
    return render(request, 'building_optimizer/index.html')

@csrf_exempt
@api_view(['GET'])
def get_population_heatmap(request):
    """API для получения тепловой карты населения"""
    city = request.GET.get('city', 'Бишкек')
    
    try:
        population_data_with_geometry = PopulationService.get_or_create_population_data(city)
        
        return Response({
            'success': True,
            'city': city,
            'districts': population_data_with_geometry
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
def get_enhanced_heatmap_data(request):
    """НОВОЕ API: Получить расширенные данные для тепловой карты Google Maps"""
    city = request.GET.get('city', 'Бишкек')
    
    try:
        osm_service = OpenStreetMapService()
        
        # Получаем все типы данных
        districts_data = osm_service.get_districts_in_city(city)
        residential_data = osm_service.get_residential_buildings_in_city(city)
        commercial_data = osm_service.get_commercial_places_in_city(city)
        schools_data = osm_service.get_schools_in_city(city)
        
        # Генерируем градиентные данные для тепловой карты
        heatmap_data = osm_service.generate_gradient_heatmap_data(
            districts_data, residential_data, commercial_data
        )
        
        return Response({
            'success': True,
            'city': city,
            'districts': districts_data,
            'residential_buildings': residential_data,
            'commercial_places': commercial_data,
            'schools': schools_data,
            'heatmap_data': heatmap_data,
            'stats': {
                'districts_count': len(districts_data),
                'residential_count': len(residential_data),
                'commercial_count': len(commercial_data),
                'schools_count': len(schools_data),
                'heatmap_points': len(heatmap_data)
            }
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
def suggest_building_location(request):
    """API для предложения оптимального места размещения здания"""
    try:
        data = json.loads(request.body)
        building_type = data.get('building_type')
        city = data.get('city', 'Бишкек')
        
        if not building_type:
            return Response({
                'success': False,
                'error': 'Не указан тип здания'
            }, status=400)
        
        population_data = PopulationService.get_or_create_population_data(city)
        
        districts_for_ai = []
        for district in population_data:
            districts_for_ai.append({
                'name': district['district_name'],
                'lat': district['lat'],
                'lng': district['lng'],
                'population_density': district['population_density']
            })
        
        gemini_service = GeminiService()
        suggestion = gemini_service.get_building_suggestion(
            building_type, city, districts_for_ai
        )
        
        if not suggestion:
            return Response({
                'success': False,
                'error': 'Не удалось получить рекомендацию'
            }, status=500)
        
        building_request = BuildingRequest.objects.create(
            building_type=building_type,
            city=city,
            suggested_lat=suggestion['coordinates']['lat'],
            suggested_lng=suggestion['coordinates']['lng'],
            population_density=0,
            confidence_score=suggestion['confidence'],
            reasoning=suggestion['reasoning']
        )
        
        return Response({
            'success': True,
            'suggestion': {
                'district': suggestion['district'],
                'coordinates': {
                    'lat': suggestion['coordinates']['lat'],
                    'lng': suggestion['coordinates']['lng']
                },
                'confidence': suggestion['confidence'],
                'reasoning': suggestion['reasoning'],
                'building_type': building_type,
                'city': city
            }
        })
    
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
def analyze_districts(request):
    """НОВОЕ API: Анализ выбранных районов"""
    try:
        data = json.loads(request.body)
        selected_districts = data.get('districts', [])
        
        if not selected_districts:
            return Response({
                'success': False,
                'error': 'Не выбраны районы для анализа'
            }, status=400)
        
        # Получаем данные о районах
        osm_service = OpenStreetMapService()
        districts_data = osm_service.get_districts_in_city('Бишкек')
        schools_data = osm_service.get_schools_in_city('Бишкек')
        
        # Фильтруем только выбранные районы
        district_name_mapping = {
            'oktyabrsky': 'Октябрьский район',
            'pervomaisky': 'Первомайский район',
            'leninsky': 'Ленинский район',
            'sverdlovsky': 'Свердловский район'
        }
        
        selected_district_names = [district_name_mapping.get(d, d) for d in selected_districts]
        filtered_districts = [d for d in districts_data if d['name'] in selected_district_names]
        
        # Генерируем результаты анализа
        analysis_results = {
            'statistics': {
                'totalFacilities': len(schools_data),
                'avgDistance': round(random.uniform(1.2, 3.5), 1),
                'coveragePercent': random.randint(65, 95),
                'populationServed': sum([d['population_density'] for d in filtered_districts]) * random.randint(1, 3)
            },
            'charts': {
                'district': [random.randint(15, 35) for _ in range(4)],
                'accessibility': [random.randint(5, 25) for _ in range(5)],
                'time': [random.randint(45, 95) for _ in range(7)]
            },
            'districts_analyzed': len(filtered_districts),
            'schools_in_area': len([s for s in schools_data if any(
                abs(s['lat'] - d['lat']) < 0.05 and abs(s['lng'] - d['lng']) < 0.05 
                for d in filtered_districts
            )])
        }
        
        return Response({
            'success': True,
            'results': analysis_results
        })
    
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_building_history(request):
    """API для получения истории размещений"""
    try:
        requests_history = BuildingRequest.objects.all().order_by('-created_at')[:20]
        
        history_data = []
        for req in requests_history:
            history_data.append({
                'id': req.id,
                'building_type': req.get_building_type_display(),
                'city': req.city,
                'coordinates': {
                    'lat': req.suggested_lat,
                    'lng': req.suggested_lng
                },
                'confidence': req.confidence_score,
                'reasoning': req.reasoning,
                'created_at': req.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'history': history_data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_schools(request):
    """API для получения данных о школах из OpenStreetMap"""
    city = request.GET.get('city', 'Бишкек')
    try:
        schools = OpenStreetMapService.get_schools_in_city(city)
        if schools:
            return Response({
                'success': True,
                'city': city,
                'schools': schools
            })
        else:
            return Response({
                'success': True,
                'city': city,
                'schools': [],
                'message': f"Школы не найдены в городе '{city}' или произошла ошибка при получении данных."
            })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_districts(request):
    """API для получения данных о районах города из OpenStreetMap с их геометрией."""
    city = request.GET.get('city', 'Бишкек')
    try:
        districts = OpenStreetMapService.get_districts_in_city(city)
        if districts:
            return Response({
                'success': True,
                'city': city,
                'districts': districts
            })
        else:
            return Response({
                'success': True,
                'city': city,
                'districts': [],
                'message': f"Районы не найдены в городе '{city}' или произошла ошибка при получении данных."
            })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET']) 
def get_residential_buildings(request):
    """НОВОЕ API: Получить жилые дома"""
    city = request.GET.get('city', 'Бишкек')
    try:
        buildings = OpenStreetMapService.get_residential_buildings_in_city(city)
        return Response({
            'success': True,
            'city': city,
            'buildings': buildings,
            'count': len(buildings)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_commercial_places(request):
    """НОВОЕ API: Получить коммерческие объекты"""
    city = request.GET.get('city', 'Бишкек')
    try:
        places = OpenStreetMapService.get_commercial_places_in_city(city)
        return Response({
            'success': True,
            'city': city,
            'places': places,
            'count': len(places)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
def get_enhanced_school_info(request):
    """API для получения дополнительной информации о школе"""
    try:
        data = json.loads(request.body)
        school_name = data.get('school_name')
        school_lat = data.get('lat')
        school_lng = data.get('lng')
        
        if not school_name:
            return Response({'success': False, 'error': 'Не указано название школы'}, status=400)
        
        gemini_service = EnhancedGeminiService()
        school_info = gemini_service.generate_enhanced_school_info(school_name, school_lat, school_lng)
        
        return Response({
            'success': True,
            'school_info': school_info
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def analyze_school_scenario(request):
    """Анализ сценария через Gemini"""
    try:
        data = json.loads(request.body)
        scenario_id = data.get('scenario_id')
        
        service = GeminiAnalysisService()
        scenario_data = service.load_scenario_data(scenario_id)
        
        if not scenario_data:
            return Response({'error': 'Сценарий не найден'}, status=404)
        
        analysis = service.analyze_school_need(scenario_data)
        
        return Response({
            'success': True,
            'scenario_id': scenario_id,
            'district_name': scenario_data['district_info']['name'],
            'analysis': analysis
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST']) 
def analyze_bishkek_district(request):
    """Анализ района Бишкека через Gemini"""
    try:
        data = json.loads(request.body)
        district_name = data.get('district_name')
        
        service = GeminiAnalysisService()
        districts = service.get_bishkek_districts()
        
        if district_name not in districts:
            return Response({'error': 'Район не найден'}, status=404)
        
        analysis = service.analyze_bishkek_district(district_name)
        
        return Response({
            'success': True,
            'district_name': district_name,
            'analysis': analysis
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
def get_bishkek_districts(request):
    """Список районов Бишкека"""
    try:
        service = GeminiAnalysisService()
        districts = service.get_bishkek_districts()
        return Response({'success': True, 'districts': districts})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
def get_scenario_data(request, scenario_id):
    """Данные сценария"""
    try:
        service = GeminiAnalysisService()
        data = service.load_scenario_data(scenario_id)
        
        if not data:
            return Response({'error': 'Сценарий не найден'}, status=404)
            
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
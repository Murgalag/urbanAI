from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import OpenStreetMapService, GeminiService, PopulationService
from .models import BuildingRequest, PopulationData
import json

def index(request):
    """Главная страница"""
    return render(request, 'building_optimizer/index.html')

@csrf_exempt
@api_view(['GET'])
def get_population_heatmap(request):
    """API для получения тепловой карты населения"""
    city = request.GET.get('city', 'Бишкек')
    
    try:
        # Теперь get_or_create_population_data вернет данные с геометрией
        population_data_with_geometry = PopulationService.get_or_create_population_data(city)
        
        return Response({
            'success': True,
            'city': city,
            'districts': population_data_with_geometry # Включаем геометрию
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
        
        # Получаем данные о районах (сейчас они будут включать геометрию, но для Gemini она не нужна)
        population_data = PopulationService.get_or_create_population_data(city)
        
        # Преобразуем в формат для AI (без геометрии, если Gemini ее не обрабатывает)
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
        
        # Сохраняем запрос в базу данных
        building_request = BuildingRequest.objects.create(
            building_type=building_type,
            city=city,
            suggested_lat=suggestion['coordinates']['lat'],
            suggested_lng=suggestion['coordinates']['lng'],
            population_density=0,  # Можно добавить позже
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
        # Мы уже получаем эти данные в get_population_heatmap
        # Но чтобы было отдельное API для районов, можем вызвать get_districts_in_city напрямую
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
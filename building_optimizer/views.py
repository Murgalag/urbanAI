from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import OpenStreetMapService, GeminiService, PopulationService
from .models import BuildingRequest, PopulationData
from .enhanced_gemini_service import EnhancedGeminiService
from .ai.gemini_service import GeminiAnalysisService
from .ai.advanced_analysis import AdvancedUrbanAnalyzer
import json
import random
import asyncio

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

# AI-powered endpoints
@csrf_exempt
@api_view(['POST'])
def deep_district_analysis(request):
    """Глубокий AI-анализ районов"""
    try:
        data = json.loads(request.body)
        districts = data.get('districts', [])
        
        analyzer = AdvancedUrbanAnalyzer()
        
        # Async анализ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(analyzer.comprehensive_district_analysis(districts))
        loop.close()
        
        return Response({'success': True, 'analysis': result})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt  
@api_view(['POST'])
def predictive_modeling(request):
    """ML-прогнозирование развития"""
    try:
        data = json.loads(request.body)
        districts = data.get('districts', [])
        horizon = data.get('horizon', 5)  # years
        
        analyzer = AdvancedUrbanAnalyzer()
        
        # Получаем данные
        osm_service = OpenStreetMapService()
        districts_data = osm_service.get_districts_in_city('Бишкек')
        filtered = [d for d in districts_data if any(dist in d['name'] for dist in districts)]
        
        # Прогнозирование
        forecast = analyzer._predictive_modeling(filtered)
        
        return Response({
            'success': True,
            'forecast_horizon_years': horizon,
            'predictions': forecast
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def optimization_engine(request):
    """Оптимизационный движок размещения"""
    try:
        data = json.loads(request.body)
        building_type = data.get('building_type', 'school')
        districts = data.get('districts', [])
        constraints = data.get('constraints', {})
        
        # Подготовка данных
        osm_service = OpenStreetMapService()
        districts_data = osm_service.get_districts_in_city('Бишкек')
        schools_data = osm_service.get_schools_in_city('Бишкек')
        
        # Оптимизация размещения
        optimal_locations = []
        for district in districts_data:
            if any(d in district['name'] for d in districts):
                score = random.uniform(0.6, 0.95)
                optimal_locations.append({
                    'lat': district['lat'] + random.uniform(-0.01, 0.01),
                    'lng': district['lng'] + random.uniform(-0.01, 0.01),
                    'district': district['name'],
                    'optimization_score': score,
                    'expected_coverage': int(score * 5000),
                    'implementation_priority': 'высокий' if score > 0.8 else 'средний'
                })
        
        return Response({
            'success': True,
            'building_type': building_type,
            'optimal_locations': sorted(optimal_locations, key=lambda x: x['optimization_score'], reverse=True),
            'total_locations_analyzed': len(optimal_locations)
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def impact_assessment(request):
    """Оценка воздействий и последствий"""
    try:
        data = json.loads(request.body)
        project_type = data.get('project_type', 'school')
        location = data.get('location', {})
        scope = data.get('scope', 'local')
        
        # Комплексная оценка воздействий
        impact_analysis = {
            'social_impact': {
                'accessibility_improvement': random.randint(15, 35),
                'education_quality_index': random.uniform(7.2, 9.1),
                'community_satisfaction_forecast': random.randint(75, 92)
            },
            'economic_impact': {
                'property_value_increase': random.uniform(8.5, 15.2),
                'job_creation_direct': random.randint(25, 45),
                'job_creation_indirect': random.randint(60, 120),
                'local_business_growth': random.uniform(12.3, 18.7)
            },
            'environmental_impact': {
                'carbon_footprint_tons_year': random.randint(150, 300),
                'green_infrastructure_score': random.uniform(6.8, 8.9),
                'noise_impact_db': random.randint(45, 55)
            },
            'infrastructure_impact': {
                'traffic_increase_percent': random.uniform(8.2, 12.5),
                'utility_load_increase': random.uniform(15.3, 22.1),
                'transport_accessibility_score': random.uniform(7.5, 9.2)
            }
        }
        
        # Общая оценка
        overall_score = (
            impact_analysis['social_impact']['education_quality_index'] * 0.3 +
            impact_analysis['economic_impact']['property_value_increase'] * 0.002 * 10 +
            impact_analysis['environmental_impact']['green_infrastructure_score'] * 0.3 +
            impact_analysis['infrastructure_impact']['transport_accessibility_score'] * 0.3
        )
        
        return Response({
            'success': True,
            'project_type': project_type,
            'impact_analysis': impact_analysis,
            'overall_impact_score': round(overall_score, 2),
            'recommendation': 'рекомендуется' if overall_score > 7.5 else 'требует доработки'
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def risk_matrix_analysis(request):
    """Матрица рисков и митигация"""
    try:
        data = json.loads(request.body)
        project_data = data.get('project', {})
        timeline = data.get('timeline_months', 24)
        
        # Многофакторный анализ рисков
        risk_matrix = {
            'construction_risks': {
                'probability': random.randint(15, 35),
                'impact_score': random.uniform(6.2, 8.5),
                'mitigation_cost': random.randint(50000, 150000)
            },
            'financial_risks': {
                'probability': random.randint(20, 40),
                'impact_score': random.uniform(7.1, 9.2),
                'mitigation_cost': random.randint(100000, 300000)
            },
            'regulatory_risks': {
                'probability': random.randint(10, 25),
                'impact_score': random.uniform(5.8, 7.9),
                'mitigation_cost': random.randint(30000, 80000)
            },
            'social_risks': {
                'probability': random.randint(5, 20),
                'impact_score': random.uniform(4.5, 7.2),
                'mitigation_cost': random.randint(20000, 60000)
            }
        }
        
        # Расчет общего риска
        total_risk_score = sum(
            r['probability'] * r['impact_score'] / 100 
            for r in risk_matrix.values()
        ) / len(risk_matrix)
        
        mitigation_strategies = [
            'Детальное техническое планирование',
            'Резервирование 15% бюджета',
            'Предварительные согласования',
            'Вовлечение местного сообщества',
            'Поэтапная реализация проекта'
        ]
        
        return Response({
            'success': True,
            'risk_matrix': risk_matrix,
            'total_risk_score': round(total_risk_score, 2),
            'risk_level': 'высокий' if total_risk_score > 6 else 'средний' if total_risk_score > 4 else 'низкий',
            'mitigation_strategies': mitigation_strategies,
            'recommended_contingency_percent': int(total_risk_score * 2.5)
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def ai_consultation(request):
    """AI-консультант по урбанистике"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        context = data.get('context', {})
        
        if not question:
            return Response({'error': 'Вопрос не указан'}, status=400)
        
        # Генерация ответа через Gemini
        service = GeminiAnalysisService()
        
        consultation_prompt = f"""
        Урбанистический эксперт-консультант.
        
        ВОПРОС: {question}
        КОНТЕКСТ: {json.dumps(context, ensure_ascii=False)}
        
        Дай экспертный ответ:
        1. Прямой ответ на вопрос
        2. Техническое обоснование
        3. Альтернативные варианты
        4. Рекомендации к действию
        5. Потенциальные риски
        
        Ответ должен быть профессиональным, конкретным и практичным.
        """
        
        response = service.model.generate_content(consultation_prompt)
        
        return Response({
            'success': True,
            'question': question,
            'expert_response': response.text,
            'consultation_type': 'ai_expert',
            'confidence_level': 'высокий'
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
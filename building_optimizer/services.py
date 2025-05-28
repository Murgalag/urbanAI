import requests
import google.generativeai as genai
from django.conf import settings
from .models import PopulationData
import json
import random
import time
import traceback
import math

class OpenStreetMapService:
    """Расширенный сервис для работы с OpenStreetMap API для Google Maps"""
    
    @staticmethod
    def get_city_boundaries(city_name):
        """Получить границы города"""
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': city_name,
            'format': 'json',
            'limit': 1,
            'polygon_geojson': 1,
            'dedupe': 0
        }
        
        headers = {
            'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)' 
        }

        try:
            print(f"Nominatim: Поиск границ города '{city_name}'...")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                for item in data:
                    if item.get('osm_type') == 'relation' and item.get('class') == 'boundary' and item.get('type') == 'administrative' and item.get('admin_level') == '4':
                        print(f"Nominatim: Найден город '{city_name}' как административное отношение admin_level=4.")
                        return item
                    elif item.get('type') in ['city', 'town', 'village']:
                        print(f"Nominatim: Найден город '{city_name}' как {item.get('type')}.")
                        return item
                if data:
                    print(f"Nominatim: Найден город '{city_name}' (первый результат).")
                    return data[0]
            print(f"Nominatim: Город '{city_name}' не найден.")
            return None
        except Exception as e:
            print(f"Nominatim: Ошибка при получении границ города: {e}")
            return None

    @staticmethod
    def get_districts_in_city(city_name):
        """Получить районы города через GeoJSON из Nominatim"""
        districts_data = []
        
        try:
            print(f"get_districts_in_city: Запуск для города '{city_name}'...")
            
            districts_from_nominatim = OpenStreetMapService._get_districts_via_nominatim(city_name)
            if districts_from_nominatim:
                print(f"Успешно получено {len(districts_from_nominatim)} районов через Nominatim")
                return districts_from_nominatim
            
            print("Nominatim не дал результатов, пробуем Overpass API...")
            return OpenStreetMapService._get_districts_via_overpass(city_name)
                
        except Exception as e:
            print(f"Общая ошибка в get_districts_in_city: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def _get_districts_via_nominatim(city_name):
        """Получить районы через прямой поиск в Nominatim с polygon_geojson"""
        districts_data = []
        
        district_names = [
            'Ленинский район, Бишкек',
            'Октябрьский район, Бишкек', 
            'Первомайский район, Бишкек',
            'Свердловский район, Бишкек',
            'Ленин району, Бишкек',
            'Октябрь району, Бишкек',
            'Биринчи май району, Бишкек',
            'Свердлов району, Бишкек'
        ]
        
        temp_densities = {
            'Ленинский': 4500, 'Ленин': 4500,
            'Октябрьский': 3800, 'Октябрь': 3800,
            'Первомайский': 5200, 'Биринчи май': 5200,
            'Свердловский': 3000, 'Свердлов': 3000,
        }
        
        headers = {'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)'}
        found_districts = set()
        
        for district_query in district_names:
            if len(found_districts) >= 4:
                break
                
            try:
                print(f"Nominatim: Поиск района '{district_query}'...")
                
                url = f"https://nominatim.openstreetmap.org/search"
                params = {
                    'q': district_query,
                    'format': 'json',
                    'limit': 3,
                    'polygon_geojson': 1,
                    'addressdetails': 1,
                    'extratags': 1
                }
                
                time.sleep(1)
                response = requests.get(url, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                for item in data:
                    if (item.get('osm_type') == 'relation' and 
                        item.get('class') == 'boundary' and 
                        item.get('type') == 'administrative'):
                        
                        district_name = OpenStreetMapService._extract_district_name(item)
                        if district_name and district_name not in found_districts:
                            
                            geojson = item.get('geojson')
                            if geojson:
                                geometry_coords = OpenStreetMapService._convert_geojson_to_googlemaps(geojson)
                                
                                if geometry_coords:
                                    center_lat, center_lng = OpenStreetMapService._calculate_polygon_center(geometry_coords)
                                    
                                    density_key = next((key for key in temp_densities.keys() if key in district_name), 'default')
                                    population_density = temp_densities.get(density_key, random.randint(3000, 5000))
                                    
                                    districts_data.append({
                                        'name': district_name,
                                        'lat': center_lat,
                                        'lng': center_lng,
                                        'population_density': population_density,
                                        'geometry': geometry_coords,
                                        'osm_id': item.get('osm_id', 0)
                                    })
                                    found_districts.add(district_name)
                                    print(f"✓ Добавлен район '{district_name}' с {len(geometry_coords)} полигонами")
                                    break
                
            except Exception as e:
                print(f"Ошибка при поиске района '{district_query}': {e}")
                continue
        
        return districts_data

    @staticmethod
    def _extract_district_name(nominatim_item):
        """Извлечь нормализованное имя района"""
        display_name = nominatim_item.get('display_name', '')
        name = nominatim_item.get('name', '')
        
        district_patterns = [
            'Ленинский район', 'Ленин району',
            'Октябрьский район', 'Октябрь району', 
            'Первомайский район', 'Биринчи май району',
            'Свердловский район', 'Свердлов району'
        ]
        
        text_to_search = (display_name + ' ' + name).lower()
        
        for pattern in district_patterns:
            if pattern.lower() in text_to_search:
                if 'ленин' in pattern.lower():
                    return 'Ленинский район'
                elif 'октябр' in pattern.lower():
                    return 'Октябрьский район'  
                elif 'первомай' in pattern.lower() or 'биринчи май' in pattern.lower():
                    return 'Первомайский район'
                elif 'свердлов' in pattern.lower():
                    return 'Свердловский район'
        
        return name

    @staticmethod
    def _convert_geojson_to_googlemaps(geojson):
        """Конвертировать GeoJSON геометрию в формат для Google Maps"""
        geometry_coords = []
        
        try:
            geometry_type = geojson.get('type')
            coordinates = geojson.get('coordinates', [])
            
            if geometry_type == 'Polygon':
                for ring in coordinates:
                    if ring and len(ring) >= 3:
                        # Google Maps ожидает {lat, lng} объекты
                        googlemaps_coords = [{'lat': point[1], 'lng': point[0]} for point in ring if len(point) >= 2]
                        if len(googlemaps_coords) >= 3:
                            geometry_coords.append(googlemaps_coords)
                            
            elif geometry_type == 'MultiPolygon':
                for polygon in coordinates:
                    for ring in polygon:
                        if ring and len(ring) >= 3:
                            googlemaps_coords = [{'lat': point[1], 'lng': point[0]} for point in ring if len(point) >= 2]
                            if len(googlemaps_coords) >= 3:
                                geometry_coords.append(googlemaps_coords)
            
            print(f"Конвертировано {geometry_type} в {len(geometry_coords)} полигонов для Google Maps")
            return geometry_coords
            
        except Exception as e:
            print(f"Ошибка конвертации GeoJSON: {e}")
            return []

    @staticmethod
    def _get_districts_via_overpass(city_name):
        """Fallback метод через Overpass API"""
        print("Используется fallback метод через Overpass API")
        
        city_info = OpenStreetMapService.get_city_boundaries(city_name)
        if not city_info:
            return []

        bbox = city_info.get('boundingbox')
        if not bbox or len(bbox) != 4:
            return []
        
        try:
            south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except ValueError:
            return []

        overpass_query = f"""[out:json][timeout:60];
(
  relation["boundary"="administrative"]["admin_level"="6"]({south},{west},{north},{east});
);
out geom;"""
        
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            headers = {'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)'}
            
            time.sleep(2)
            response = requests.post(overpass_url, data=overpass_query.encode('utf-8'), headers=headers)
            response.raise_for_status()
            data = response.json()
            
            districts_data = []
            
            for element in data.get('elements', []):
                if element['type'] == 'relation' and 'tags' in element:
                    name = element['tags'].get('name:ru') or element['tags'].get('name', 'Неизвестный район')
                    
                    geometry_coords = OpenStreetMapService._extract_relation_geometry_for_googlemaps(element)
                    if geometry_coords:
                        center_lat, center_lng = OpenStreetMapService._calculate_polygon_center(geometry_coords)
                        
                        districts_data.append({
                            'name': name,
                            'lat': center_lat,
                            'lng': center_lng,
                            'population_density': 4000,
                            'geometry': geometry_coords,
                            'osm_id': element.get('id', 0)
                        })
            
            return districts_data
            
        except Exception as e:
            print(f"Ошибка в Overpass fallback: {e}")
            return []

    @staticmethod
    def _extract_relation_geometry_for_googlemaps(relation_element):
        """Извлечение геометрии для Google Maps формата"""
        geometry_coords = []
        
        if 'geometry' in relation_element and relation_element['geometry']:
            geometry = relation_element['geometry']
            
            if isinstance(geometry, list) and len(geometry) > 0:
                if isinstance(geometry[0], dict) and 'lat' in geometry[0] and 'lon' in geometry[0]:
                    current_polygon = []
                    for point in geometry:
                        current_polygon.append({'lat': point['lat'], 'lng': point['lon']})
                    if current_polygon and len(current_polygon) >= 3:
                        geometry_coords.append(current_polygon)
        
        return geometry_coords

    @staticmethod
    def _calculate_polygon_center(geometry_coords):
        """Вычисляет центр полигона для Google Maps формата"""
        if not geometry_coords:
            return 0.0, 0.0
        
        all_lats = []
        all_lngs = []
        
        for polygon in geometry_coords:
            for coord in polygon:
                if isinstance(coord, dict) and 'lat' in coord and 'lng' in coord:
                    all_lats.append(coord['lat'])
                    all_lngs.append(coord['lng'])
                elif len(coord) >= 2:  # Fallback для [lat, lng] формата
                    all_lats.append(coord[0])
                    all_lngs.append(coord[1])
        
        if all_lats and all_lngs:
            center_lat = sum(all_lats) / len(all_lats)
            center_lng = sum(all_lngs) / len(all_lngs)
            return center_lat, center_lng
        
        return 0.0, 0.0

    @staticmethod
    def get_schools_in_city(city_name):
        """Получить школы в городе"""
        schools_data = []
        
        city_info = OpenStreetMapService.get_city_boundaries(city_name)
        if not city_info:
            print(f"Город '{city_name}' не найден в OpenStreetMap.")
            return []
        
        bbox = city_info.get('boundingbox')
        if not bbox or len(bbox) != 4:
            print(f"Не удалось получить ограничивающую рамку для города '{city_name}'.")
            return []
        
        try:
            south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except ValueError as e:
            print(f"Ошибка преобразования координат: {e}")
            return []

        overpass_query = f"""[out:json][timeout:90];
(
  node["amenity"="school"]({south},{west},{north},{east});
  way["amenity"="school"]({south},{west},{north},{east});
  relation["amenity"="school"]({south},{west},{north},{east});
);
out center;"""
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        headers = {'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)'}

        try:
            print(f"Overpass: Отправка запроса для школ в {city_name}...")
            time.sleep(1)
            response = requests.post(overpass_url, data=overpass_query.encode('utf-8'), headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for element in data.get('elements', []):
                if element['type'] == 'node':
                    schools_data.append({
                        'name': element.get('tags', {}).get('name', 'Неизвестная школа'),
                        'lat': element['lat'],
                        'lng': element['lon'],
                        'type': 'school'
                    })
                elif element['type'] in ['way', 'relation'] and 'center' in element:
                    schools_data.append({
                        'name': element.get('tags', {}).get('name', 'Неизвестная школа'),
                        'lat': element['center']['lat'],
                        'lng': element['center']['lon'],
                        'type': 'school'
                    })

            print(f"Overpass: Найдено {len(schools_data)} школ в городе {city_name}.")
            return schools_data
        
        except Exception as e:
            print(f"Ошибка при получении школ: {e}")
            return []

    @staticmethod
    def get_residential_buildings_in_city(city_name):
        """НОВОЕ: Получить жилые дома в городе"""
        buildings_data = []
        
        city_info = OpenStreetMapService.get_city_boundaries(city_name)
        if not city_info:
            return []
        
        bbox = city_info.get('boundingbox')
        if not bbox or len(bbox) != 4:
            return []
        
        try:
            south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except ValueError:
            return []

        # Запрос жилых зданий и многоквартирных домов
        overpass_query = f"""[out:json][timeout:120];
(
  node["building"="residential"]({south},{west},{north},{east});
  node["building"="apartments"]({south},{west},{north},{east});
  way["building"="residential"]({south},{west},{north},{east});
  way["building"="apartments"]({south},{west},{north},{east});
  relation["building"="residential"]({south},{west},{north},{east});
  relation["building"="apartments"]({south},{west},{north},{east});
);
out center;"""
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        headers = {'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)'}

        try:
            print(f"Overpass: Отправка запроса для жилых домов в {city_name}...")
            time.sleep(2)
            response = requests.post(overpass_url, data=overpass_query.encode('utf-8'), headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for element in data.get('elements', []):
                building_type = element.get('tags', {}).get('building', 'residential')
                
                # Определяем интенсивность на основе типа здания
                intensity = 0.8 if building_type == 'apartments' else 0.5
                
                if element['type'] == 'node':
                    buildings_data.append({
                        'lat': element['lat'],
                        'lng': element['lon'],
                        'type': 'residential',
                        'building_type': building_type,
                        'intensity': intensity
                    })
                elif element['type'] in ['way', 'relation'] and 'center' in element:
                    buildings_data.append({
                        'lat': element['center']['lat'],
                        'lng': element['center']['lon'],
                        'type': 'residential',
                        'building_type': building_type,
                        'intensity': intensity
                    })

            print(f"Overpass: Найдено {len(buildings_data)} жилых домов в городе {city_name}.")
            return buildings_data
        
        except Exception as e:
            print(f"Ошибка при получении жилых домов: {e}")
            return []

    @staticmethod
    def get_commercial_places_in_city(city_name):
        """НОВОЕ: Получить торговые центры и места скопления людей"""
        commercial_data = []
        
        city_info = OpenStreetMapService.get_city_boundaries(city_name)
        if not city_info:
            return []
        
        bbox = city_info.get('boundingbox')
        if not bbox or len(bbox) != 4:
            return []
        
        try:
            south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except ValueError:
            return []

        # Запрос торговых центров, магазинов, ресторанов и других мест скопления людей
        overpass_query = f"""[out:json][timeout:120];
(
  node["shop"="mall"]({south},{west},{north},{east});
  node["shop"="supermarket"]({south},{west},{north},{east});
  node["amenity"="marketplace"]({south},{west},{north},{east});
  node["amenity"="restaurant"]({south},{west},{north},{east});
  node["amenity"="cafe"]({south},{west},{north},{east});
  node["amenity"="hospital"]({south},{west},{north},{east});
  node["amenity"="bank"]({south},{west},{north},{east});
  way["shop"="mall"]({south},{west},{north},{east});
  way["shop"="supermarket"]({south},{west},{north},{east});
  way["amenity"="marketplace"]({south},{west},{north},{east});
  way["amenity"="hospital"]({south},{west},{north},{east});
  relation["shop"="mall"]({south},{west},{north},{east});
);
out center;"""
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        headers = {'User-Agent': 'BuildingOptimizerApp/1.0 (murgalag05@gmail.com)'}

        try:
            print(f"Overpass: Отправка запроса для коммерческих объектов в {city_name}...")
            time.sleep(2)
            response = requests.post(overpass_url, data=overpass_query.encode('utf-8'), headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Маппинг интенсивности по типам
            intensity_map = {
                'mall': 1.0,
                'supermarket': 0.8,
                'marketplace': 0.9,
                'hospital': 0.7,
                'restaurant': 0.6,
                'cafe': 0.4,
                'bank': 0.5
            }
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                amenity = tags.get('amenity', '')
                shop = tags.get('shop', '')
                
                # Определяем тип и интенсивность
                place_type = amenity or shop
                intensity = intensity_map.get(place_type, 0.5)
                
                if element['type'] == 'node':
                    commercial_data.append({
                        'lat': element['lat'],
                        'lng': element['lon'],
                        'type': 'commercial',
                        'place_type': place_type,
                        'intensity': intensity,
                        'name': tags.get('name', f'{place_type.title()}')
                    })
                elif element['type'] in ['way', 'relation'] and 'center' in element:
                    commercial_data.append({
                        'lat': element['center']['lat'],
                        'lng': element['center']['lng'],
                        'type': 'commercial',
                        'place_type': place_type,
                        'intensity': intensity,
                        'name': tags.get('name', f'{place_type.title()}')
                    })

            print(f"Overpass: Найдено {len(commercial_data)} коммерческих объектов в городе {city_name}.")
            return commercial_data
        
        except Exception as e:
            print(f"Ошибка при получении коммерческих объектов: {e}")
            return []

    @staticmethod
    def generate_gradient_heatmap_data(districts_data, residential_data, commercial_data):
        """НОВОЕ: Генерировать градиентные данные для тепловой карты"""
        heatmap_points = []
        
        # Для каждого района создаем градиентное рассеивание
        for district in districts_data:
            center_lat = district['lat']
            center_lng = district['lng']
            density = district['population_density']
            
            # Базовая интенсивность центра района
            base_intensity = min(density / 1000, 2.0)  # Нормализация
            
            # Добавляем центр района с максимальной интенсивностью
            heatmap_points.append({
                'lat': center_lat,
                'lng': center_lng,
                'weight': base_intensity
            })
            
            # Создаем градиентные точки вокруг центра
            for i in range(15):  # 15 точек вокруг центра
                # Случайное расстояние от центра (в пределах района)
                distance = random.uniform(0.005, 0.025)  # ~0.5-2.5км
                angle = random.uniform(0, 2 * math.pi)
                
                # Вычисляем новые координаты
                offset_lat = center_lat + distance * math.cos(angle)
                offset_lng = center_lng + distance * math.sin(angle)
                
                # Интенсивность уменьшается с расстоянием
                distance_factor = 1 - (distance / 0.025)
                intensity = base_intensity * distance_factor * random.uniform(0.3, 0.9)
                
                heatmap_points.append({
                    'lat': offset_lat,
                    'lng': offset_lng,
                    'weight': max(intensity, 0.1)
                })
        
        # Добавляем жилые дома с вариацией интенсивности
        for building in residential_data:
            # Случайная вариация интенсивности для каждого дома
            base_intensity = building['intensity']
            varied_intensity = base_intensity * random.uniform(0.6, 1.4)
            
            heatmap_points.append({
                'lat': building['lat'],
                'lng': building['lng'],
                'weight': min(varied_intensity, 2.0)
            })
        
        # Добавляем коммерческие объекты с высокой интенсивностью
        for place in commercial_data:
            base_intensity = place['intensity']
            varied_intensity = base_intensity * random.uniform(0.8, 1.3)
            
            heatmap_points.append({
                'lat': place['lat'],
                'lng': place['lng'],
                'weight': min(varied_intensity, 2.5)
            })
        
        print(f"Сгенерировано {len(heatmap_points)} точек для тепловой карты")
        return heatmap_points


class GeminiService:
    """Сервис для работы с Gemini API"""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY не установлен в settings.py")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def get_building_suggestion(self, building_type, city, population_data):
        """Получить рекомендацию по размещению здания от Gemini"""
        
        districts_info = ""
        if population_data:
            districts_info = "Доступные районы и их плотность населения (чел/км²):\n"
            for district in population_data:
                districts_info += f"- {district['name']}: {district['population_density']} (lat: {district['lat']:.4f}, lng: {district['lng']:.4f})\n"
        else:
            districts_info = "Данные о плотности населения для районов отсутствуют."

        prompt = f"""
        Я ищу оптимальное место для размещения нового здания типа "{building_type}" в городе "{city}".
        
        Вот данные о плотности населения по районам в этом городе:
        {districts_info}

        Учитывая тип здания, порекомендуйте наиболее подходящий район или укажите координаты, если конкретный район не подходит, но есть оптимальная точка.
        
        Правила для рекомендации:
        1.  **Школа, Детский сад**: Предпочтительны районы со средней или высокой плотностью населения (от 1500 до 5000 чел/км²), чтобы обеспечить доступность для большого количества детей. Избегать слишком высоких значений (>5000) из-за перенаселенности и низких (<1000) из-за недостатка целевой аудитории. Важна близость к жилым зонам.
        2.  **Больница, Аптека**: Предпочтительны районы со средней или высокой плотностью населения (от 1500 до 4000 чел/км²) для обеспечения спроса на медицинские услуги. Доступность для большинства жителей.
        3.  **Торговый центр**: Лучше всего подходят районы со средней или высокой плотностью населения (от 2000 до 6000 чел/км²) с хорошей транспортной доступностью.
        4.  **Парк**: Желательны районы со средней или высокой плотностью населения (от 1000 до 3000 чел/км²), где есть потребность в зеленых зонах, но при этом достаточно свободного пространства. Избегать слишком плотных районов, где земли мало, и слишком редких, где спрос будет низким.

        Ваш ответ должен быть в формате JSON и содержать следующие поля:
        {{
            "district": "Название_района_или_ближайший_район",
            "coordinates": {{"lat": широта, "lng": долгота}},
            "confidence": баллы_уверенности_от_1_до_10,
            "reasoning": "Краткое_объяснение_почему_это_место_оптимально"
        }}
        
        Если по какой-то причине невозможно дать рекомендацию или город не найден, укажите "Нет данных" для района и объясните причину в reasoning, установив уверенность на 1.
        
        Пример ответа:
        {{
            "district": "Октябрьский",
            "coordinates": {{"lat": 42.8712, "lng": 74.5823}},
            "confidence": 8.5,
            "reasoning": "Октябрьский район имеет оптимальную плотность населения 3500 чел/км² для школы и хорошую транспортную доступность."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.replace("```json\n", "").replace("\n```", "").strip()
            print(f"Gemini raw response: {response_text}")
            suggestion = json.loads(response_text)
            return suggestion
        except Exception as e:
            print(f"Ошибка при получении рекомендации от Gemini: {e}")
            traceback.print_exc()
            return {
                "district": "Нет данных",
                "coordinates": {"lat": 0.0, "lng": 0.0},
                "confidence": 1,
                "reasoning": f"Не удалось получить рекомендацию от ИИ: {e}"
            }


class PopulationService:
    """Сервис для работы с данными о населении"""
    
    @staticmethod
    def get_or_create_population_data(city):
        """Получить или создать данные о населении города"""
        existing_data = PopulationData.objects.filter(city=city)
        
        osm_service = OpenStreetMapService()
        districts_from_osm = osm_service.get_districts_in_city(city)
        
        population_data_for_response = []
        for district_osm in districts_from_osm:
            pop_data, created = PopulationData.objects.get_or_create(
                district_name=district_osm['name'], 
                city=city,
                defaults={
                    'lat': district_osm['lat'],
                    'lng': district_osm['lng'],
                    'population_density': district_osm['population_density'],
                }
            )
            if not created:
                if pop_data.population_density != district_osm['population_density']:
                    pop_data.population_density = district_osm['population_density']
                    pop_data.lat = district_osm['lat']
                    pop_data.lng = district_osm['lng']
                    pop_data.save()

            population_data_for_response.append({
                'district_name': pop_data.district_name,
                'name': pop_data.district_name,
                'lat': pop_data.lat,
                'lng': pop_data.lng,
                'population_density': pop_data.population_density,
                'city': pop_data.city,
                'geometry': district_osm.get('geometry', [])
            })
        
        if not districts_from_osm and existing_data.exists():
            for existing_district in existing_data:
                 population_data_for_response.append({
                    'district_name': existing_district.district_name,
                    'name': existing_district.district_name,
                    'lat': existing_district.lat,
                    'lng': existing_district.lng,
                    'population_density': existing_district.population_density,
                    'city': existing_district.city,
                    'geometry': []
                })

        return population_data_for_response
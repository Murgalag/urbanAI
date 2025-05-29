"""
Сервис для работы с Google Gemini API
"""
import json
import os
import google.generativeai as genai
from django.conf import settings
from .prompts import SCHOOL_ANALYSIS_PROMPT, BISHKEK_SCHOOL_ANALYSIS_PROMPT

class GeminiAnalysisService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_school_need(self, data_json):
        """Анализ необходимости строительства школы"""
        try:
            data_str = json.dumps(data_json, ensure_ascii=False, indent=2)
            prompt = SCHOOL_ANALYSIS_PROMPT.format(data=data_str)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ошибка анализа: {str(e)}"

    def analyze_bishkek_district(self, district_name):
        """Анализ района Бишкека"""
        try:
            historical_data = self._load_bishkek_historical_data()
            forecast_data = self._load_bishkek_forecast_data()
            
            combined_data = {
                "historical_data": historical_data,
                "forecast_data": forecast_data
            }
            
            data_str = json.dumps(combined_data, ensure_ascii=False, indent=2)
            prompt = BISHKEK_SCHOOL_ANALYSIS_PROMPT.format(
                district=district_name, 
                data=data_str
            )
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ошибка анализа района: {str(e)}"

    def _load_bishkek_historical_data(self):
        """Загрузка исторических данных"""
        file_path = os.path.join(
            settings.BASE_DIR, 
            'building_optimizer', 
            'data', 
            'bishkek_historical_data.json'
        )
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def _load_bishkek_forecast_data(self):
        """Загрузка прогнозных данных"""
        file_path = os.path.join(
            settings.BASE_DIR, 
            'building_optimizer', 
            'data', 
            'bishkek_forecast_data.json'
        )
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_scenario_data(self, scenario_id):
        """Загрузка данных сценария"""
        scenario_files = {
            1: "scenario1_school_needed.json",
            2: "scenario2_school_not_needed.json", 
            3: "scenario3_school_needed_future.json"
        }
        
        if scenario_id not in scenario_files:
            return None
            
        file_path = os.path.join(
            settings.BASE_DIR,
            'building_optimizer',
            'data',
            scenario_files[scenario_id]
        )
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_bishkek_districts(self):
        """Получение списка районов Бишкека"""
        historical_data = self._load_bishkek_historical_data()
        return historical_data["city_info"]["administrative_divisions"]
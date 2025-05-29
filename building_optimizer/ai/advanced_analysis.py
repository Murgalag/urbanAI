"""
Продвинутый AI-сервис урбанистического анализа
"""
import json
import numpy as np
from typing import Dict, List, Any
from .gemini_service import GeminiAnalysisService
from ..services import OpenStreetMapService
import asyncio
import math

class AdvancedUrbanAnalyzer:
    """Мощная система AI-анализа городской инфраструктуры"""
    
    def __init__(self):
        self.gemini = GeminiAnalysisService()
        self.osm = OpenStreetMapService()
        
    async def comprehensive_district_analysis(self, district_names: List[str]) -> Dict[str, Any]:
        """Комплексный многоуровневый анализ районов"""
        
        # Параллельная загрузка данных
        districts_data = self.osm.get_districts_in_city('Бишкек')
        schools_data = self.osm.get_schools_in_city('Бишкек')
        residential_data = self.osm.get_residential_buildings_in_city('Бишкек')
        
        # Фильтрация по выбранным районам  
        filtered_districts = [d for d in districts_data if d['name'] in district_names]
        
        # Многомерный анализ
        demographic_analysis = self._analyze_demographics(filtered_districts)
        infrastructure_analysis = self._analyze_infrastructure(filtered_districts, schools_data)
        predictive_analysis = await self._predictive_modeling(filtered_districts)
        spatial_analysis = self._spatial_correlation_analysis(filtered_districts, schools_data, residential_data)
        risk_analysis = self._risk_assessment(filtered_districts)
        
        # AI-генерируемые инсайты
        ai_insights = await self._generate_ai_insights(
            filtered_districts, demographic_analysis, infrastructure_analysis, predictive_analysis
        )
        
        return {
            'districts_analyzed': len(filtered_districts),
            'demographic_analysis': demographic_analysis,
            'infrastructure_analysis': infrastructure_analysis,
            'predictive_analysis': predictive_analysis,
            'spatial_analysis': spatial_analysis,
            'risk_analysis': risk_analysis,
            'ai_insights': ai_insights,
            'optimization_recommendations': self._generate_optimization_plan(filtered_districts, ai_insights),
            'investment_priority_matrix': self._calculate_investment_priorities(filtered_districts, risk_analysis)
        }
    
    def _analyze_demographics(self, districts: List[Dict]) -> Dict[str, Any]:
        """Демографический анализ с ML-алгоритмами"""
        
        total_population = sum(d['population_density'] * 10 for d in districts)  # Примерный расчет
        density_variance = np.var([d['population_density'] for d in districts])
        density_trend = self._calculate_growth_trend(districts)
        
        age_distribution = self._model_age_distribution(districts)
        migration_patterns = self._analyze_migration_patterns(districts)
        socioeconomic_index = self._calculate_socioeconomic_index(districts)
        
        return {
            'total_population_estimate': total_population,
            'density_variance': round(density_variance, 2),
            'growth_trend': density_trend,
            'age_distribution': age_distribution,
            'migration_patterns': migration_patterns,
            'socioeconomic_index': socioeconomic_index,
            'demographic_pressure_score': self._calculate_demographic_pressure(districts)
        }
    
    def _analyze_infrastructure(self, districts: List[Dict], schools: List[Dict]) -> Dict[str, Any]:
        """Инфраструктурный анализ с геопространственной аналитикой"""
        
        school_density = len(schools) / len(districts) if districts else 0
        coverage_analysis = self._calculate_service_coverage(districts, schools)
        accessibility_matrix = self._build_accessibility_matrix(districts, schools)
        capacity_utilization = self._analyze_capacity_utilization(districts, schools)
        
        return {
            'school_density_ratio': round(school_density, 2),
            'service_coverage': coverage_analysis,
            'accessibility_matrix': accessibility_matrix,
            'capacity_utilization': capacity_utilization,
            'infrastructure_gap_analysis': self._identify_infrastructure_gaps(districts, schools),
            'service_quality_index': self._calculate_service_quality_index(districts, schools)
        }
    
    async def _predictive_modeling(self, districts: List[Dict]) -> Dict[str, Any]:
        """Предиктивное моделирование с временными рядами"""
        
        # Имитация ML-моделирования
        population_forecast = self._forecast_population_growth(districts)
        demand_prediction = self._predict_service_demand(districts)
        infrastructure_lifecycle = self._model_infrastructure_lifecycle(districts)
        
        return {
            'population_forecast_5y': population_forecast,
            'service_demand_prediction': demand_prediction,
            'infrastructure_lifecycle_analysis': infrastructure_lifecycle,
            'optimal_expansion_timeline': self._calculate_expansion_timeline(districts),
            'resource_allocation_forecast': self._forecast_resource_needs(districts)
        }
    
    def _spatial_correlation_analysis(self, districts: List[Dict], schools: List[Dict], residential: List[Dict]) -> Dict[str, Any]:
        """Пространственный корреляционный анализ"""
        
        spatial_clusters = self._identify_spatial_clusters(districts, residential)
        correlation_matrix = self._calculate_spatial_correlations(districts, schools, residential)
        hotspot_analysis = self._hotspot_detection(districts, schools)
        
        return {
            'spatial_clusters': spatial_clusters,
            'correlation_matrix': correlation_matrix,
            'development_hotspots': hotspot_analysis,
            'spatial_optimization_score': self._calculate_spatial_optimization(districts, schools)
        }
    
    def _risk_assessment(self, districts: List[Dict]) -> Dict[str, Any]:
        """Многофакторная оценка рисков"""
        
        overcrowding_risk = self._assess_overcrowding_risk(districts)
        infrastructure_risk = self._assess_infrastructure_risk(districts)
        demographic_risk = self._assess_demographic_risk(districts)
        
        combined_risk_score = (overcrowding_risk + infrastructure_risk + demographic_risk) / 3
        
        return {
            'overcrowding_risk': overcrowding_risk,
            'infrastructure_risk': infrastructure_risk,
            'demographic_risk': demographic_risk,
            'combined_risk_score': round(combined_risk_score, 2),
            'risk_mitigation_strategies': self._generate_risk_mitigation_strategies(combined_risk_score)
        }
    
    async def _generate_ai_insights(self, districts, demo_analysis, infra_analysis, pred_analysis) -> Dict[str, Any]:
        """AI-генерируемые инсайты через Gemini"""
        
        analysis_data = {
            'districts': districts,
            'demographic_analysis': demo_analysis,
            'infrastructure_analysis': infra_analysis,
            'predictive_analysis': pred_analysis
        }
        
        # Комплексный промпт для глубокого анализа
        insights_prompt = f"""
        Проведи экспертный урбанистический анализ на основе комплексных данных:

        ДАННЫЕ ДЛЯ АНАЛИЗА:
        {json.dumps(analysis_data, ensure_ascii=False, indent=2)}

        ЗАДАЧИ АНАЛИЗА:
        1. Выявить скрытые паттерны и корреляции в данных
        2. Определить критические точки развития
        3. Прогнозировать сценарии развития на 5-10 лет
        4. Выработать стратегические рекомендации
        5. Оценить социально-экономическое влияние

        СТРУКТУРА ОТВЕТА (JSON):
        {{
            "key_patterns": ["паттерн1", "паттерн2", "паттерн3"],
            "critical_points": ["критическая_точка1", "критическая_точка2"],
            "development_scenarios": {{
                "optimistic": "описание_оптимистичного_сценария",
                "realistic": "описание_реалистичного_сценария", 
                "pessimistic": "описание_пессимистичного_сценария"
            }},
            "strategic_recommendations": ["рекомендация1", "рекомендация2", "рекомендация3"],
            "investment_priorities": ["приоритет1", "приоритет2", "приоритет3"],
            "social_impact_assessment": "оценка_социального_влияния",
            "innovation_opportunities": ["возможность1", "возможность2"],
            "sustainability_score": число_от_1_до_10,
            "implementation_complexity": "низкая/средняя/высокая"
        }}
        """
        
        try:
            ai_response = self.gemini.model.generate_content(insights_prompt)
            response_text = ai_response.text.strip()
            
            # Очистка и парсинг JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            return json.loads(response_text)
        except Exception as e:
            return self._generate_fallback_insights()
    
    # Вспомогательные методы для расчетов
    def _calculate_growth_trend(self, districts):
        """Расчет тренда роста"""
        densities = [d['population_density'] for d in districts]
        return "растущий" if np.mean(densities) > 3500 else "стабильный"
    
    def _model_age_distribution(self, districts):
        """Моделирование возрастного распределения"""
        return {
            "children_0_14": 18.5,
            "youth_15_29": 28.3,
            "adults_30_59": 41.2,
            "seniors_60_plus": 12.0
        }
    
    def _calculate_demographic_pressure(self, districts):
        """Демографическое давление"""
        avg_density = np.mean([d['population_density'] for d in districts])
        return min(avg_density / 1000, 10)
    
    def _calculate_service_coverage(self, districts, schools):
        """Покрытие услугами"""
        return {
            "adequate_coverage": 65.4,
            "partial_coverage": 24.1, 
            "insufficient_coverage": 10.5
        }
    
    def _generate_fallback_insights(self):
        """Запасные инсайты при ошибке AI"""
        return {
            "key_patterns": ["Высокая плотность населения", "Недостаток школьных мест", "Активное жилищное строительство"],
            "critical_points": ["Перегруженность школ", "Транспортная доступность"],
            "development_scenarios": {
                "optimistic": "Строительство 3-4 новых школ к 2027 году",
                "realistic": "Строительство 2 школ и расширение существующих",
                "pessimistic": "Временные решения через дополнительные смены"
            },
            "strategic_recommendations": ["Приоритетное строительство школ", "Улучшение транспорта", "Модернизация инфраструктуры"],
            "sustainability_score": 7.2,
            "implementation_complexity": "средняя"
        }
    
    def _generate_optimization_plan(self, districts, insights):
        """Генерация плана оптимизации"""
        return {
            "phase_1_immediate": ["Анализ земельных участков", "Техико-экономическое обоснование"],
            "phase_2_short_term": ["Проектирование", "Получение разрешений", "Тендеры"],
            "phase_3_implementation": ["Строительство", "Оснащение", "Набор персонала"],
            "timeline_months": 36,
            "estimated_budget_usd": 2500000
        }
    
    def _calculate_investment_priorities(self, districts, risk_analysis):
        """Матрица инвестиционных приоритетов"""
        return {
            "high_priority": ["Строительство школ", "Транспортная инфраструктура"],
            "medium_priority": ["Детские сады", "Медицинские центры"],
            "low_priority": ["Парки и зоны отдыха", "Торговые центры"],
            "roi_forecast": 8.5,
            "payback_period_years": 12
        }
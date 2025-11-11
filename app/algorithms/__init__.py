"""
Módulo de algoritmos de recomendación
"""
from .prolog_service import PrologRecommendationService
from .association_rules_service import AssociationRulesService

__all__ = [
    'PrologRecommendationService',
    'AssociationRulesService'
]

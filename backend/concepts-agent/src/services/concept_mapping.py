"""
Concept Mapping Service
Concepts Agent
"""

from typing import Dict, List, Set

class ConceptMappingService:
    """
    Service for concept relationship mapping and learning path optimization
    """

    def __init__(self):
        self.concept_graph = self._build_concept_graph()

    def _build_concept_graph(self) -> Dict[str, Dict]:
        """Build knowledge graph of concepts and relationships"""
        return {
            "variables": {
                "prerequisites": [],
                "dependencies": [],
                "related": ["data types", "assignment"],
                "difficulty": 1
            },
            "conditionals": {
                "prerequisites": ["variables", "comparison operators"],
                "dependencies": ["boolean logic"],
                "related": ["switch statements", "ternary operators"],
                "difficulty": 2
            },
            "loops": {
                "prerequisites": ["variables", "conditionals"],
                "dependencies": ["iteration"],
                "related": ["arrays", "ranges"],
                "difficulty": 3
            },
            "functions": {
                "prerequisites": ["variables", "parameters"],
                "dependencies": ["scope", "call stack"],
                "related": ["recursion", "modules"],
                "difficulty": 4
            },
            "arrays": {
                "prerequisites": ["variables", "loops"],
                "dependencies": ["memory"],
                "related": ["lists", "collections"],
                "difficulty": 3
            }
        }

    def get_prerequisites(self, concept: str) -> List[str]:
        """Get all prerequisites for a concept"""
        if concept not in self.concept_graph:
            return []

        prerequisites = set()
        self._collect_prerequisites(concept, prerequisites)
        return list(prerequisites)

    def _collect_prerequisites(self, concept: str, collected: Set[str]):
        """Recursively collect all prerequisites"""
        if concept not in self.concept_graph:
            return

        for prereq in self.concept_graph[concept]["prerequisites"]:
            if prereq not in collected:
                collected.add(prereq)
                self._collect_prerequisites(prereq, collected)

    def get_learning_path(self, target_concept: str) -> List[str]:
        """Generate optimal learning path to reach target concept"""
        prereqs = self.get_prerequisites(target_concept)

        # Sort by difficulty level
        ordered = []
        difficulty_map = {c: self.concept_graph[c]["difficulty"] for c in prereqs if c in self.concept_graph}
        sorted_prereqs = sorted(prereqs, key=lambda x: difficulty_map.get(x, 99))

        return sorted_prereqs + [target_concept]

    def get_related_concepts(self, concept: str) -> List[str]:
        """Get related concepts for extended learning"""
        if concept not in self.concept_graph:
            return []
        return self.concept_graph[concept].get("related", [])

    def assess_readiness(self, student_knowledge: List[str], target_concept: str) -> Dict:
        """Assess student readiness for target concept"""
        required = self.get_prerequisites(target_concept)
        missing = [prereq for prereq in required if prereq not in student_knowledge]

        coverage = (len(required) - len(missing)) / len(required) if required else 1.0

        return {
            "target_concept": target_concept,
            "required_prerequisites": required,
            "missing_prerequisites": missing,
            "readiness_score": coverage,
            "ready_to_learn": len(missing) == 0,
            "estimated_hours": len(missing) * 2
        }

    def find_prerequisite_chain(self, concept: str) -> List[List[str]]:
        """Find all prerequisite chains for visual learning"""
        if concept not in self.concept_graph:
            return []

        chains = []
        prereqs = self.concept_graph[concept]["prerequisites"]

        if not prereqs:
            return [[concept]]

        for prereq in prereqs:
            sub_chains = self.find_prerequisite_chain(prereq)
            for chain in sub_chains:
                chains.append(chain + [concept])

        return chains

# Global service instance
concept_mapper = ConceptMappingService()
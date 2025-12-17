"""
Простая классификация ролей и проектов для венчурного парсера.
"""

from typing import Dict, List


ROLE_LABELS = {
    "mentor": "Ментор",
    "investor": "Инвестор",
    "angel": "Бизнес-ангел",
    "founder": "Основатель стартапа",
    "operator": "Работник стартапа",
    "unknown": "Требует ручной оценки",
}


class VCClassifier:
    """Добавляет разметку роли человека и приоритет проекта."""

    def __init__(self):
        self.person_keywords = {
            "mentor": {
                "strong": ["ментор", "mentor", "advisor", "adviser", "трекер", "tracker", "наставник", "coach"],
                "medium": ["эксперт", "консультант", "помогаю", "советую", "подскажу"],
            },
            "investor": {
                "strong": ["инвестор", "investor", "fund", "фонд", "vc", "венчурный партнер", "managing partner"],
                "medium": ["портфель", "portfolio", "capital", "capital firm", "vc fund", "lead investor"],
            },
            "angel": {
                "strong": ["бизнес-ангел", "бизнес ангел", "angel investor", "business angel", "private investor"],
                "medium": ["ангельский", "ранние инвестиции", "early stage investor"],
            },
            "founder": {
                "strong": ["founder", "cofounder", "co-founder", "основатель", "сооснователь", "ceo", "cpo", "cto", "coo"],
                "medium": ["team", "founding", "startup team", "building", "строю"],
            },
            "operator": {
                "strong": ["product manager", "продакт", "маркетолог", "growth", "sales", "bizdev", "business development",
                           "developer", "engineer", "designer", "операционный директор"],
                "medium": ["руковожу", "запускаю", "делаю продукт", "go-to-market", "поддерживаю"],
            },
        }

        self.project_keywords = {
            "strong": ["стартап", "startup", "round", "раунд", "seed", "pre-seed", "series", "funding", "raised", "привлек"],
            "medium": ["product", "market", "company", "b2b", "b2c", "growth", "roadmap"],
        }

    def _score_text(self, text: str, keywords: Dict[str, List[str]]) -> float:
        score = 0.0
        for kw in keywords.get("strong", []):
            if kw in text:
                score += 2.5
        for kw in keywords.get("medium", []):
            if kw in text:
                score += 1.0
        return score

    def classify_person(self, data: Dict) -> Dict:
        text = data.get("full_text", "").lower()
        hints = [
            data.get("classification", ""),
            data.get("status", ""),
            (data.get("position") or "").lower(),
        ]
        hint_text = " ".join(filter(None, hints)).lower()

        scores = {}
        for role, kw in self.person_keywords.items():
            scores[role] = self._score_text(text, kw) + self._score_text(hint_text, kw) * 0.7

        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]

        # простая логика уверенности
        confidence = min(best_score / 5.0, 1.0)
        primary = ROLE_LABELS.get(best_role, ROLE_LABELS["unknown"])

        # вторичные роли
        secondary = []
        for role, score in scores.items():
            if role != best_role and score >= best_score * 0.6 and score > 1.5:
                secondary.append(ROLE_LABELS.get(role, role))

        return {
            "primary_classification": primary,
            "confidence": confidence,
            "secondary_classifications": secondary,
            "debug_scores": scores,
        }

    def classify_project(self, data: Dict) -> Dict:
        text = data.get("full_text", "").lower()
        stage = data.get("investment_stage") or ""
        theme = data.get("theme") or ""

        relevance = self._score_text(text, self.project_keywords)
        stage_bonus = {
            "pre-seed": 1,
            "seed": 2,
            "series a": 3,
            "series b": 3.5,
            "series c": 4,
        }.get(stage.lower(), 0.5)

        priority_theme = 1.5 if theme in ["AI/ML", "FinTech", "SaaS", "HealthTech"] else 1.0
        total = relevance + stage_bonus + priority_theme

        return {
            "relevance_score": min(total / 10.0, 1.0),
            "is_promising": total >= 5.0,
            "recommendation": self._recommendation(total),
        }

    def _recommendation(self, total: float) -> str:
        if total >= 8:
            return "Горячий лид: смотрите срочно, есть потенциал закрыть раунд."
        if total >= 5:
            return "Интересно: добавить в воронку, обсудить первые шаги."
        if total >= 3:
            return "На наблюдении: следить за обновлениями, уточнить метрики."
        return "Слабая релевантность: можно отложить."

    def enrich_data(self, data: Dict) -> Dict:
        enriched = data.copy()
        if data.get("type") == "project":
            classification = self.classify_project(data)
            enriched.update({
                "project_relevance": classification["relevance_score"],
                "is_promising": classification["is_promising"],
                "recommendation": classification["recommendation"],
            })
        else:
            classification = self.classify_person(data)
            enriched.update({
                "person_classification": classification["primary_classification"],
                "classification_confidence": classification["confidence"],
                "secondary_roles": ", ".join(classification["secondary_classifications"]),
            })
        return enriched


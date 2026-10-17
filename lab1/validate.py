import re
import sys
from difflib import SequenceMatcher
from typing import List, Tuple
from srs_model import Specification, load_srs

# Допустимі типи вимог згідно з Таблицею 1.2
ALLOWED_TYPES = {
    "functional",
    "operational",
    "performance",
    "security",
    "cultural",
    "constraint",
}

# Шаблон ID: R1, R1.1, N1, C1
ID_PATTERN = re.compile(r"^([RNC]\d+)(\.\d+)?$")

# Словник розмитих слів (не менше 8 коренів/слів) - Перевірка 4
VAGUE_WORDS = [
    "зручн",
    "швидк",
    "прост",
    "надійн",
    " інтуїтивн",
    "мінімальн",
    "максимальн",
    "достатн",
    "оптимальн",
    "ефективн",
]

# Заборонені слова реалізації (Власна перевірка 9)
IMPLEMENTATION_WORDS = [
    "кнопк",
    "таблиц",
    "mysql",
    "postgresql",
    "sql",
    "база даних",
    "html",
]


def clean_for_comparison(text: str) -> str:
    """Нормалізує текст (нижній регістр, без пунктуації та зайвих пробілів) перед порівнянням."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def validate_specification(spec: Specification) -> List[Tuple[str, str, str]]:
    """
    Перевіряє специфікацію та повертає список кортежів:
    (id_елемента, тип_дефекту, опис_дефекту)
    """
    defects: List[Tuple[str, str, str]] = []
    seen_ids = set()
    all_ids = {r.id for r in spec.requirements}

    for idx, req in enumerate(spec.requirements):
        req_id = req.id
        text_norm = " ".join(req.text.split())
        text_lower = text_norm.lower()

        # 1. Перевірка унікальності та формату ID
        if req_id in seen_ids:
            defects.append((req_id, "надлишковість", f"дублікат ID {req_id}"))
        seen_ids.add(req_id)

        if not ID_PATTERN.match(req_id):
            defects.append((req_id, "формат", f"ID '{req_id}' не відповідає шаблону R1 / R1.1 / N1 / C1"))

        # 2. Перевірка типу вимоги
        if req.type not in ALLOWED_TYPES:
            defects.append((req_id, "формат", f"неприпустимий тип вимоги '{req.type}'"))

        # 3. Текст починається з «ІС повинна» або «Система повинна»
        if not (text_norm.startswith("ІС повинна") or text_norm.startswith("Система повинна")):
            defects.append((req_id, "формулювання", "немає «ІС повинна…»"))

        # 4. Перевірка на розмиті слова (неоднозначність)
        for vague in VAGUE_WORDS:
            if vague.strip() in text_lower:
                defects.append((req_id, "неоднозначність", f"розмите слово «{vague.strip()}…»"))

        # 5. Вимога продуктивності містить числовий критерій
        if req.type == "performance":
            if not re.search(r"\d+", text_norm):
                defects.append((req_id, "неперевірюваність", "немає числового критерію"))

        # 6. Пріоритет – ціле число 1–5 (для всіх, крім обмежень)
        if req.type != "constraint":
            if not isinstance(req.priority, int) or isinstance(req.priority, bool) or not (1 <= req.priority <= 5):
                defects.append((req_id, "пріоритет", "пріоритет має бути 1..5"))

        # 7. Батьківська вимога існує, а ID підвимоги продовжує ID батька
        if req.parent or "." in req_id:
            if not req.parent:
                defects.append((req_id, "нетрасованість", "для складеного ID не вказано поле parent"))
            else:
                if req.parent not in all_ids:
                    defects.append((req_id, "нетрасованість", f"немає батька {req.parent}"))
                if not req_id.startswith(f"{req.parent}."):
                    defects.append((req_id, "нетрасованість", f"ID підвимоги {req_id} не продовжує ID батька {req.parent}"))
        # 8. Схожість текстів вимог >= 85% (difflib)
        clean_current = clean_for_comparison(text_norm)
        for prev_req in spec.requirements[:idx]:
            clean_prev = clean_for_comparison(prev_req.text)
            ratio = SequenceMatcher(None, clean_current, clean_prev).ratio()
            if ratio >= 0.85:
                percent = int(round(ratio * 100))
                defects.append((req_id, "надлишковість", f"схожа на {prev_req.id} ({percent}%)"))
        # 9. Власна перевірка 1: заборонені слова технічної реалізації та UI
        for impl_word in IMPLEMENTATION_WORDS:
            if impl_word in text_lower:
                defects.append((req_id, "проєктування", f"містить деталь реалізації «{impl_word}…»"))
        # 10. Власна перевірка 2: узгодженість обмежень (constraint без пріоритету)
        if req.type == "constraint" and req.priority is not None:
            defects.append((req_id, "пріоритет", "обмеження (constraint) не повинно мати пріоритету"))
        if req_id.startswith("C") and req.type != "constraint":
            defects.append((req_id, "формат", "вимога з префіксом C повинна мати тип constraint"))
    # 11. Власна перевірка 3: кожна User Story має бути джерелом хоча б однієї вимоги
    all_sources = " ".join(r.source for r in spec.requirements)
    for us in spec.user_stories:
        if us.id not in all_sources:
            defects.append((us.id, "неповнота", f"користувацька історія {us.id} не покрита жодною вимогою у полі source"))
    return defects
def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "srs.yaml"
    spec = load_srs(filepath)
    defects = validate_specification(spec)
    for req_id, defect_type, message in defects:
        print(f"{req_id:<6} [{defect_type}] {message}")
    print(f"Перевірено {len(spec.requirements)} вимог, знайдено {len(defects)} дефектів")
    sys.exit(1 if defects else 0)
if __name__ == "__main__":
    main()
import pytest
from srs_model import Requirement, Specification, SystemRequest, UserStory, load_srs
from validate import validate_specification


def make_spec(reqs=None, user_stories=None) -> Specification:
    """Допоміжна функція для створення мінімальної специфікації в тестах."""
    sr = SystemRequest(
        sponsor="Спонсор",
        business_need="Потреба",
        business_requirements=["БВ1"],
        business_value=["БЦ1"],
        constraints=["Обм1"],
    )
    if user_stories is None:
        user_stories = [UserStory(id="US-01", text="Історія 1")]
    if reqs is None:
        reqs = [
            Requirement(
                id="R1",
                type="functional",
                text="ІС повинна реєструвати бронювання столика на обраний час.",
                priority=1,
                source="US-01",
            )
        ]
    return Specification(
        project="Тестовий Ресторан",
        system_request=sr,
        stakeholders=["Гість"],
        user_stories=user_stories,
        requirements=reqs,
    )


def test_clean_srs_yaml_has_no_defects():
    """Перевіряє, що робоча специфікація srs.yaml не містить жодного дефекту."""
    spec = load_srs("srs.yaml")
    defects = validate_specification(spec)
    assert defects == [], f"Знайдено неочікувані дефекти: {defects}"


def test_check_1_invalid_and_duplicate_id():
    """Перевірка 1: шаблон ID та унікальність."""
    r1 = Requirement(id="BAD_ID", type="functional", text="ІС повинна формувати чек.", priority=1, source="US-01")
    r2 = Requirement(id="BAD_ID", type="functional", text="ІС повинна закривати рахунок столика.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r1, r2]))
    types = [d[1] for d in defects]
    assert "формат" in types
    assert "надлишковість" in types


def test_check_2_invalid_type():
    """Перевірка 2: неприпустимий тип вимоги."""
    r = Requirement(id="R1", type="unknown_type", text="ІС повинна зберігати меню.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "формат" and "тип" in d[2] for d in defects)


def test_check_3_bad_phrasing():
    """Перевірка 3: текст не починається з 'ІС повинна'."""
    r = Requirement(id="R1", type="functional", text="Офіціант має змогу відкрити стіл.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "формулювання" for d in defects)


def test_check_4_vague_words():
    """Перевірка 4: розмиті слова у формулюванні."""
    r = Requirement(id="R1", type="functional", text="ІС повинна надавати зручний пошук страв.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "неоднозначність" for d in defects)


def test_check_5_performance_without_numbers():
    """Перевірка 5: вимога продуктивності без числового критерію."""
    r = Requirement(id="N1", type="performance", text="ІС повинна миттєво оновлювати чергу кухаря.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "неперевірюваність" for d in defects)


def test_check_6_invalid_priority():
    """Перевірка 6: пріоритет поза межами 1..5."""
    r = Requirement(id="R1", type="functional", text="ІС повинна друкувати звіт за зміну.", priority=7, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "пріоритет" for d in defects)


def test_check_7_broken_parent_traceability():
    """Перевірка 7: відсутня батьківська вимога або невідповідний префікс ID."""
    r = Requirement(id="R2.1", parent="R9", type="functional", text="ІС повинна скасовувати бронь.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "нетрасованість" for d in defects)


def test_check_8_similar_texts_redundancy():
    """Перевірка 8: дві вимоги зі схожістю тексту >= 85%."""
    r1 = Requirement(id="R1", type="functional", text="ІС повинна автоматично розподіляти страви між цехами кухні.", priority=1, source="US-01")
    r2 = Requirement(id="R2", type="functional", text="ІС повинна автоматично розподіляти страви між цехами кухні!", priority=2, source="US-01")
    defects = validate_specification(make_spec([r1, r2]))
    assert any(d[1] == "надлишковість" and "схожа на R1" in d[2] for d in defects)


def test_check_9_implementation_details():
    """Власна перевірка 9: заборонені деталі реалізації (кнопка, MySQL)."""
    r = Requirement(id="R1", type="functional", text="ІС повинна мати кнопку для запису в базу MySQL.", priority=1, source="US-01")
    defects = validate_specification(make_spec([r]))
    assert any(d[1] == "проєктування" for d in defects)


def test_check_10_constraint_with_priority():
    """Власна перевірка 10: обмеження не повинно мати пріоритету."""
    c = Requirement(id="C1", type="constraint", text="ІС повинна працювати у браузері.", priority=2, source="US-01")
    defects = validate_specification(make_spec([c]))
    assert any(d[1] == "пріоритет" and "обмеження" in d[2] for d in defects)


def test_check_11_uncovered_user_story():
    """Власна перевірка 11: користувацька історія не прив'язана до жодної вимоги."""
    stories = [UserStory(id="US-01", text="Історія 1"), UserStory(id="US-02", text="Непокрита історія")]
    defects = validate_specification(make_spec(user_stories=stories))
    assert any(d[0] == "US-02" and d[1] == "неповнота" for d in defects)
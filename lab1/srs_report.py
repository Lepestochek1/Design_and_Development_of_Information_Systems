import sys
from collections import Counter
from srs_model import Specification, load_srs
TYPE_TITLES = {
    "functional": "3.1. Функціональні вимоги (Functional)",
    "performance": "3.2. Вимоги до продуктивності (Performance)",
    "operational": "3.3. Експлуатаційні вимоги (Operational)",
    "security": "3.4. Вимоги безпеки (Security)",
    "cultural": "3.5. Культурні та політичні вимоги (Cultural)",
    "constraint": "3.6. Обмеження (Constraints)",
}
def generate_markdown(spec: Specification) -> str:
    lines = []

    # Заголовок документа
    lines.append(f"# Специфікація вимог до програмного забезпечення (SRS)")
    lines.append(f"**Проєкт:** {spec.project}\n")

    # Розділ 1. Вступ
    lines.append("## 1. Вступ")
    lines.append(f"**Бізнес-спонсор:** {spec.system_request.sponsor}\n")
    lines.append(f"**Бізнес-потреба:** {spec.system_request.business_need}\n")

    lines.append("### Бізнес-цінність")
    for val in spec.system_request.business_value:
        lines.append(f"- {val}")
    lines.append("")

    # Розділ 2. Загальний опис
    lines.append("## 2. Загальний опис")
    lines.append("### 2.1. Основні функції продукту (Бізнес-вимоги)")
    for br in spec.system_request.business_requirements:
        lines.append(f"- {br}")
    lines.append("")

    lines.append("### 2.2. Класи та характеристики користувачів (Стейкхолдери)")
    for sh in spec.stakeholders:
        lines.append(f"- {sh}")
    lines.append("")

    lines.append("### 2.3. Користувацькі історії (User Stories)")
    for us in spec.user_stories:
        lines.append(f"- **{us.id}:** {us.text}")
    lines.append("")

    lines.append("### 2.4. Загальні обмеження")
    for con in spec.system_request.constraints:
        lines.append(f"- {con}")
    lines.append("")

    # Розділ 3. Детальні вимоги
    lines.append("## 3. Специфічні вимоги")

    # Словник підвимог за ID батьківської вимоги
    children_map = {}
    for req in spec.requirements:
        if req.parent:
            children_map.setdefault(req.parent, []).append(req)

    for req_type, section_title in TYPE_TITLES.items():
        top_level_reqs = [
            r for r in spec.requirements if r.type == req_type and not r.parent
        ]
        if not top_level_reqs:
            continue

        lines.append(f"### {section_title}")
        for req in top_level_reqs:
            prio_str = f" [Пріоритет: {req.priority}]" if req.priority is not None else ""
            lines.append(f"- **{req.id}**{prio_str}: {req.text} *(Джерело: {req.source})*")

            # Виведення підвимог з відступом під батьківською вимогою
            for child in children_map.get(req.id, []):
                c_prio = f" [Пріоритет: {child.priority}]" if child.priority is not None else ""
                lines.append(
                    f"  - **{child.id}**{c_prio}: {child.text} *(Джерело: {child.source})*"
                )
        lines.append("")

    # Розділ 4. Статистика вимог
    lines.append("## 4. Статистика вимог")
    type_counts = Counter(r.type for r in spec.requirements)
    lines.append("### Розподіл за типами вимог")
    lines.append("| Тип вимоги | Кількість |")
    lines.append("| :--- | :---: |")
    for r_type in TYPE_TITLES.keys():
        if type_counts[r_type] > 0:
            lines.append(f"| `{r_type}` | {type_counts[r_type]} |")
    lines.append(f"| **Всього** | **{len(spec.requirements)}** |\n")
    prio_counts = Counter(r.priority for r in spec.requirements)
    lines.append("### Розподіл за пріоритетами")
    lines.append("| Пріоритет | Кількість |")
    lines.append("| :--- | :---: |")
    for p in sorted(k for k in prio_counts.keys() if k is not None):
        lines.append(f"| Пріоритет {p} | {prio_counts[p]} |")
    if None in prio_counts:
        lines.append(f"| Без пріоритету (обмеження) | {prio_counts[None]} |")
    lines.append(f"| **Всього** | **{len(spec.requirements)}** |\n")
    return "\n".join(lines)
def main():
    yaml_path = sys.argv[1] if len(sys.argv) > 1 else "srs.yaml"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "SRS.md"

    spec = load_srs(yaml_path)
    markdown_content = generate_markdown(spec)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Документ успішно згенеровано: {out_path}")


if __name__ == "__main__":
    main()
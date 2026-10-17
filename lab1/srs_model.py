from dataclasses import dataclass, field
from typing import List, Optional
import yaml
def normalize_text(text: str) -> str:
    """Нормалізує багаторядковий текст в один рядок без зайвих пробілів."""
    if not text:
        return ""
    return " ".join(str(text).split())
@dataclass
class SystemRequest:
    sponsor: str
    business_need: str
    business_requirements: List[str]
    business_value: List[str]
    constraints: List[str]
@dataclass
class UserStory:
    id: str
    text: str
@dataclass
class Requirement:
    id: str
    type: str
    text: str
    source: str
    priority: Optional[int] = None
    parent: Optional[str] = None


@dataclass
class Specification:
    project: str
    system_request: SystemRequest
    stakeholders: List[str]
    user_stories: List[UserStory] = field(default_factory=list)
    requirements: List[Requirement] = field(default_factory=list)


def load_srs(filepath: str) -> Specification:
    """Завантажує специфікацію вимог із YAML-файлу та нормалізує тексти."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sr_data = data["system_request"]
    system_request = SystemRequest(
        sponsor=normalize_text(sr_data["sponsor"]),
        business_need=normalize_text(sr_data["business_need"]),
        business_requirements=[normalize_text(item) for item in sr_data.get("business_requirements", [])],
        business_value=[normalize_text(item) for item in sr_data.get("business_value", [])],
        constraints=[normalize_text(item) for item in sr_data.get("constraints", [])],
    )

    user_stories = [
        UserStory(
            id=str(us["id"]).strip(),
            text=normalize_text(us["text"]),
        )
        for us in data.get("user_stories", [])
    ]

    requirements = [
        Requirement(
            id=str(req["id"]).strip(),
            type=str(req["type"]).strip(),
            text=normalize_text(req["text"]),
            source=normalize_text(req["source"]),
            priority=req.get("priority"),
            parent=str(req["parent"]).strip() if req.get("parent") else None,
        )
        for req in data.get("requirements", [])
    ]

    return Specification(
        project=normalize_text(data["project"]),
        system_request=system_request,
        stakeholders=[normalize_text(s) for s in data.get("stakeholders", [])],
        user_stories=user_stories,
        requirements=requirements,
    )
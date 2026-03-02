from enum import Enum
class LinguagemEnum(str, Enum):
    python = "python"
    java = "java"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member

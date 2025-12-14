import pygame
from typing import Dict, Tuple, Any, Optional

class Enum:
    class ObjectType:
        UI = 'type_ui'
        ENTITY = 'type_entity'

class Object:
    def __init__(self, position: Tuple[int, int], type: str = Enum.ObjectType.UI, **kwargs) -> None:

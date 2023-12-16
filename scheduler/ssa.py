from typing import NamedTuple
from .node import Node

Assignment = NamedTuple('Assignment', [('symbol', str), ('value', Node)])
External = NamedTuple('External', [('symbol', str)])

Step = Node | Assignment | External

"""
Routing algorithms for NoC topologies

Provides comprehensive routing algorithm implementations for Network-on-Chip:

Deterministic Algorithms:
- XYRouting: Dimension-ordered routing (X first, then Y)
- YXRouting: Dimension-ordered routing (Y first, then X)

Turn Model Algorithms (Partially Adaptive):
- WestFirstRouting: All westward movements first
- NorthLastRouting: All northward movements last
- NegativeFirstRouting: Negative directions (West/North) before positive

Advanced Adaptive Algorithms:
- OddEvenRouting: Column-parity-based turn restrictions
- FullyAdaptiveRouting: Maximum adaptivity with escape paths
- DuatoRouting: Duato's protocol with escape channels

All algorithms inherit from BaseRouting and can be used with any topology.
"""

from .base_routing import BaseRouting
from .xy_routing import XYRouting, YXRouting
from .west_first_routing import WestFirstRouting
from .north_last_routing import NorthLastRouting
from .negative_first_routing import NegativeFirstRouting
from .odd_even_routing import OddEvenRouting
from .fully_adaptive_routing import FullyAdaptiveRouting
from .duato_routing import DuatoRouting, ChannelType

__all__ = [
    # Base class
    'BaseRouting',
    
    # Deterministic algorithms
    'XYRouting',
    'YXRouting',
    
    # Turn model algorithms
    'WestFirstRouting',
    'NorthLastRouting',
    'NegativeFirstRouting',
    
    # Advanced adaptive algorithms
    'OddEvenRouting',
    'FullyAdaptiveRouting',
    'DuatoRouting',
    'ChannelType',
]

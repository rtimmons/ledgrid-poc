#!/usr/bin/env python3
"""
LED Grid Animation System

A plugin-based animation system for LED grids with hot-swapping capabilities.
"""

from .animation_base import AnimationBase, StatefulAnimationBase
from .plugin_loader import AnimationPluginLoader

__version__ = "1.0.0"
__all__ = ["AnimationBase", "StatefulAnimationBase", "AnimationPluginLoader"]

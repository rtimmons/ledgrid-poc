#!/usr/bin/env python3
"""
Base animation class and plugin system for LED Grid
"""

import time
import colorsys
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional


class AnimationBase(ABC):
    """Base class for all LED animations"""
    
    def __init__(self, controller, config: Dict[str, Any] = None):
        """
        Initialize animation
        
        Args:
            controller: LED controller instance
            config: Animation configuration parameters
        """
        self.controller = controller
        self.config = config or {}
        self.start_time = time.time()
        self.frame_count = 0
        self.is_running = False
        
        # Animation metadata
        self.name = getattr(self, 'ANIMATION_NAME', self.__class__.__name__)
        self.description = getattr(self, 'ANIMATION_DESCRIPTION', 'No description')
        self.author = getattr(self, 'ANIMATION_AUTHOR', 'Unknown')
        self.version = getattr(self, 'ANIMATION_VERSION', '1.0')
        
        # Default parameters that can be overridden
        self.default_params = {
            'speed': 1.0,
            'brightness': 1.0,
            'color_saturation': 1.0,
            'color_value': 1.0
        }
        
        # Merge default params with config
        self.params = {**self.default_params, **self.config}
    
    @abstractmethod
    def generate_frame(self, time_elapsed: float, frame_count: int) -> List[Tuple[int, int, int]]:
        """
        Generate a single frame of animation
        
        Args:
            time_elapsed: Time since animation started (seconds)
            frame_count: Number of frames rendered so far
            
        Returns:
            List of (r, g, b) tuples for all pixels
        """
        pass
    
    def get_parameter_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Return schema describing configurable parameters
        
        Returns:
            Dict with parameter definitions including type, range, description
        """
        return {
            'speed': {
                'type': 'float',
                'min': 0.1,
                'max': 5.0,
                'default': 1.0,
                'description': 'Animation speed multiplier'
            },
            'brightness': {
                'type': 'float',
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'description': 'Overall brightness (0.0 - 1.0)'
            },
            'color_saturation': {
                'type': 'float',
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'description': 'Color saturation (0.0 - 1.0)'
            },
            'color_value': {
                'type': 'float',
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'description': 'Color value/brightness (0.0 - 1.0)'
            }
        }
    
    def update_parameters(self, new_params: Dict[str, Any]):
        """Update animation parameters in real-time"""
        self.params.update(new_params)
    
    def get_info(self) -> Dict[str, Any]:
        """Get animation metadata"""
        return {
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'parameters': self.get_parameter_schema(),
            'current_params': self.params
        }
    
    def start(self):
        """Called when animation starts"""
        self.start_time = time.time()
        self.frame_count = 0
        self.is_running = True
    
    def stop(self):
        """Called when animation stops"""
        self.is_running = False
    
    def cleanup(self):
        """Called when animation is being destroyed"""
        self.stop()
    
    # Utility methods for common operations
    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB (0-255)"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)
    
    def apply_brightness(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Apply brightness parameter to a color"""
        r, g, b = color
        brightness = self.params.get('brightness', 1.0)
        return (
            int(r * brightness),
            int(g * brightness),
            int(b * brightness)
        )
    
    def get_pixel_count(self) -> int:
        """Get total number of pixels"""
        return self.controller.total_leds
    
    def get_strip_info(self) -> Tuple[int, int]:
        """Get (strip_count, leds_per_strip)"""
        return self.controller.strip_count, self.controller.leds_per_strip

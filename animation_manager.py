#!/usr/bin/env python3
"""
Animation Manager Service

Coordinates between LED controller, animation plugins, and web interface.
Handles animation switching, parameter updates, and frame generation.
"""

import time
import threading
import traceback
from typing import Optional, Dict, Any, List
from pathlib import Path

from animation_system import AnimationBase, AnimationPluginLoader
from led_controller_spi import LEDController


class AnimationManager:
    """Manages animation playback and plugin system"""
    
    def __init__(self, controller: LEDController, plugins_dir: str = "animations"):
        """
        Initialize animation manager
        
        Args:
            controller: LED controller instance
            plugins_dir: Directory containing animation plugins
        """
        self.controller = controller
        self.plugin_loader = AnimationPluginLoader(plugins_dir)
        
        # Animation state
        self.current_animation: Optional[AnimationBase] = None
        self.current_animation_name: Optional[str] = None
        self.is_running = False
        self.target_fps = 50
        self.frame_count = 0
        self.start_time = 0.0
        
        # Threading
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Performance tracking
        self.fps_history = []
        self.last_fps_update = 0.0
        
        # Load all plugins on startup
        self.refresh_plugins()
    
    def refresh_plugins(self) -> Dict[str, Any]:
        """Reload all animation plugins"""
        try:
            plugins = self.plugin_loader.load_all_plugins()
            print(f"✓ Loaded {len(plugins)} animation plugins")
            return {name: self.plugin_loader.get_plugin_info(name) for name in plugins.keys()}
        except Exception as e:
            print(f"✗ Error loading plugins: {e}")
            traceback.print_exc()
            return {}
    
    def list_animations(self) -> List[Dict[str, Any]]:
        """Get list of available animations with metadata"""
        animations = []
        for plugin_name in self.plugin_loader.list_plugins():
            info = self.plugin_loader.get_plugin_info(plugin_name)
            if info:
                animations.append(info)
        return animations
    
    def get_animation_info(self, animation_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a specific animation"""
        return self.plugin_loader.get_plugin_info(animation_name)
    
    def start_animation(self, animation_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Start playing an animation
        
        Args:
            animation_name: Name of animation plugin to start
            config: Animation configuration parameters
            
        Returns:
            True if started successfully
        """
        try:
            # Stop current animation if running
            self.stop_animation()
            
            # Get animation class
            animation_class = self.plugin_loader.get_plugin(animation_name)
            if animation_class is None:
                print(f"✗ Animation not found: {animation_name}")
                return False
            
            # Create animation instance
            self.current_animation = animation_class(self.controller, config or {})
            self.current_animation_name = animation_name
            
            # Start animation
            self.current_animation.start()
            self.is_running = True
            self.stop_event.clear()
            self.frame_count = 0
            self.start_time = time.time()
            
            # Start animation thread
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()
            
            print(f"✓ Started animation: {animation_name}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start animation {animation_name}: {e}")
            traceback.print_exc()
            return False
    
    def stop_animation(self):
        """Stop current animation"""
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            
            if self.animation_thread and self.animation_thread.is_alive():
                self.animation_thread.join(timeout=1.0)
            
            if self.current_animation:
                self.current_animation.stop()
                self.current_animation.cleanup()
                self.current_animation = None
            
            self.current_animation_name = None
            
            # Clear LEDs
            self.controller.clear()
            
            print("✓ Animation stopped")
    
    def update_animation_parameters(self, params: Dict[str, Any]) -> bool:
        """Update current animation parameters in real-time"""
        if self.current_animation:
            try:
                self.current_animation.update_parameters(params)
                print(f"✓ Updated animation parameters: {params}")
                return True
            except Exception as e:
                print(f"✗ Failed to update parameters: {e}")
                return False
        return False
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current animation status and performance info"""
        status = {
            'is_running': self.is_running,
            'current_animation': self.current_animation_name,
            'frame_count': self.frame_count,
            'uptime': time.time() - self.start_time if self.is_running else 0,
            'target_fps': self.target_fps,
            'actual_fps': self._calculate_fps(),
            'led_info': {
                'total_leds': self.controller.total_leds,
                'strip_count': self.controller.strip_count,
                'leds_per_strip': self.controller.leds_per_strip
            }
        }
        
        if self.current_animation:
            status['animation_info'] = self.current_animation.get_info()
        
        return status
    
    def _animation_loop(self):
        """Main animation loop running in separate thread"""
        frame_time = 1.0 / self.target_fps
        
        while self.is_running and not self.stop_event.is_set():
            loop_start = time.time()
            
            try:
                if self.current_animation:
                    # Generate frame
                    time_elapsed = time.time() - self.start_time
                    colors = self.current_animation.generate_frame(time_elapsed, self.frame_count)
                    
                    # Send to LEDs
                    self.controller.set_all_pixels(colors)
                    
                    self.frame_count += 1
                    
                    # Update FPS tracking
                    self._update_fps_tracking()
                
            except Exception as e:
                print(f"✗ Animation loop error: {e}")
                traceback.print_exc()
                break
            
            # Sleep to maintain target FPS
            loop_time = time.time() - loop_start
            sleep_time = max(0, frame_time - loop_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _update_fps_tracking(self):
        """Update FPS calculation"""
        now = time.time()
        if now - self.last_fps_update >= 1.0:  # Update every second
            if self.start_time > 0:
                elapsed = now - self.start_time
                current_fps = self.frame_count / elapsed if elapsed > 0 else 0
                self.fps_history.append(current_fps)
                
                # Keep only last 10 seconds of history
                if len(self.fps_history) > 10:
                    self.fps_history.pop(0)
            
            self.last_fps_update = now
    
    def _calculate_fps(self) -> float:
        """Calculate current FPS"""
        if not self.fps_history:
            return 0.0
        return sum(self.fps_history) / len(self.fps_history)
    
    def save_animation(self, name: str, code: str) -> bool:
        """Save new animation plugin"""
        return self.plugin_loader.save_plugin(name, code)
    
    def reload_animation(self, name: str) -> bool:
        """Reload specific animation plugin"""
        try:
            self.plugin_loader.reload_plugin(name)
            return True
        except Exception as e:
            print(f"✗ Failed to reload animation {name}: {e}")
            return False

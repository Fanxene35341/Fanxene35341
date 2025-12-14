from re import S
from typing import Any, Optional
import pygame, time

pygame.init()

Screen_Width = 800
Screen_Height = 600

screen = pygame.display.set_mode((Screen_Width, Screen_Height), pygame.RESIZABLE | pygame.WINDOWMAXIMIZED)
clock = pygame.time.Clock()
FPS = 60

class KeywordArgs:
    """Container for Object keyword arguments to avoid retyping"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get(self) -> dict[str, Any]:
        """Return a dictionary"""
        return self.kwargs
    
    def update(self, **new_kwargs):
        """Update kwargs with new values"""
        self.kwargs.update(new_kwargs)
    
    def edit_kwargs(self, **kwargs):
        """Edit kwargs with new values (alias for update)"""
        self.kwargs.update(kwargs)
    
    def __repr__(self):
        return f"KeywordArgs({self.kwargs})"


class Object:
    _instances = []
    
    def __init__(self, x, y, size, **kwargs):
        """
        Initialize a simple game object.
        
        Args:
            x: X position
            y: Y position
            size: Size of object - int for circle/square, tuple[int, int] for rectangle
            **kwargs: Additional optional parameters including color
        """
        self.base_kwargs = kwargs.copy()
        
        # Process kwargs first to get shape_type
        self._process_kwargs(kwargs)
        
        # Handle size based on shape type
        if self.shape_type == 'circle':
            if isinstance(size, tuple):
                print(f'Error: Unexpected Size value for {self.shape_type}')
                self.size = size[0]  # Use first element as radius
                self.width = size[0]
                self.height = size[0]
            elif isinstance(size, int):
                self.size = size
                self.width = size * 2  # Diameter
                self.height = size * 2
            else:
                self.size = size
                self.width = size
                self.height = size
        else:  # rect
            if isinstance(size, tuple):
                self.size = size
                self.width = size[0]
                self.height = size[1]
            elif isinstance(size, int):
                self.size = (size, size)
                self.width = size
                self.height = size
            else:
                self.size = (size, size)
                self.width = size
                self.height = size
        
        # Parse color after processing kwargs
        self.color = self._parse_color(self.base_color)
        
        # Set position based on position_center
        if self.position_center:
            self.x = x - self.width // 2
            self.y = y - self.height // 2
            self.center_x = x
            self.center_y = y
        else:
            self.x = x
            self.y = y
            self.center_x = x + self.width // 2
            self.center_y = y + self.height // 2
        
        self._create_rect()
        
        # Initialize text surface
        self._init_text()
        
        # Store initial screen size for relative positioning
        if self.relative_to_screen:
            display_surface = pygame.display.get_surface()
            if display_surface:
                self.screen_width = display_surface.get_width()
                self.screen_height = display_surface.get_height()
                self.screen_width_original = self.screen_width  # Store original screen size
                self.screen_height_original = self.screen_height
                # Calculate position as ratio of screen size
                if self.position_center:
                    self.relative_x_ratio = self.center_x / self.screen_width
                    self.relative_y_ratio = self.center_y / self.screen_height
                else:
                    self.relative_x_ratio = self.x / self.screen_width
                    self.relative_y_ratio = self.y / self.screen_height
        
        # State management
        self.is_hovered = False
        self.is_clicked = False
        self.is_colliding = False
        self.current_state = 'normal'
        self.temp_kwargs = None
        
        # Animation state
        self.is_animating = False
        self.animation_start_time = None
        self.animation_current_point = 0
        self.animation_start_pos = None
        
        # Add to instances
        Object._instances.append(self)
    
    def _parse_color(self, color):
        """Parse color from tuple or string"""
        if isinstance(color, str):
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255),
                'gray': (128, 128, 128),
                'grey': (128, 128, 128)
            }
            return color_map.get(color.lower(), (255, 255, 255))
        return color
    
    def _create_rect(self):
        """Create rect based on border settings"""
        if self.border_includes:
            # Border is inside the object
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        else:
            # Border grows outward
            offset = self.border_thickness if not self.border_thickness_grow else 0
            self.rect = pygame.Rect(
                self.x - offset,
                self.y - offset,
                self.width + offset * 2,
                self.height + offset * 2
            )
    
    def _process_kwargs(self, kwargs):
        """Process all keyword arguments and set default values"""
        # Color property
        self.base_color: tuple | str = kwargs.get('color', (255, 255, 255))
        
        # Border properties
        self.border_radius: int = kwargs.get('border_radius', 0)
        self.border_radius_corners: list[str] = kwargs.get('border_radius_corners', ['topleft', 'topright', 'bottomleft', 'bottomright'])
        self.border_thickness: int = kwargs.get('border_thickness', 0)
        self.border_color: tuple = self._parse_color(kwargs.get('border_color', (0, 0, 0)))
        self.border_thickness_grow: bool = kwargs.get('border_thickness_grow', False)
        self.border_includes: bool = kwargs.get('border_includes', True)
        
        # Position properties
        self.position_center: bool = kwargs.get('position_center', False)
        
        # Image properties
        self.image_replacement: pygame.Surface | None = kwargs.get('image_replacement', None)
        self.image_contains: tuple | None = kwargs.get('image_contains', None)
        self.texture: pygame.Surface | None = kwargs.get('texture', None)
        
        # Text properties
        self.text: str = kwargs.get('text', '')
        self.text_reposition_type: str = kwargs.get('text_reposition_type', 'alignment')
        self.text_alignment: str = kwargs.get('text_alignment', 'center')
        self.text_position: tuple[int, int] = kwargs.get('text_position', (0, 0))
        self.text_font: str | None = kwargs.get('text_font', None)
        self.text_exfonts: str | None = kwargs.get('text_exfonts', None)
        self.text_size: int = kwargs.get('text_size', 20)
        self.text_size_original: int = kwargs.get('text_size', 20)  # Store original size
        self.text_color: tuple | str = kwargs.get('text_color', (0, 0, 0))
        
        # Content properties
        self.content_padding: int = kwargs.get('content_padding', 0)
        
        # UI properties
        self.ui_type: bool = kwargs.get('ui_type', False)
        
        # Interactive kwargs
        self.hover_kwargs: KeywordArgs | dict | None = kwargs.get('hover_kwargs', None)
        self.click_kwargs: KeywordArgs | dict | None = kwargs.get('click_kwargs', None)
        self.rect_collides_kwargs: tuple | None = kwargs.get('rect_collides_kwargs', None)
        
        # Shape properties
        self.shape_type: str = kwargs.get('shape_type', 'rect')
        
        # Animation properties
        self.animated: bool = kwargs.get('animated', False)
        self.animation_type: str = kwargs.get('animation_type', 'loop')
        self.animation_points: list[tuple[int, int]] = kwargs.get('animation_points', [])
        self.animation_duration: int | float = kwargs.get('animation_duration', 1.0)
        
        # ID
        self.uid: str | None = kwargs.get('uid', None)
        
        # Screen relative positioning
        self.relative_to_screen: bool = kwargs.get('relative_to_screen', False)
        self.screen_width: int | None = None
        self.screen_height: int | None = None
        self.relative_x_ratio: float | None = None
        self.relative_y_ratio: float | None = None
    
    def _apply_temp_kwargs(self, kwargs_obj):
        """Temporarily apply kwargs from KeywordArgs object"""
        if isinstance(kwargs_obj, KeywordArgs):
            kwargs = kwargs_obj.get()
        else:
            kwargs = kwargs_obj
        
        if kwargs:
            self.temp_kwargs = {}
            for key, value in kwargs.items():
                self.temp_kwargs[key] = getattr(self, key, None)
                setattr(self, key, value)
            
            # Re-parse color if changed
            if 'color' in kwargs:
                self.color = self._parse_color(kwargs['color'])
            if 'border_color' in kwargs:
                self.border_color = self._parse_color(kwargs['border_color'])
            
            # Re-init text if text properties changed
            if any(k.startswith('text') for k in kwargs.keys()):
                self._init_text()
    
    def _restore_kwargs(self):
        """Restore original kwargs"""
        if self.temp_kwargs:
            for key, value in self.temp_kwargs.items():
                setattr(self, key, value)
            self.temp_kwargs = None
            self._init_text()
    
    def _init_text(self):
        """Initialize text surface if text is provided"""
        self.text_surface = None
        self.text_rect = None
        
        if self.text:
            # Load font
            if self.text_exfonts:
                font = pygame.font.Font(self.text_exfonts, self.text_size)
            elif self.text_font:
                font = pygame.font.SysFont(self.text_font, self.text_size)
            else:
                font = pygame.font.Font(None, self.text_size)
            
            # Render text
            text_color = self._parse_color(self.text_color)
            self.text_surface = font.render(self.text, True, text_color)
            self.text_rect = self.text_surface.get_rect()
            self._position_text()
    
    def _position_text(self):
        """Position text based on text_reposition_type"""
        if not self.text_rect:
            return
        
        if self.text_reposition_type == 'alignment':
            alignments = {
                'center': (self.width // 2 - self.text_rect.width // 2, 
                          self.height // 2 - self.text_rect.height // 2),
                'top': (self.width // 2 - self.text_rect.width // 2, 
                       self.content_padding),
                'bottom': (self.width // 2 - self.text_rect.width // 2, 
                          self.height - self.text_rect.height - self.content_padding),
                'left': (self.content_padding, 
                        self.height // 2 - self.text_rect.height // 2),
                'right': (self.width - self.text_rect.width - self.content_padding, 
                         self.height // 2 - self.text_rect.height // 2),
                'topleft': (self.content_padding, self.content_padding),
                'topright': (self.width - self.text_rect.width - self.content_padding, 
                            self.content_padding),
                'bottomleft': (self.content_padding, 
                              self.height - self.text_rect.height - self.content_padding),
                'bottomright': (self.width - self.text_rect.width - self.content_padding,
                               self.height - self.text_rect.height - self.content_padding)
            }
            
            offset = alignments.get(self.text_alignment, (0, 0))
            self.text_rect.x = self.x + offset[0]
            self.text_rect.y = self.y + offset[1]
        
        elif self.text_reposition_type == 'position':
            self.text_rect.x = self.x + self.text_position[0]
            self.text_rect.y = self.y + self.text_position[1]
    
    def _get_border_radius_dict(self):
        """Convert border_radius_corners list to pygame border radius dict"""
        radius_dict = {
            'top_left_radius': 0,
            'top_right_radius': 0,
            'bottom_left_radius': 0,
            'bottom_right_radius': 0
        }
        
        corner_map = {
            'topleft': 'top_left_radius',
            'topright': 'top_right_radius',
            'bottomleft': 'bottom_left_radius',
            'bottomright': 'bottom_right_radius'
        }
        
        for corner in self.border_radius_corners:
            if corner in corner_map:
                radius_dict[corner_map[corner]] = self.border_radius
        
        return radius_dict
    
    def update(self):
        """Update object state"""
        self.center_x = self.x + self.width // 2
        self.center_y = self.y + self.height // 2
        self._create_rect()
        self._position_text()
        self._init_text()
        
        # Update animation
        if self.is_animating and self.animation_points:
            self._update_animation()
    
    def _update_animation(self):
        """Update animation state"""
        if not self.animation_start_time:
            self.animation_start_time = time.time()
            self.animation_start_pos = (self.x, self.y) if not self.position_center else (self.center_x, self.center_y)
        
        elapsed = time.time() - self.animation_start_time
        progress = min(elapsed / self.animation_duration, 1.0)
        
        if self.animation_current_point < len(self.animation_points):
            target = self.animation_points[self.animation_current_point]
            start = self.animation_start_pos
            
            # Interpolate position
            new_x = start[0] + (target[0] - start[0]) * progress
            new_y = start[1] + (target[1] - start[1]) * progress
            
            if self.position_center:
                self.x = new_x - self.width // 2
                self.y = new_y - self.height // 2
                self.center_x = new_x
                self.center_y = new_y
            else:
                self.x = new_x
                self.y = new_y
            
            # Move to next point
            if progress >= 1.0:
                self.animation_current_point += 1
                self.animation_start_time = time.time()
                self.animation_start_pos = (new_x, new_y) if self.position_center else (self.x, self.y)
                
                if self.animation_current_point >= len(self.animation_points):
                    if self.animation_type == 'loop':
                        self.animation_current_point = 0
                    else:
                        self.is_animating = False
    
    def draw(self, surface):
        """Draw the object on the given surface"""
        # Draw image replacement if provided
        if self.image_replacement:
            scaled_image = pygame.transform.scale(self.image_replacement, (self.width, self.height))
            surface.blit(scaled_image, (self.x, self.y))
        elif self.texture:
            # Draw texture as background
            scaled_texture = pygame.transform.scale(self.texture, (self.width, self.height))
            surface.blit(scaled_texture, (self.x, self.y))
        else:
            # Draw the main shape
            if self.shape_type == 'circle':
                radius = self.width // 2 if isinstance(self.size, tuple) else self.size
                pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), radius)
            else:
                draw_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                if self.border_radius > 0:
                    pygame.draw.rect(surface, self.color, draw_rect, border_radius=self.border_radius)
                else:
                    pygame.draw.rect(surface, self.color, draw_rect)
        
        # Draw border if thickness is specified
        if self.border_thickness > 0:
            if self.shape_type == 'circle':
                radius = self.width // 2 if isinstance(self.size, tuple) else self.size
                pygame.draw.circle(surface, self.border_color, (self.center_x, self.center_y), 
                                 radius, width=self.border_thickness)
            else:
                draw_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                if self.border_radius > 0:
                    pygame.draw.rect(surface, self.border_color, draw_rect, 
                                   width=self.border_thickness, 
                                   border_radius=self.border_radius)
                else:
                    pygame.draw.rect(surface, self.border_color, draw_rect, width=self.border_thickness)
        
        # Draw image_contains if provided
        if self.image_contains:
            img_surface = self.image_contains[0]
            img_data = self.image_contains[1] if len(self.image_contains) > 1 else None
            
            if isinstance(img_data, tuple) and len(img_data) == 2 and isinstance(img_data[0], int):
                surface.blit(img_surface, (self.x + img_data[0], self.y + img_data[1]))
            elif isinstance(img_data, str):
                img_rect = img_surface.get_rect()
                positions = {
                    'top': (self.x + self.width // 2 - img_rect.width // 2, self.y + self.content_padding),
                    'bottom': (self.x + self.width // 2 - img_rect.width // 2, 
                              self.y + self.height - img_rect.height - self.content_padding),
                    'left': (self.x + self.content_padding, self.y + self.height // 2 - img_rect.height // 2),
                    'right': (self.x + self.width - img_rect.width - self.content_padding, 
                             self.y + self.height // 2 - img_rect.height // 2),
                    'center': (self.x + self.width // 2 - img_rect.width // 2, 
                              self.y + self.height // 2 - img_rect.height // 2),
                    'topleft': (self.x + self.content_padding, self.y + self.content_padding),
                    'topright': (self.x + self.width - img_rect.width - self.content_padding, 
                                self.y + self.content_padding),
                    'bottomleft': (self.x + self.content_padding, 
                                  self.y + self.height - img_rect.height - self.content_padding),
                    'bottomright': (self.x + self.width - img_rect.width - self.content_padding,
                                   self.y + self.height - img_rect.height - self.content_padding)
                }
                pos = positions.get(img_data, (self.x, self.y))
                surface.blit(img_surface, pos)
            else:
                surface.blit(img_surface, (self.x, self.y))
        
        # Draw text if provided
        if self.text_surface and self.text_rect:
            surface.blit(self.text_surface, self.text_rect)
    
    def move(self, x=None, y=None, animate=False, duration=None):
        """Move the object to new position with optional animation"""
        if x is None:
            x = self.x if not self.position_center else self.center_x
        if y is None:
            y = self.y if not self.position_center else self.center_y
        
        if animate:
            dur = duration if duration else self.animation_duration
            self.create_n_animate([(x, y)], dur)
        else:
            if self.position_center:
                self.x = x - self.width // 2
                self.y = y - self.height // 2
                self.center_x = x
                self.center_y = y
            else:
                self.x = x
                self.y = y
            self.update()

    def _point_in_rounded_rect(self, point):
        """Check if a point is inside a rounded rectangle"""
        if self.border_radius == 0:
            return self.rect.collidepoint(point)
        
        x, y = point
        rx, ry = self.x, self.y
        rw, rh = self.width, self.height
        r = self.border_radius
        
        # Check if point is in the main rectangular areas
        if (rx + r <= x <= rx + rw - r) or (ry + r <= y <= ry + rh - r):
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return True
        
        # Check rounded corners
        corners = [
            (rx + r, ry + r),  # top-left
            (rx + rw - r, ry + r),  # top-right
            (rx + r, ry + rh - r),  # bottom-left
            (rx + rw - r, ry + rh - r)  # bottom-right
        ]
        
        for cx, cy in corners:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                return True
        
        return False
    
    def create_n_animate(self, points, duration):
        """Create and start animation with given points"""
        self.animation_points = points
        self.animation_duration = duration
        self.animation_current_point = 0
        self.animation_start_time = None
        self.is_animating = True
    
    def handle_events(self, event: pygame.event.Event) -> None:
        """Handle pygame events for this object"""
        # Handle window resize for relative positioning
        if self.relative_to_screen and event.type == pygame.VIDEORESIZE:
            new_width = event.w
            new_height = event.h
            
            if self.screen_width and self.screen_height:
                # Calculate scale ratio from original screen size
                scale_x = new_width / self.screen_width_original
                scale_y = new_height / self.screen_height_original
                
                # Resize text based on area scale (more aggressive scaling)
                area_scale = (scale_x * scale_y) ** 1.5  # Square root of area ratio
                self.text_size = int(self.text_size_original * area_scale)

                # Resize based on original ratios
                ratiow = self.width / self.screen_width
                ratioh = self.height / self.screen_height
                self.width = int(ratiow * new_width)
                self.height = int(ratioh * new_height)
                
                if self.position_center:
                    ratiox = self.center_x / self.screen_width
                    ratioy = self.center_y / self.screen_height
                    self.center_x = int(ratiox * new_width)
                    self.center_y = int(ratioy * new_height)
                    self.x = self.center_x - self.width // 2
                    self.y = self.center_y - self.height // 2
                else:
                    ratiox = self.x / self.screen_width
                    ratioy = self.y / self.screen_height
                    self.x = int(ratiox * new_width)
                    self.y = int(ratioy * new_height)
                
                # Update stored screen size
                self.screen_width = new_width
                self.screen_height = new_height
                self.update()
        
        if not self.ui_type:
            return
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Check hover
        was_hovered = self.is_hovered
        self.is_hovered = self._point_in_rounded_rect(mouse_pos) if self.border_radius > 0 else self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered and not was_hovered and self.hover_kwargs:
            self._apply_temp_kwargs(self.hover_kwargs)
        elif not self.is_hovered and was_hovered and self.temp_kwargs:
            self._restore_kwargs()
        
        # Check click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_clicked = True
                if self.click_kwargs:
                    self._restore_kwargs()
                    self._apply_temp_kwargs(self.click_kwargs)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_clicked:
                self.is_clicked = False
                self._restore_kwargs()
                if self.is_hovered and self.hover_kwargs:
                    self._apply_temp_kwargs(self.hover_kwargs)

    def check_collision(self, target):
        """Check and handle collision with target"""
        if self.rect_collides_kwargs:
            target_obj, collision_kwargs = self.rect_collides_kwargs
            
            if isinstance(target_obj, Object):
                target_rect = target_obj.rect
            else:
                target_rect = target_obj
            
            is_colliding = self.rect.colliderect(target_rect)
            
            if is_colliding and not self.is_colliding:
                self._apply_temp_kwargs(collision_kwargs)
                self.is_colliding = True
            elif not is_colliding and self.is_colliding:
                self._restore_kwargs()
                self.is_colliding = False
    
    def collides_with(self, other):
        """Check collision with another Object or rect"""
        if isinstance(other, Object):
            return self.rect.colliderect(other.rect)
        else:
            return self.rect.colliderect(other)
    
    def get_properties(self, name):
        """Get property value by name"""
        return getattr(self, name, None)
    
    def get_id(self):
        """Get the object's ID"""
        return self.uid
    
    def edit_id(self, new_id):
        """Edit the object's ID"""
        old_id = self.uid
        self.uid = new_id
        return old_id
    
    def edit_kwargs(self, **kwargs):
        """Edit the object's kwargs and reprocess them"""
        # Update base kwargs
        self.base_kwargs.update(kwargs)
        
        # Reprocess all kwargs
        self._process_kwargs(self.base_kwargs)
        
        # Re-parse colors if they were changed
        if 'color' in kwargs:
            self.color = self._parse_color(self.base_color if 'color' not in kwargs else kwargs['color'])
        if 'border_color' in kwargs:
            self.border_color = self._parse_color(kwargs['border_color'])
        
        # Recreate rect if border settings changed
        if any(k in kwargs for k in ['border_thickness', 'border_includes', 'border_thickness_grow', 'width', 'height']):
            self._create_rect()
        
        # Re-init text if text properties changed
        if any(k.startswith('text') for k in kwargs.keys()):
            self._init_text()
        
        # Update position and visuals
        self.update()
    
    def kill(self):
        """Remove object from instances"""
        if self in Object._instances:
            Object._instances.remove(self)
    
    @classmethod
    def get_all_instances(cls):
        """Get all Object instances"""
        return cls._instances.copy()
    
    @classmethod
    def get_by_id(cls, obj_id):
        """Get object by ID"""
        for obj in cls._instances:
            if obj.uid == obj_id:
                return obj
        return None
    
    def __repr__(self):
        return f"Object(x={self.x}, y={self.y}, width={self.width}, height={self.height}, id={self.uid})"
    
    def __str__(self):
        return f"Object at ({self.x}, {self.y}) with size {self.width}x{self.height}"
    
    def __eq__(self, other):
        if isinstance(other, Object):
            return self.uid == other.uid if self.uid and other.uid else self is other
        return False
    
    def __hash__(self):
        return hash(id(self))


class ObjectManager:
    """Manager class for handling multiple objects"""
    def __init__(self):
        self.objects: list[Object] = []
        self.id_map = {}
        self.groups = {}
        self.group_id_counter = 0
    
    def init(self, objs: list[Object]):
        for obj in objs:
            self.add(obj)
    
    def add(self, obj):
        """Add an existing object to the manager"""
        if obj not in self.objects:
            # Ensure unique ID
            if obj.uid:
                obj.uid = self._ensure_unique_id(obj.uid)
            else:
                obj.uid = self._generate_id()
            
            self.objects.append(obj)
            self.id_map[obj.uid] = obj
        return obj
    
    def create_object(self, x, y, size, **kwargs):
        """Create a new Object without adding it to the manager"""
        obj = Object(x, y, size, **kwargs)
        return obj
    
    def _ensure_unique_id(self, base_id):
        """Ensure ID is unique by appending counter if needed"""
        if base_id not in self.id_map:
            return base_id
        
        counter = 1
        new_id = f"{base_id}_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"{base_id}_{counter}"
        return new_id
    
    def _generate_id(self):
        """Generate a unique ID"""
        counter = len(self.objects)
        new_id = f"object_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"object_{counter}"
        return new_id
    
    def get_object_by_id(self, obj_id):
        """Get object by its ID"""
        return self.id_map.get(obj_id, None)
    
    def get_id_by_instance(self, instance):
        """Get ID by object instance"""
        if instance in self.objects:
            return instance.uid
        return None
    
    def get_kwargs_by_id(self, obj_id):
        """Get the base kwargs of an object by ID"""
        obj = self.get_object_by_id(obj_id)
        if obj:
            return obj.base_kwargs.copy()
        return None
    
    def check_collide_by_id(self, first_id, sec_id):
        """Check collision between two objects by their IDs"""
        first = self.get_object_by_id(first_id)
        second = self.get_object_by_id(sec_id)
        
        if first and second:
            return first.collides_with(second)
        return False
    
    def update_all(self):
        """Update all objects"""
        for obj in self.objects:
            obj.update()
    
    def draw_all(self, surface):
        """Draw all objects"""
        for obj in self.objects:
            obj.draw(surface)
    
    def handle_events_all(self, event):
        """Handle events for all UI objects"""
        for obj in self.objects:
            obj.handle_events(event)
    
    def kill(self, target):
        """Remove an object by instance or ID"""
        obj = None
        if isinstance(target, str):
            obj = self.get_object_by_id(target)
        elif isinstance(target, Object):
            obj = target
        
        if obj and obj in self.objects:
            self.objects.remove(obj)
            if obj.uid in self.id_map:
                del self.id_map[obj.uid]
            
            # Remove from groups
            for group_data in self.groups.values():
                if obj in group_data['objects']:
                    group_data['objects'].remove(obj)
            
            obj.kill()
    
    def group(self, objects_list, name, group_id=None):
        """Create a group of objects"""
        if group_id is None:
            group_id = f"group_{self.group_id_counter}"
            self.group_id_counter += 1
        
        self.groups[name] = {
            'id': group_id,
            'objects': objects_list.copy()
        }
        self.groups[group_id] = self.groups[name]
        return group_id
    
    def draw_group(self, identifier, surface):
        """Draw all objects in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            for obj in group_data['objects']:
                if isinstance(obj, Object):
                    obj.draw(surface)
    
    def update_group(self, identifier):
        """Update all objects in a group"""
        group_data = self.groups.get(identifier)
        if group_data:
            for obj in group_data['objects']:
                obj.update()
    
    def get_objects_in_group(self, identifier):
        """Get all objects in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            return group_data['objects'].copy()
        return []
    
    def find_group(self, instance):
        """Find which group(s) contain the given object instance"""
        groups_found = []
        for name, group_data in self.groups.items():
            if isinstance(name, str) and not name.startswith('group_'):
                if instance in group_data['objects']:
                    groups_found.append(name)
        return groups_found
    
    def add_to_group(self, identifier, obj):
        """Add an object to an existing group"""
        group_data = self.groups.get(identifier)
        if group_data and obj not in group_data['objects']:
            group_data['objects'].append(obj)
    
    def remove_from_group(self, identifier, obj):
        """Remove an object from a group"""
        group_data = self.groups.get(identifier)
        if group_data and obj in group_data['objects']:
            group_data['objects'].remove(obj)
    
    def delete_group(self, identifier):
        """Delete a group (objects remain in manager)"""
        group_data = self.groups.get(identifier)
        if group_data:
            group_id = group_data['id']
            # Find group name
            group_name = None
            for name, data in self.groups.items():
                if data is group_data and isinstance(name, str) and not name.startswith('group_'):
                    group_name = name
                    break
            
            if group_name:
                del self.groups[group_name]
            del self.groups[group_id]
    
    def get_all_objects(self):
        """Get all objects in the manager"""
        return self.objects.copy()
    
    def get_objects_by_type(self, shape_type):
        """Get all objects of a specific shape type"""
        return [obj for obj in self.objects if obj.shape_type == shape_type]
    
    def get_ui_objects(self):
        """Get all UI objects"""
        return [obj for obj in self.objects if obj.ui_type]
    
    def get_animated_objects(self):
        """Get all animated objects"""
        return [obj for obj in self.objects if obj.is_animating]
    
    def check_collisions_with(self, target):
        """Get all objects colliding with target object or rect"""
        colliding = []
        for obj in self.objects:
            if obj is not target and obj.collides_with(target):
                colliding.append(obj)
        return colliding
    
    def get_objects_at_point(self, x, y):
        """Get all objects at a specific point"""
        objects_at_point = []
        for obj in self.objects:
            if obj.rect.collidepoint(x, y):
                objects_at_point.append(obj)
        return objects_at_point
    
    def clear_all(self):
        """Remove all objects from the manager"""
        for obj in self.objects.copy():
            self.kill(obj)
    
    def edit_kwargs(self, target, **kwargs):
        """Edit kwargs of an object by ID or instance"""
        obj = None
        if isinstance(target, str):
            obj = self.get_object_by_id(target)
        elif isinstance(target, Object):
            obj = target
        
        if obj:
            obj.edit_kwargs(**kwargs)
            return True
        return False
    
    def __len__(self):
        """Return number of objects in manager"""
        return len(self.objects)
    
    def __repr__(self):
        return f"ObjectManager({len(self.objects)} objects, {len(self.groups)//2} groups)"

class Card:
    """Card class for displaying image with text below"""
    _instances = []
    _card_width = 150
    _card_height = 200
    _image_height_ratio = 0.7  # Image takes 70% of card height
    
    def __init__(self, x, y, **kwargs):
        """
        Initialize a Card object.
        
        Args:
            x: X position
            y: Y position
            **kwargs: Optional parameters
        """
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.kwargs = kwargs
        
        # Process kwargs to get padding first
        self._process_kwargs(kwargs)
        
        # Calculate dimensions (content size + padding)
        # Use custom size if provided, otherwise use default
        if self.custom_width is not None:
            self.content_width = self.custom_width
        else:
            self.content_width = Card._card_width
        
        if self.custom_height is not None:
            self.content_height = self.custom_height
        else:
            self.content_height = Card._card_height
        
        self.width = self.content_width + self.card_padding * 2
        self.height = self.content_height + self.card_padding * 2
        self.image_height = int(self.content_height * Card._image_height_ratio)
        self.text_height = self.content_height - self.image_height
        
        # Create rects
        self.container_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.image_rect = pygame.Rect(
            self.x + self.card_padding, 
            self.y + self.card_padding, 
            self.content_width, 
            self.image_height
        )
        self.text_rect_bg = pygame.Rect(
            self.x + self.card_padding, 
            self.y + self.card_padding + self.image_height, 
            self.content_width, 
            self.text_height
        )
        
        # Process image
        self.scaled_image = None
        if self.image:
            self.scaled_image = pygame.transform.scale(self.image, (self.content_width, self.image_height))
        
        # Process text
        self._init_text()
        
        # Screen size tracking for responsive resize
        self.screen_width = None
        self.screen_height = None
        if self.relative_to_screen:
            display_surface = pygame.display.get_surface()
            if display_surface:
                self.screen_width = display_surface.get_width()
                self.screen_height = display_surface.get_height()
                self.screen_width_original = self.screen_width
                self.screen_height_original = self.screen_height
        
        # Interaction state
        self.is_hovered = False
        self.is_clicked = False
        self.temp_kwargs = None
        
        # Add to instances
        Card._instances.append(self)
    
    def _process_kwargs(self, kwargs: dict[str, Any]):
        """Process keyword arguments"""
        self.image: pygame.Surface | None = kwargs.get('image', None)
        self._original_image: pygame.Surface | None = self.image
        self.text: str = kwargs.get('text', '')
        self.color: tuple | str = kwargs.get('color', (255, 255, 255))
        self.text_color: tuple | str = kwargs.get('text_color', (0, 0, 0))
        self.text_size: int = kwargs.get('text_size', 16)
        self.text_size_original: int = kwargs.get('text_size', 16)
        self.text_font: str | None = kwargs.get('text_font', None)
        self.text_exfont: str | None = kwargs.get('text_exfont', None)
        self.border_radius: int = kwargs.get('border_radius', 10)
        self.border_thickness: int = kwargs.get('border_thickness', 0)
        self.border_color: tuple | str = kwargs.get('border_color', (0, 0, 0))
        self.card_padding: int = kwargs.get('card_padding', 0)  # Outer padding
        self.padding: int = kwargs.get('padding', 10)  # Inner text padding
        self.image_fit: str = kwargs.get('image_fit', 'cover')  # 'cover', 'contain', 'fill'
        self.text_alignment: str = kwargs.get('text_alignment', 'center')
        self.shadow: bool = kwargs.get('shadow', False)
        self.shadow_offset: tuple[int, int] = kwargs.get('shadow_offset', (3, 3))
        self.shadow_color: tuple = kwargs.get('shadow_color', (0, 0, 0, 128))
        self.hover_kwargs: dict | None = kwargs.get('hover_kwargs', None)
        self.click_kwargs: dict | None = kwargs.get('click_kwargs', None)
        self.id: str | None = kwargs.get('id', None)
        self.relative_to_screen: bool = kwargs.get('relative_to_screen', True)
        self.switch_image_on_size: Optional[list[tuple[tuple[int, int], pygame.Surface, float]]] = kwargs.get('image_on_size', None)
        self.switch_image: bool = False
        self._base_image = self._original_image  # default
        
        # Custom size (overrides default if provided)
        self.custom_width: int | None = kwargs.get('width', None)
        self.custom_height: int | None = kwargs.get('height', None)
        
        # Parse colors
        self.color = self._parse_color(self.color)
        self.text_color = self._parse_color(self.text_color)
        self.border_color = self._parse_color(self.border_color)
    
    def _parse_color(self, color):
        """Parse color from tuple or string"""
        if isinstance(color, str):
            color_map = {
                'white': (255, 255, 255), 'black': (0, 0, 0),
                'red': (255, 0, 0), 'green': (0, 255, 0),
                'blue': (0, 0, 255), 'yellow': (255, 255, 0),
                'cyan': (0, 255, 255), 'magenta': (255, 0, 255),
                'gray': (128, 128, 128), 'grey': (128, 128, 128)
            }
            return color_map.get(color.lower(), (255, 255, 255))
        return color
    
    def _init_text(self):
        """Initialize text surface"""
        self.text_surface = None
        self.text_render_rect = None
        
        if self.text:
            text_size = int(self.text_size)
            
            # Load font
            if self.text_exfont:
                font = pygame.font.Font(self.text_exfont, text_size)
            elif self.text_font:
                font = pygame.font.SysFont(self.text_font, text_size)
            else:
                font = pygame.font.Font(None, text_size)
            
            # Render text with word wrap
            self.text_surface = self._render_text_wrapped(font, self.text, self.text_color, 
                                                           self.content_width)
            
            # Position text
            self._position_text()
    
    def _render_text_wrapped(self, font: pygame.font.Font, text: str, color: tuple[int, int, int], max_width: int):
        """Render text with word wrapping"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        # Account for inner padding when calculating max width
        available_width = max_width - self.padding * 2
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, color)
            
            if test_surface.get_width() <= available_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Create surface with all lines
        if not lines:
            return None
        
        line_height = font.get_linesize()
        text_surface = pygame.Surface((available_width, line_height * len(lines)), pygame.SRCALPHA)
        
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, color)
            text_surface.blit(line_surface, (0, i * line_height))
        
        return text_surface
    
    def _position_text(self):
        """Position text within text area"""
        if not self.text_surface:
            return
        
        text_w = self.text_surface.get_width()
        text_h = self.text_surface.get_height()
        
        # Text positioned within content area (inside card_padding)
        content_x = self.x + self.card_padding
        content_y = self.y + self.card_padding + self.image_height
        
        if self.text_alignment == 'center':
            text_x = content_x + (self.content_width - text_w) // 2
            text_y = content_y + (self.text_height - text_h) // 2
        elif self.text_alignment == 'left':
            text_x = content_x + self.padding
            text_y = content_y + (self.text_height - text_h) // 2
        elif self.text_alignment == 'right':
            text_x = content_x + self.content_width - text_w - self.padding
            text_y = content_y + (self.text_height - text_h) // 2
        else:
            text_x = content_x + self.padding
            text_y = content_y + self.padding
        
        self.text_render_rect = pygame.Rect(text_x, text_y, text_w, text_h)
    
    def _apply_temp_kwargs(self, kwargs):
        """Temporarily apply kwargs"""
        if kwargs:
            self.temp_kwargs = {}
            for key, value in kwargs.items():
                self.temp_kwargs[key] = getattr(self, key, None)
                setattr(self, key, value)
            
            if 'color' in kwargs:
                self.color = self._parse_color(kwargs['color'])
            if 'text_color' in kwargs:
                self.text_color = self._parse_color(kwargs['text_color'])
            if any(k.startswith('text') for k in kwargs.keys()):
                self._init_text()
    
    def _restore_kwargs(self):
        """Restore original kwargs"""
        if self.temp_kwargs:
            for key, value in self.temp_kwargs.items():
                setattr(self, key, value)
            self.temp_kwargs = None
            self._init_text()
    
    def update(self):
        """Update card state"""
        self.container_rect.x = self.x
        self.container_rect.y = self.y
        self.image_rect.x = self.x + self.card_padding
        self.image_rect.y = self.y + self.card_padding
        self.text_rect_bg.x = self.x + self.card_padding
        self.text_rect_bg.y = self.y + self.card_padding + self.image_height
        self._position_text()
    
    def draw(self, surface):
        """Draw the card"""
        # Draw shadow if enabled
        if self.shadow:
            shadow_rect = self.container_rect.copy()
            shadow_rect.x += self.shadow_offset[0]
            shadow_rect.y += self.shadow_offset[1]
            shadow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, self.shadow_color, 
                           pygame.Rect(0, 0, self.width, self.height), 
                           border_radius=self.border_radius)
            surface.blit(shadow_surface, (shadow_rect.x, shadow_rect.y))
        
        # Draw container background
        pygame.draw.rect(surface, self.color, self.container_rect, border_radius=self.border_radius)
        
        # Draw image (positioned with card_padding offset)
        if self.scaled_image:
            # Create a surface with rounded corners for image
            img_surface = pygame.Surface((self.content_width, self.image_height), pygame.SRCALPHA)
            pygame.draw.rect(img_surface, (255, 255, 255), 
                           pygame.Rect(0, 0, self.content_width, self.image_height),
                           border_radius=self.border_radius)
            img_surface.blit(self.scaled_image, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surface.blit(img_surface, (self.x + self.card_padding, self.y + self.card_padding))
        
        # Draw text background area (positioned with card_padding offset)
        text_bg_rect = pygame.Rect(
            self.x + self.card_padding, 
            self.y + self.card_padding + self.image_height, 
            self.content_width, 
            self.text_height
        )
        pygame.draw.rect(surface, self.color, text_bg_rect, border_radius=self.border_radius)
        
        # Draw text
        if self.text_surface and self.text_render_rect:
            surface.blit(self.text_surface, self.text_render_rect)
        
        # Draw border
        if self.border_thickness > 0:
            pygame.draw.rect(surface, self.border_color, self.container_rect, 
                           width=self.border_thickness, border_radius=self.border_radius)
    
    def handle_events(self, event: pygame.event.Event) -> None:
        """Handle pygame events"""
        # Handle window resize
        if self.relative_to_screen and event.type == pygame.VIDEORESIZE:
            new_width, new_height = event.w, event.h

            if self.screen_width and self.screen_height:
                # Calculate ratios
                ratio_x = self.content_width / self.screen_width
                ratio_y = self.content_height / self.screen_height

                old_card_area = self._card_width * self._card_height

                # Scale dimensions
                Card._card_width = new_width * ratio_x
                Card._card_height = new_height * ratio_y
                self.content_width = Card._card_width
                self.content_height = Card._card_height
                self.width = self.content_width + self.card_padding * 2
                self.height = self.content_height + self.card_padding * 2
                self.image_height = round(self.content_height * Card._image_height_ratio)
                self.text_height = self.content_height - self.image_height

                # Scale text
                self.text_size = round(
                    self.text_size * ((new_width*new_height) / (self.screen_width*self.screen_height))
                )

                # Scale position
                ratiox = self.x / self.screen_width
                ratioy = self.y / self.screen_height
                self.x = round(ratiox * new_width)
                self.y = round(ratioy * new_height)

                # Determine base image based on size
                self.switch_image = False
                matched_image = None

                if self.switch_image_on_size:
                    for element in self.switch_image_on_size:
                        if element and len(element) >= 2:
                            size_check, image_candidate = element[0], element[1]
                            accuracy = element[2] if len(element) == 3 else 0.1

                            min_w = size_check[0] * (1 - accuracy)
                            max_w = size_check[0] * (1 + accuracy)
                            min_h = size_check[1] * (1 - accuracy)
                            max_h = size_check[1] * (1 + accuracy)

                            if min_w < self.content_width < max_w and min_h < self.image_height < max_h:
                                self.switch_image = True
                                matched_image = image_candidate
                                break  # Stop at first match

                # Store base image for later override
                self._base_image = matched_image if self.switch_image else self._original_image

                # Update rects
                self.container_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                self.image_rect = pygame.Rect(
                    self.x + self.card_padding,
                    self.y + self.card_padding,
                    self.content_width,
                    self.image_height
                )
                self.text_rect_bg = pygame.Rect(
                    self.x + self.card_padding,
                    self.y + self.card_padding + self.image_height,
                    self.content_width,
                    self.text_height
                )

                # Update screen size
                self.screen_width = new_width
                self.screen_height = new_height

                # Rescale image (will be finalized later)
                self._init_text()
                self.update()

        # Handle mouse interaction
        mouse_pos = pygame.mouse.get_pos()
        was_hovered = self.is_hovered
        self.is_hovered = self.container_rect.collidepoint(mouse_pos)

        if self.is_hovered and not was_hovered and self.hover_kwargs:
            self._apply_temp_kwargs(self.hover_kwargs)
        elif not self.is_hovered and was_hovered and self.temp_kwargs:
            self._restore_kwargs()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_clicked = True
                if self.click_kwargs:
                    self._restore_kwargs()
                    self._apply_temp_kwargs(self.click_kwargs)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_clicked:
                self.is_clicked = False
                self._restore_kwargs()
                if self.is_hovered and self.hover_kwargs:
                    self._apply_temp_kwargs(self.hover_kwargs)

        # Finalize image selection
        if self.is_clicked and self.click_kwargs.get('image'):
            self.image = self.click_kwargs['image']
        elif self.is_hovered and self.hover_kwargs.get('image'):
            self.image = self.hover_kwargs['image']
        else:
            self.image = self._base_image

        # Rescale image
        if self.image:
            self.scaled_image = pygame.transform.scale(self.image, (self.content_width, self.image_height))  

    def get_id(self):
        """Get card ID"""
        return self.id
    
    def edit_id(self, new_id):
        """Edit card ID"""
        old_id = self.id
        self.id = new_id
        return old_id
    
    def edit_kwargs(self, **kwargs):
        """Edit card kwargs"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        if 'color' in kwargs:
            self.color = self._parse_color(kwargs['color'])
        if 'text_color' in kwargs:
            self.text_color = self._parse_color(kwargs['text_color'])
        if 'image' in kwargs:
            self.scaled_image = pygame.transform.scale(kwargs['image'], (self.width, self.image_height))
        
        if any(k.startswith('text') for k in kwargs.keys()) or 'image' in kwargs:
            self._init_text()
        
        self.update()
    
    def kill(self):
        """Remove card from instances"""
        if self in Card._instances:
            Card._instances.remove(self)
    
    @classmethod
    def set_default_size(cls, width, height):
        """Set default card size for all new cards"""
        cls._card_width = width
        cls._card_height = height
    
    @classmethod
    def get_all_instances(cls):
        """Get all Card instances"""
        return cls._instances.copy()
    
    def __repr__(self):
        return f"Card(x={self.x}, y={self.y}, id={self.id})"


class CardManager:
    """Manager class for handling multiple Cards"""
    def __init__(self):
        self.cards: list[Card] = []
        self.id_map = {}
        self.groups: dict[str, dict[str, list[Card]]] = {}
        self.group_id_counter = 0
    
    def add(self, card):
        """Add an existing card to the manager"""
        if card not in self.cards:
            # Ensure unique ID
            if card.id:
                card.id = self._ensure_unique_id(card.id)
            else:
                card.id = self._generate_id()
            
            self.cards.append(card)
            self.id_map[card.id] = card
        return card
    
    def _ensure_unique_id(self, base_id):
        """Ensure ID is unique by appending counter if needed"""
        if base_id not in self.id_map:
            return base_id
        
        counter = 1
        new_id = f"{base_id}_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"{base_id}_{counter}"
        return new_id
    
    def _generate_id(self):
        """Generate a unique ID"""
        counter = len(self.cards)
        new_id = f"card_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"card_{counter}"
        return new_id
    
    def create_card(self, x, y, **kwargs):
        """Create a new Card without adding it to the manager"""
        card = Card(x, y, **kwargs)
        return card
    
    def get_card_by_id(self, card_id):
        """Get card by its ID"""
        return self.id_map.get(card_id, None)
    
    def get_id_by_instance(self, instance):
        """Get ID by card instance"""
        if instance in self.cards:
            return instance.id
        return None
    
    def get_kwargs_by_id(self, card_id):
        """Get the kwargs of a card by ID"""
        card = self.get_card_by_id(card_id)
        if card:
            return {
                'image': card.image,
                'text': card.text,
                'color': card.color,
                'text_color': card.text_color,
                'text_size': card.text_size,
                'text_font': card.text_font,
                'border_radius': card.border_radius,
                'card_padding': card.card_padding,
                'padding': card.padding
            }
        return None
    
    def check_collide_by_id(self, first_id, sec_id):
        """Check collision between two cards by their IDs"""
        first = self.get_card_by_id(first_id)
        second = self.get_card_by_id(sec_id)
        
        if first and second:
            return first.container_rect.colliderect(second.container_rect)
        return False
    
    def update_all(self):
        """Update all cards"""
        for card in self.cards:
            card.update()
    
    def draw_all(self, surface):
        """Draw all cards"""
        for card in self.cards:
            card.draw(surface)
    
    def handle_events_all(self, event):
        """Handle events for all cards"""
        for card in self.cards:
            card.handle_events(event)
    
    def kill(self, target):
        """Remove a card by instance or ID"""
        card = None
        if isinstance(target, str):
            card = self.get_card_by_id(target)
        elif isinstance(target, Card):
            card = target
        
        if card and card in self.cards:
            self.cards.remove(card)
            if card.id in self.id_map:
                del self.id_map[card.id]
            
            # Remove from groups
            for group_data in self.groups.values():
                if card in group_data['cards']:
                    group_data['cards'].remove(card)
            
            card.kill()
    
    def group(self, cards_list, name, group_id=None):
        """Create a group of cards"""
        if group_id is None:
            group_id = f"group_{self.group_id_counter}"
            self.group_id_counter += 1
        
        self.groups[name] = {
            'id': group_id,
            'cards': cards_list.copy()
        }
        self.groups[group_id] = self.groups[name]
        return group_id
    
    def init(self, cards: list[Card]) -> None:
        for card in cards:
            self.add(card)
    
    def draw_group(self, identifier, surface):
        """Draw all cards in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            for card in group_data['cards']:
                card.draw(surface)
    
    def update_group(self, identifier):
        """Update all cards in a group"""
        group_data = self.groups.get(identifier)
        if group_data:
            for card in group_data['cards']:
                card.update()
    
    def get_cards_in_group(self, identifier):
        """Get all cards in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            return group_data['cards'].copy()
        return []
    
    def find_group(self, instance):
        """Find which group(s) contain the given card instance"""
        groups_found = []
        for name, group_data in self.groups.items():
            if isinstance(name, str) and not name.startswith('group_'):
                if instance in group_data['cards']:
                    groups_found.append(name)
        return groups_found
    
    def add_to_group(self, identifier, card):
        """Add a card to an existing group"""
        group_data = self.groups.get(identifier)
        if group_data and card not in group_data['cards']:
            group_data['cards'].append(card)
    
    def remove_from_group(self, identifier, card):
        """Remove a card from a group"""
        group_data = self.groups.get(identifier)
        if group_data and card in group_data['cards']:
            group_data['cards'].remove(card)
    
    def delete_group(self, identifier):
        """Delete a group (cards remain in manager)"""
        group_data = self.groups.get(identifier)
        if group_data:
            group_id = group_data['id']
            # Find group name
            group_name = None
            for name, data in self.groups.items():
                if data is group_data and isinstance(name, str) and not name.startswith('group_'):
                    group_name = name
                    break
            
            if group_name:
                del self.groups[group_name]
            del self.groups[group_id]
    
    def get_all_cards(self):
        """Get all cards in the manager"""
        return self.cards.copy()
    
    def get_cards_at_point(self, x, y):
        """Get all cards at a specific point"""
        cards_at_point = []
        for card in self.cards:
            if card.container_rect.collidepoint(x, y):
                cards_at_point.append(card)
        return cards_at_point
    
    def get_hovered_cards(self):
        """Get all currently hovered cards"""
        return [card for card in self.cards if card.is_hovered]
    
    def get_clicked_cards(self):
        """Get all currently clicked cards"""
        return [card for card in self.cards if card.is_clicked]
    
    def check_collisions_with(self, target):
        """Get all cards colliding with target card or rect"""
        colliding = []
        if isinstance(target, Card):
            target_rect = target.container_rect
        else:
            target_rect = target
        
        for card in self.cards:
            if card is not target and card.container_rect.colliderect(target_rect):
                colliding.append(card)
        return colliding
    
    def clear_all(self):
        """Remove all cards from the manager"""
        for card in self.cards.copy():
            self.kill(card)
    
    def edit_kwargs(self, target, **kwargs):
        """Edit kwargs of a card by ID or instance"""
        card = None
        if isinstance(target, str):
            card = self.get_card_by_id(target)
        elif isinstance(target, Card):
            card = target
        
        if card:
            card.edit_kwargs(**kwargs)
            return True
        return False
    
    def arrange_grid(self, cards_list, columns, spacing_x=20, spacing_y=20, start_x=0, start_y=0):
        """Arrange cards in a grid layout"""
        for i, card in enumerate(cards_list):
            row = i // columns
            col = i % columns
            card.x = start_x + col * (card.width + spacing_x)
            card.y = start_y + row * (card.height + spacing_y)
            card.update()
    
    def arrange_horizontal(self, cards_list, spacing=20, start_x=0, start_y=0):
        """Arrange cards horizontally"""
        current_x = start_x
        for card in cards_list:
            card.x = current_x
            card.y = start_y
            card.update()
            current_x += card.width + spacing
    
    def arrange_vertical(self, cards_list, spacing=20, start_x=0, start_y=0):
        """Arrange cards vertically"""
        current_y = start_y
        for card in cards_list:
            card.x = start_x
            card.y = current_y
            card.update()
            current_y += card.height + spacing
    
    def set_group_size(self, identifier, width=None, height=None):
        """Set width and/or height for all cards in a group"""
        group_data = self.groups.get(identifier)
        if group_data:
            for card in group_data['cards']:
                kwargs = {}
                if width is not None:
                    kwargs['width'] = width
                if height is not None:
                    kwargs['height'] = height
                if kwargs:
                    card.edit_kwargs(**kwargs)
    
    def set_group_kwargs(self, identifier, **kwargs):
        """Set kwargs for all cards in a group"""
        group_data = self.groups.get(identifier)
        if group_data:
            for card in group_data['cards']:
                card.edit_kwargs(**kwargs)

    def get_group_kwargs(self, group_identifier: str) -> dict[str, Any]|list[dict[str, Any]]:
        group_data = self.groups.get(group_identifier)
        kwargs: list|dict = []
        if group_data:
            for card in group_data['cards']:
                if card.kwargs not in kwargs:
                    kwargs.append(card.kwargs)

        if len[kwargs] == 1:
            return kwargs[0]
        else:
            return kwargs
    
    def set_all_size(self, width=None, height=None):
        """Set width and/or height for all cards in manager"""
        for card in self.cards:
            kwargs = {}
            if width is not None:
                kwargs['width'] = width
            if height is not None:
                kwargs['height'] = height
            if kwargs:
                card.edit_kwargs(**kwargs)
    
    def set_all_kwargs(self, **kwargs):
        """Set kwargs for all cards in manager"""
        for card in self.cards:
            card.edit_kwargs(**kwargs)
    
    def __len__(self):
        """Return number of cards in manager"""
        return len(self.cards)
    
    def __repr__(self):
        return f"CardManager({len(self.cards)} cards, {len(self.groups)//2} groups)"

class Body:
    """Physics body for space simulation"""
    _instances = []
    GRAVITATIONAL_CONSTANT = 6.674e-11  # Can be scaled for game physics
    
    def __init__(self, x: int, y: int, bodytype: str, mass: float|int, **kwargs) -> None:
        self.x = x
        self.y = y
        # Debug: log initial construction positions
        try:
            print(f"INIT Body: type={bodytype!r} initial x={self.x!r}, y={self.y!r}")
        except Exception:
            pass
        self.position = (self.x, self.y)
        self.bodytype = bodytype
        self.mass = mass
        self.belongs: Optional[str] = None

        if self.bodytype not in ['planet', 'star', 'black_hole', 'particle']:
            self.belongs = 'artificial'
        else:
            self.belongs = 'space objects'

        self._process_kwargs(kwargs)
        
        # Physics state
        self.acceleration_x = 0
        self.acceleration_y = 0
        self.force_x = 0
        self.force_y = 0
        
        # Trajectory prediction
        self.trajectory_points = []
        self.show_trajectory = False
        self.trajectory_steps = 100
        self.trajectory_dt = 1.0
        
        # Visualization flags
        self.show_forces = False
        self.show_velocity = False
        
        # Create visual representation
        self._create_visual()
        
        # Add to instances
        Body._instances.append(self)
        # Debug flag to avoid repeated large-value prints
        self._warned_large = False

    def _process_kwargs(self, kwargs: dict) -> None:
        self.width: Optional[int] = kwargs.get('width', None) if self.belongs == 'artificial' else None
        self.height: Optional[int] = kwargs.get('height', None) if self.belongs == 'artificial' else None
        self.object_name: Optional[str] = kwargs.get('class', None) if self.belongs == 'artificial' else None
        self._id: Optional[str] = kwargs.get('id', None)
        self.velocity_x: int = kwargs.get('vx', 0) if type(kwargs.get('vx', 0)) == int else round(kwargs.get('vx', 0))
        self.velocity_y: int = kwargs.get('vy', 0) if type(kwargs.get('vy', 0)) == int else round(kwargs.get('vy', 0))
        
        # Temperature properties (Celsius)
        self.temperature: float = kwargs.get('temperature', None)
        self.cooling_rate: float = kwargs.get('cooling_rate', 0.01)  # Degrees per update
        self.min_temperature: float = kwargs.get('min_temperature', -273.15)  # Absolute zero
        
        # Set default temperatures based on body type
        if self.temperature is None:
            if self.bodytype == 'star':
                self.temperature = 5500.0  # Sun's surface temp
            elif self.bodytype == 'planet':
                self.temperature = 15.0  # Earth-like temperature
            elif self.bodytype == 'black_hole':
                self.temperature = -273.15  # Near absolute zero
            elif self.bodytype == 'particle':
                self.temperature = 100.0  # Warm gas
            else:
                self.temperature = 20.0  # Room temperature for artificial objects
        
        # Particle-specific properties
        self.angular_velocity: float = kwargs.get('angular_velocity', 0.0)  # Rotation speed
        self.spin_direction: int = kwargs.get('spin_direction', 1)  # 1 = counterclockwise, -1 = clockwise
        self.accretion_rate: float = kwargs.get('accretion_rate', 0.0)  # Mass gain per update
        
        # Transformation thresholds
        self.particle_to_planet_mass: float = kwargs.get('particle_to_planet_mass', 1e20)
        self.planet_to_star_mass: float = kwargs.get('planet_to_star_mass', 1e28)
        self.star_to_blackhole_mass: float = kwargs.get('star_to_blackhole_mass', 3e31)
        
        # Visualization settings from kwargs
        self.show_trajectory: bool = kwargs.get('show_trajectory', False)
        self.show_forces: bool = kwargs.get('show_forces', False)
        self.show_velocity: bool = kwargs.get('show_velocity', False)
        self.trajectory_steps: int = kwargs.get('trajectory_steps', 100)
        self.trajectory_dt: float = kwargs.get('trajectory_dt', 1.0)
        
        # Physical properties
        self.fixed: bool = kwargs.get('fixed', False)  # Fixed bodies don't move
        self.density: float = kwargs.get('density', None)
        self.auto_size: bool = kwargs.get('auto_size', True)  # Calculate size from mass/density
        
        # Visual properties
        self.radius: int = kwargs.get('radius', None)
        self.base_color: tuple = kwargs.get('color', None)  # User-defined color override
        self.color: tuple = self._calculate_color_from_temperature()
        self.image: pygame.Surface | None = kwargs.get('image', None)
        self.trail: bool = kwargs.get('trail', False)
        self.trail_length: int = kwargs.get('trail_length', 50)
        self.trail_positions: list = []
        
        # Collision
        self.collision_enabled: bool = kwargs.get('collision', True)
        
        # Set default densities if not provided (kg/m³)
        if self.density is None:
            if self.bodytype == 'star':
                self.density = 1408.0  # Sun's average density
            elif self.bodytype == 'planet':
                self.density = 5514.0  # Earth's density
            elif self.bodytype == 'black_hole':
                self.density = 1e17  # Extremely dense
            elif self.bodytype == 'particle':
                self.density = 0.1  # Very low density gas
            else:
                self.density = 1000.0  # Water density for artificial objects
        
        # Calculate size for natural bodies
        if self.belongs == 'space objects' and self.auto_size:
            self.radius = self._calculate_radius_from_mass()
        elif self.radius is None:
            # Fallback to simple mass-based calculation
            if self.bodytype == 'star':
                self.radius = max(int((self.mass ** 0.3) / 100), 30)
            elif self.bodytype == 'planet':
                self.radius = max(int((self.mass ** 0.3) / 150), 10)
            elif self.bodytype == 'black_hole':
                self.radius = max(int((self.mass ** 0.2) / 200), 15)
            elif self.bodytype == 'particle':
                self.radius = max(int((self.mass ** 0.2) / 500), 2)
            else:
                self.radius = 20  # Default for artificial objects
    
    def _create_visual(self):
        """Create visual representation"""
        if self.belongs == 'artificial' and self.width and self.height:
            self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, 
                                   self.width, self.height)
        else:
            self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                                   self.radius * 2, self.radius * 2)
    
    def _calculate_radius_from_mass(self) -> int:
        """
        Calculate radius from mass and density using the formula:
        Volume = Mass / Density
        Volume of sphere = (4/3) * π * r³
        Therefore: r = ³√((3 * Mass) / (4 * π * Density))
        
        This allows realistic size differences like Jupiter being 11.2x larger than Earth
        while only being 318x more massive (due to lower density).
        """
        import math
        
        # Calculate volume in m³
        volume = self.mass / self.density
        
        # Calculate radius in meters: r = ³√((3 * V) / (4 * π))
        radius_meters = ((3 * volume) / (4 * math.pi)) ** (1/3)
        
        # Scale factor for game display (1 pixel = X meters)
        # Adjust this to make bodies visible at reasonable sizes
        if self.bodytype == 'star':
            scale_factor = 1e-7  # Stars are huge
        elif self.bodytype == 'planet':
            scale_factor = 1e-5  # Planets are smaller
        elif self.bodytype == 'black_hole':
            scale_factor = 1e-3  # Black holes are tiny but appear larger
        elif self.bodytype == 'particle':
            scale_factor = 1e-3  # Particles are very small
        else:
            scale_factor = 1.0
        
        radius_pixels = int(radius_meters * scale_factor)
        
        # Ensure minimum and maximum sizes for gameplay
        if self.bodytype == 'particle':
            min_radius = 1
            max_radius = 10
        elif self.bodytype != 'star':
            min_radius = 5
            max_radius = 200
        else:
            min_radius = 20
            max_radius = 200
        
        return max(min_radius, min(radius_pixels, max_radius))
    
    def _calculate_color_from_temperature(self) -> tuple:
        """Calculate color based on temperature (blackbody radiation)"""
        # If user provided a color override, use it
        if self.base_color is not None:
            return self.base_color
        
        # Black holes are always black
        if self.bodytype == 'black_hole':
            return (0, 0, 0)
        
        temp = self.temperature
        
        # Temperature to color mapping (simplified blackbody radiation)
        if temp < 0:  # Frozen/cold bodies
            # Deep blue to cyan gradient
            intensity = max(0, min(255, int((temp + 273.15) / 273.15 * 100)))
            return (0, intensity // 2, intensity)
        
        elif temp < 100:  # Cool bodies (planets)
            # Blue to green gradient
            ratio = temp / 100
            return (
                int(50 * ratio),
                int(100 + 100 * ratio),
                int(255 - 100 * ratio)
            )
        
        elif temp < 1000:  # Warm bodies
            # Green to orange gradient
            ratio = (temp - 100) / 900
            return (
                int(150 + 105 * ratio),
                int(200 - 100 * ratio),
                int(50 * (1 - ratio))
            )
        
        elif temp < 3000:  # Hot bodies (red dwarfs)
            # Orange to red gradient
            ratio = (temp - 1000) / 2000
            return (
                255,
                int(100 * (1 - ratio)),
                0
            )
        
        elif temp < 6000:  # Very hot (sun-like stars)
            # Red to yellow gradient
            ratio = (temp - 3000) / 3000
            return (
                255,
                int(100 + 155 * ratio),
                int(50 * ratio)
            )
        
        elif temp < 10000:  # Extremely hot (white stars)
            # Yellow to white gradient
            ratio = (temp - 6000) / 4000
            return (
                255,
                255,
                int(50 + 205 * ratio)
            )
        
        else:  # Ultra hot (blue giants)
            # White to blue-white gradient
            ratio = min(1.0, (temp - 10000) / 20000)
            return (
                int(255 - 55 * ratio),
                int(255 - 55 * ratio),
                255
            )
    
    def update_temperature(self, dt: float = 1.0):
        """Update temperature with cooling"""
        if self.bodytype != 'black_hole':  # Black holes don't cool
            # Cool down over time
            self.temperature -= self.cooling_rate * dt
            
            # Particles heat up when spinning fast (friction)
            if self.bodytype == 'particle' and abs(self.angular_velocity) > 0.1:
                heating = abs(self.angular_velocity) * 0.5
                self.temperature += heating * dt
            
            # Don't go below minimum temperature
            self.temperature = max(self.temperature, self.min_temperature)
            
            # Update color based on new temperature
            self.color = self._calculate_color_from_temperature()
    
    def apply_spin(self, angular_acceleration: float):
        """Apply angular acceleration to spinning particles"""
        if self.bodytype == 'particle':
            self.angular_velocity += angular_acceleration
    
    def accrete_mass(self, additional_mass: float):
        """Add mass to the body (for particle accretion)"""
        self.mass += additional_mass
        
        # Recalculate size if auto_size is enabled
        if self.auto_size:
            self.radius = self._calculate_radius_from_mass()
            self._create_visual()
    
    def check_transformation(self) -> Optional[str]:
        """
        Check if body should transform to another type based on mass and conditions.
        Returns the new body type if transformation should occur, None otherwise.
        """
        if self.bodytype == 'particle':
            # Particles become planets when enough mass accumulates
            if self.mass >= self.particle_to_planet_mass:
                return 'planet'
        
        elif self.bodytype == 'planet':
            # Planets become stars when they reach fusion mass threshold
            if self.mass >= self.planet_to_star_mass:
                return 'star'
        
        elif self.bodytype == 'star':
            # Stars become black holes when they collapse (high mass + low temperature)
            if self.mass >= self.star_to_blackhole_mass and self.temperature < 1000:
                return 'black_hole'
        
        return None
    
    def transform_to(self, new_type: str):
        """
        Transform this body into a different type.
        Updates all relevant properties for the new type.
        """
        old_type = self.bodytype
        self.bodytype = new_type
        
        # Update density for new type
        if new_type == 'planet':
            self.density = 5514.0
            self.temperature = max(self.temperature, 15.0)
            self.angular_velocity *= 0.5  # Slow down rotation
        elif new_type == 'star':
            self.density = 1408.0
            self.temperature = 5500.0  # Ignite fusion
            self.angular_velocity *= 0.2  # Further slow down
        elif new_type == 'black_hole':
            self.density = 1e17
            self.temperature = -273.15
            self.angular_velocity = 0  # Stop rotation
        
        # Recalculate size and visuals
        if self.auto_size:
            self.radius = self._calculate_radius_from_mass()
        self.color = self._calculate_color_from_temperature()
        self._create_visual()
        
        return old_type
    
    def predict_trajectory(self, other_bodies: list['Body'], steps: int = None, dt: float = None):
        """
        Predict the trajectory of this body given gravitational forces from other bodies.
        Returns a list of (x, y) positions.
        """
        if steps is None:
            steps = self.trajectory_steps
        if dt is None:
            dt = self.trajectory_dt
        
        # Create a copy of current state
        sim_x = self.x
        sim_y = self.y
        sim_vx = self.velocity_x
        sim_vy = self.velocity_y
        
        trajectory = [(sim_x, sim_y)]
        
        for step in range(steps):
            # Calculate forces from all other bodies
            total_fx = 0
            total_fy = 0
            
            for other in other_bodies:
                if other is self or self.fixed:
                    continue
                
                # Calculate gravitational force
                dx = other.x - sim_x
                dy = other.y - sim_y
                distance = max((dx**2 + dy**2) ** 0.5, 1)

                # Convert G from SI into pixel-space by dividing by (pixels_per_meter^2)
                eff_G = Body.GRAVITATIONAL_CONSTANT / (FisXSettings.pixels_per_meter ** 2) * FisXSettings.gravity_scale
                force_magnitude = (eff_G * self.mass * other.mass) / (distance ** 2)
                
                fx = force_magnitude * (dx / distance)
                fy = force_magnitude * (dy / distance)
                
                total_fx += fx
                total_fy += fy
            
            # Calculate acceleration
            if self.mass > 0 and not self.fixed:
                ax = total_fx / self.mass
                ay = total_fy / self.mass
                
                # Update velocity
                sim_vx += ax * dt
                sim_vy += ay * dt
                
                # Update position
                sim_x += sim_vx * dt
                sim_y += sim_vy * dt
                
                trajectory.append((int(sim_x), int(sim_y)))
        
        return trajectory
    
    def draw_arrow(self, surface: pygame.Surface, start_x: float, start_y: float, 
                   end_x: float, end_y: float, color: tuple, width: int = 2):
        """Draw an arrow from start to end position"""
        import math
        
        # Draw line
        pygame.draw.line(surface, color, (int(start_x), int(start_y)), 
                        (int(end_x), int(end_y)), width)
        
        # Calculate arrow head
        dx = end_x - start_x
        dy = end_y - start_y
        length = (dx**2 + dy**2) ** 0.5
        
        if length > 0:
            # Normalize
            dx /= length
            dy /= length
            
            # Arrow head size
            arrow_size = min(length * 0.3, 10)
            
            # Arrow head angle
            angle = math.atan2(dy, dx)
            
            # Calculate arrow head points
            left_angle = angle + 2.5
            right_angle = angle - 2.5
            
            left_x = end_x - arrow_size * math.cos(left_angle)
            left_y = end_y - arrow_size * math.sin(left_angle)
            right_x = end_x - arrow_size * math.cos(right_angle)
            right_y = end_y - arrow_size * math.sin(right_angle)
            
            # Draw arrow head
            pygame.draw.polygon(surface, color, [
                (int(end_x), int(end_y)),
                (int(left_x), int(left_y)),
                (int(right_x), int(right_y))
            ])
    
    def apply_force(self, fx: float, fy: float):
        """Apply force to the body"""
        if not self.fixed:
            self.force_x += fx
            self.force_y += fy
    
    def calculate_gravity(self, other: 'Body') -> tuple[float, float]:
        """Calculate gravitational force from another body"""
        dx = other.x - self.x
        dy = other.y - self.y
        distance = max((dx**2 + dy**2) ** 0.5, 1)  # Avoid division by zero

        # Convert G from SI into pixel-space by dividing by (pixels_per_meter^2)
        eff_G = Body.GRAVITATIONAL_CONSTANT / (FisXSettings.pixels_per_meter ** 2) * FisXSettings.gravity_scale
        # F = G_eff * m1 * m2 / r^2
        force_magnitude = (eff_G * self.mass * other.mass) / (distance ** 2)

        # Calculate force components
        fx = force_magnitude * (dx / distance)
        fy = force_magnitude * (dy / distance)

        return fx, fy
    
    def update(self, dt: float = 1.0):
        """Update physics state"""
        # Debug: warn if position/velocity become extremely large
        if (not getattr(self, '_warned_large', False)) and (abs(self.x) > 1e9 or abs(self.y) > 1e9 or abs(self.velocity_x) > 1e9 or abs(self.velocity_y) > 1e9):
            print(f"LARGE VALUE DETECTED in Body(id={self._id}): x={self.x}, y={self.y}, vx={self.velocity_x}, vy={self.velocity_y}, mass={self.mass}")
            self._warned_large = True
        if not self.fixed:
            # Calculate acceleration: a = F / m
            self.acceleration_x = self.force_x / self.mass if self.mass > 0 else 0
            self.acceleration_y = self.force_y / self.mass if self.mass > 0 else 0
            
            # Update velocity: v = v0 + a * dt
            self.velocity_x += self.acceleration_x * dt
            self.velocity_y += self.acceleration_y * dt
            
            # Apply angular velocity for particles (spiral motion)
            if self.bodytype == 'particle' and abs(self.angular_velocity) > 0.01:
                import math
                # Add tangential velocity component
                angle = math.atan2(self.velocity_y, self.velocity_x)
                speed = (self.velocity_x**2 + self.velocity_y**2) ** 0.5
                
                # Add perpendicular velocity for spinning
                perpendicular_angle = angle + (math.pi / 2 * self.spin_direction)
                spin_strength = abs(self.angular_velocity) * 10
                self.velocity_x += math.cos(perpendicular_angle) * spin_strength * dt
                self.velocity_y += math.sin(perpendicular_angle) * spin_strength * dt
            
            # Update position: x = x0 + v * dt
            self.x += self.velocity_x * dt
            self.y += self.velocity_y * dt
            
            # Update trail
            if self.trail:
                self.trail_positions.append((int(self.x), int(self.y)))
                if len(self.trail_positions) > self.trail_length:
                    self.trail_positions.pop(0)
            
            # Update visual
            self._create_visual()
            
            # Reset forces
            self.force_x = 0
            self.force_y = 0
        
        # Accrete mass for particles (gain mass over time)
        if self.bodytype == 'particle' and self.accretion_rate > 0:
            self.accrete_mass(self.accretion_rate * dt)
        
        # Update temperature (cooling)
        self.update_temperature(dt)
        
        # Check for transformation
        new_type = self.check_transformation()
        if new_type:
            self.transform_to(new_type)
        
        self.position = (self.x, self.y)
    
    def draw(self, surface: pygame.Surface):
        """Draw the body"""
        # draw with optional camera offset support (deprecated calls still work)
        cam = getattr(self, '_cam_offset', (0, 0))
        cam_x, cam_y = cam
        # Draw trajectory prediction first (behind everything)
        if self.show_trajectory and len(self.trajectory_points) > 1:
            for i in range(len(self.trajectory_points) - 1):
                alpha = int(100 * (i / len(self.trajectory_points)))
                # Draw fading line segments
                color = (*self.color[:3], alpha) if len(self.color) >= 3 else (255, 255, 255, alpha)
                if i % 5 == 0:  # Draw every 5th point for performance
                    px, py = self.trajectory_points[i]
                    pygame.draw.circle(surface, color, (int(px - cam_x), int(py - cam_y)), 1)
        
        # Draw trail (camera-aware)
        if self.trail and len(self.trail_positions) > 1:
            cam_x, cam_y = cam
            for i in range(len(self.trail_positions) - 1):
                try:
                    sx, sy = self.trail_positions[i]
                    ex, ey = self.trail_positions[i + 1]
                    sx = int(sx - cam_x)
                    sy = int(sy - cam_y)
                    ex = int(ex - cam_x)
                    ey = int(ey - cam_y)
                    alpha = int(255 * (i / len(self.trail_positions)))
                    color = (*self.color[:3], alpha) if len(self.color) == 4 else self.color
                    pygame.draw.line(surface, color, (sx, sy), (ex, ey), 2)
                except Exception:
                    # Skip any invalid trail segment silently (avoids console spam)
                    continue
        
        # Draw body
        if self.image:
            scaled_img = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            surface.blit(scaled_img, (int(self.x - self.radius - cam_x), int(self.y - self.radius - cam_y)))
        elif self.belongs == 'artificial' and self.width and self.height:
            pygame.draw.rect(surface, self.color, self.rect)
        else:
            # Draw particles with transparency/glow effect
            if self.bodytype == 'particle':
                # Draw glow effect for particles
                glow_radius = int(self.radius * 1.5)
                glow_color = (*self.color[:3], 100) if len(self.color) == 3 else self.color
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surface, (int(self.x - glow_radius - cam_x), int(self.y - glow_radius - cam_y)))
            
            # Draw main body (guard against invalid coordinates)
            try:
                cx = int(self.x - cam_x)
                cy = int(self.y - cam_y)
                # Ensure valid radius and color
                radius = int(self.radius) if hasattr(self, 'radius') and self.radius is not None else 1
                col = self.color
                if isinstance(col, (list, tuple)) and len(col) >= 3:
                    col = (int(col[0]), int(col[1]), int(col[2]))
                else:
                    col = (255, 255, 255)
                # Final safety check: coordinates within a reasonable drawable range
                if abs(cx) < 10_000_000 and abs(cy) < 10_000_000 and radius > 0:
                    pygame.draw.circle(surface, col, (cx, cy), radius)
            except Exception:
                # Silently skip invalid draws to avoid flooding the console
                pass
        
        # Draw velocity arrow
        if self.show_velocity:
            speed = (self.velocity_x**2 + self.velocity_y**2) ** 0.5
            if speed > 0.1:  # Only draw if moving
                scale = 20  # Scale factor for visibility
                end_x = self.x + self.velocity_x * scale
                end_y = self.y + self.velocity_y * scale
                self.draw_arrow(surface, self.x, self.y, end_x, end_y, (0, 255, 0), 2)
        
        # Draw force arrow
        if self.show_forces:
            force_magnitude = (self.force_x**2 + self.force_y**2) ** 0.5
            if force_magnitude > 1e-6:  # Only draw if force is significant
                scale = 1e-20  # Scale factor for visibility (adjust based on force magnitude)
                end_x = self.x + self.force_x * scale
                end_y = self.y + self.force_y * scale
                self.draw_arrow(surface, self.x, self.y, end_x, end_y, (255, 0, 0), 2)
        
        # Draw acceleration arrow (optional, yellow)
        if self.show_forces:
            accel_magnitude = (self.acceleration_x**2 + self.acceleration_y**2) ** 0.5
            if accel_magnitude > 0.001:
                scale = 100  # Scale factor for visibility
                end_x = self.x + self.acceleration_x * scale
                end_y = self.y + self.acceleration_y * scale
                self.draw_arrow(surface, self.x, self.y, end_x, end_y, (255, 255, 0), 1)
    
    def check_collision(self, other: 'Body') -> bool:
        """Check collision with another body"""
        if not self.collision_enabled or not other.collision_enabled:
            return False
        
        dx = self.x - other.x
        dy = self.y - other.y
        distance = (dx**2 + dy**2) ** 0.5
        
        return distance < (self.radius + other.radius)
    
    def get_id(self):
        """Get body ID"""
        return self._id
    
    def edit_id(self, new_id: str):
        """Edit body ID"""
        old_id = self._id
        self._id = new_id
        return old_id
    
    def edit_kwargs(self, **kwargs):
        """Edit body properties"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Recalculate color if temperature changed
        if 'temperature' in kwargs or 'base_color' in kwargs:
            self.color = self._calculate_color_from_temperature()
        
        self._create_visual()
    
    def kill(self):
        """Remove body from instances"""
        if self in Body._instances:
            Body._instances.remove(self)
    
    @classmethod
    def get_all_instances(cls):
        """Get all Body instances"""
        return cls._instances.copy()
    
    def __repr__(self):
        return f"Body(type={self.bodytype}, mass={self.mass}, pos=({self.x}, {self.y}), id={self._id})"

class BodyManager:
    """Manager class for handling multiple physics bodies"""
    def __init__(self, gravity_enabled: bool = True):
        self.bodies: list[Body] = []
        self.id_map: dict[str, Body] = {}
        self.groups: dict[str, dict] = {}
        self.group_id_counter = 0
        self.gravity_enabled = gravity_enabled
        self.time_scale = 1.0  # Speed up/slow down simulation
    
    def add(self, body: Body):
        """Add an existing body to the manager"""
        if body not in self.bodies:
            # Ensure unique ID
            if body._id:
                body._id = self._ensure_unique_id(body._id)
            else:
                body._id = self._generate_id()
            
            self.bodies.append(body)
            self.id_map[body._id] = body
        return body
    
    def create_body(self, x: int, y: int, bodytype: str, mass: float, **kwargs):
        """Create a new Body without adding it to the manager"""
        body = Body(x, y, bodytype, mass, **kwargs)
        return body
    
    def _ensure_unique_id(self, base_id: str):
        """Ensure ID is unique by appending counter if needed"""
        if base_id not in self.id_map:
            return base_id
        
        counter = 1
        new_id = f"{base_id}_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"{base_id}_{counter}"
        return new_id
    
    def _generate_id(self):
        """Generate a unique ID"""
        counter = len(self.bodies)
        new_id = f"body_{counter}"
        while new_id in self.id_map:
            counter += 1
            new_id = f"body_{counter}"
        return new_id
    
    def get_body_by_id(self, body_id: str):
        """Get body by its ID"""
        return self.id_map.get(body_id, None)
    
    def update_all(self, dt: float = 1.0):
        """Update all bodies with physics"""
        dt *= self.time_scale
        # Apply gravity between all bodies using spatial hashing to reduce O(n^2)
        if self.gravity_enabled and len(self.bodies) > 1:
            cell_size = max(16, int(FisXSettings.spatial_cell_size))
            grid: dict[tuple[int,int], list[int]] = {}
            # populate grid with body indices
            for idx, body in enumerate(self.bodies):
                cx = int(body.x) // cell_size
                cy = int(body.y) // cell_size
                grid.setdefault((cx, cy), []).append(idx)

            # For each body, only interact with bodies in neighboring cells
            for i, body1 in enumerate(self.bodies):
                bx = int(body1.x) // cell_size
                by = int(body1.y) // cell_size
                neighbors = []
                for nx in (bx - 1, bx, bx + 1):
                    for ny in (by - 1, by, by + 1):
                        neighbors.extend(grid.get((nx, ny), []))

                # Cap neighbors to avoid pathological cases
                count = 0
                for j in neighbors:
                    if j <= i:
                        continue
                    if count >= FisXSettings.max_neighbors:
                        break
                    body2 = self.bodies[j]
                    fx, fy = body1.calculate_gravity(body2)
                    # Debug: log extreme forces or distances (rare)
                    dx = body2.x - body1.x
                    dy = body2.y - body1.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if abs(fx) > 1e12 or abs(fy) > 1e12 or dist > 1e6:
                        print(f"GRAVITY DEBUG: bodies {body1._id} - {body2._id}: dx={dx}, dy={dy}, dist={dist}, fx={fx}, fy={fy}")
                    body1.apply_force(fx, fy)
                    body2.apply_force(-fx, -fy)  # Newton's third law
                    count += 1
        
        # Update trajectory predictions before updating positions (expensive; skip for many bodies)
        if any(body.show_trajectory for body in self.bodies):
            # Only compute trajectories for bodies that requested it
            for body in self.bodies:
                if body.show_trajectory:
                    body.trajectory_points = body.predict_trajectory(self.bodies, body.trajectory_steps, body.trajectory_dt)
        
        # Update all bodies
        for body in self.bodies:
            body.update(dt)
    
    def draw_all(self, surface: pygame.Surface):
        """Draw all bodies with simple culling to avoid drawing off-screen objects."""
        # Try to use camera offset stored per-body (main loop sets b._cam_offset)
        for body in self.bodies:
            cam = getattr(body, '_cam_offset', (0, 0))
            cam_x, cam_y = cam
            # Convert body world pos to screen pos
            try:
                sx = int(body.x - cam_x)
                sy = int(body.y - cam_y)
            except Exception:
                # If body has invalid coordinates, skip draw
                continue

            # Cull if fully off-screen plus small margin
            margin = 120
            if sx < -margin or sy < -margin or sx > Screen_Width + margin or sy > Screen_Height + margin:
                # skip drawing bodies far away
                continue

            body.draw(surface)
    
    def kill(self, target):
        """Remove a body by instance or ID"""
        body = None
        if isinstance(target, str):
            body = self.get_body_by_id(target)
        elif isinstance(target, Body):
            body = target
        
        if body and body in self.bodies:
            self.bodies.remove(body)
            if body._id in self.id_map:
                del self.id_map[body._id]
            
            # Remove from groups
            for group_data in self.groups.values():
                if 'bodies' in group_data and body in group_data['bodies']:
                    group_data['bodies'].remove(body)
            
            body.kill()
    
    def group(self, bodies_list: list[Body], name: str, group_id: str = None):
        """Create a group of bodies"""
        if group_id is None:
            group_id = f"group_{self.group_id_counter}"
            self.group_id_counter += 1
        
        self.groups[name] = {
            'id': group_id,
            'bodies': bodies_list.copy()
        }
        self.groups[group_id] = self.groups[name]
        return group_id
    
    def init(self, bodies: list[Body]):
        """Initialize manager with list of bodies"""
        for body in bodies:
            self.add(body)
    
    def draw_group(self, identifier: str, surface: pygame.Surface):
        """Draw all bodies in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            for body in group_data['bodies']:
                body.draw(surface)
    
    def update_group(self, identifier: str, dt: float = 1.0):
        """Update all bodies in a group"""
        group_data = self.groups.get(identifier)
        if group_data:
            for body in group_data['bodies']:
                body.update(dt * self.time_scale)
    
    def get_bodies_in_group(self, identifier: str):
        """Get all bodies in a group by name or ID"""
        group_data = self.groups.get(identifier)
        if group_data:
            return group_data['bodies'].copy()
        return []
    
    def check_collisions(self):
        """Check and return all colliding body pairs using spatial hashing to limit checks."""
        collisions = []
        if not self.bodies:
            return collisions

        cell_size = max(16, int(FisXSettings.spatial_cell_size))
        grid: dict[tuple[int,int], list[int]] = {}
        for idx, body in enumerate(self.bodies):
            cx = int(body.x) // cell_size
            cy = int(body.y) // cell_size
            grid.setdefault((cx, cy), []).append(idx)

        for i, body1 in enumerate(self.bodies):
            bx = int(body1.x) // cell_size
            by = int(body1.y) // cell_size
            neighbors = []
            for nx in (bx - 1, bx, bx + 1):
                for ny in (by - 1, by, by + 1):
                    neighbors.extend(grid.get((nx, ny), []))

            for j in neighbors:
                if j <= i:
                    continue
                body2 = self.bodies[j]
                if body1.check_collision(body2):
                    collisions.append((body1, body2))

        return collisions
    
    def get_bodies_by_type(self, bodytype: str):
        """Get all bodies of a specific type"""
        return [body for body in self.bodies if body.bodytype == bodytype]
    
    def get_particles(self):
        """Get all particle bodies"""
        return self.get_bodies_by_type('particle')
    
    def merge_particles(self, particle1: Body, particle2: Body) -> Body:
        """
        Merge two particles into one larger particle.
        Used when particles collide during accretion.
        """
        if particle1.bodytype != 'particle' or particle2.bodytype != 'particle':
            return particle1
        
        # Calculate combined mass
        total_mass = particle1.mass + particle2.mass
        
        # Calculate center of mass for position
        new_x = (particle1.x * particle1.mass + particle2.x * particle2.mass) / total_mass
        new_y = (particle1.y * particle1.mass + particle2.y * particle2.mass) / total_mass
        
        # Calculate combined momentum for velocity
        new_vx = (particle1.velocity_x * particle1.mass + particle2.velocity_x * particle2.mass) / total_mass
        new_vy = (particle1.velocity_y * particle1.mass + particle2.velocity_y * particle2.mass) / total_mass
        
        # Calculate combined angular velocity
        new_angular_v = (particle1.angular_velocity * particle1.mass + 
                        particle2.angular_velocity * particle2.mass) / total_mass
        
        # Average temperature
        new_temp = (particle1.temperature * particle1.mass + 
                   particle2.temperature * particle2.mass) / total_mass
        
        # Create merged particle
        merged = Body(
            int(new_x), int(new_y), 'particle', total_mass,
            vx=new_vx, vy=new_vy,
            temperature=new_temp,
            angular_velocity=new_angular_v,
            spin_direction=particle1.spin_direction,
            density=(particle1.density + particle2.density) / 2,
            accretion_rate=max(particle1.accretion_rate, particle2.accretion_rate),
            trail=particle1.trail or particle2.trail,
            id=f"{particle1._id}_merged"
        )
        
        # Remove original particles
        self.kill(particle1)
        self.kill(particle2)
        
        # Add merged particle
        self.add(merged)
        
        return merged
    
    def check_particle_mergers(self):
        """
        Check for colliding particles and merge them.
        Returns list of merged particles created.
        """
        particles = self.get_particles()
        merged_list = []
        already_merged = set()
        
        for i, p1 in enumerate(particles):
            if p1 in already_merged:
                continue
            for p2 in particles[i+1:]:
                if p2 in already_merged:
                    continue
                if p1.check_collision(p2):
                    merged = self.merge_particles(p1, p2)
                    merged_list.append(merged)
                    already_merged.add(p1)
                    already_merged.add(p2)
                    break
        
        return merged_list
    
    def create_particle_cloud(self, center_x: int, center_y: int, 
                             num_particles: int, cloud_radius: int,
                             total_mass: float, angular_velocity: float = 0.5,
                             **kwargs):
        """
        Create a cloud of particles that can accrete into a planet/star.
        
        Args:
            center_x, center_y: Center of the cloud
            num_particles: Number of particles to create
            cloud_radius: Radius of the cloud distribution
            total_mass: Total mass distributed among particles
            angular_velocity: Spin speed of the cloud
            **kwargs: Additional properties for particles
        """
        import random
        import math
        
        particles = []
        mass_per_particle = total_mass / num_particles
        
        for i in range(num_particles):
            # Random position within cloud radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, cloud_radius) ** 0.5 * cloud_radius ** 0.5
            
            x = center_x + int(math.cos(angle) * distance)
            y = center_y + int(math.sin(angle) * distance)
            
            # Calculate orbital velocity for spinning cloud
            orbital_speed = angular_velocity * distance
            vx = -math.sin(angle) * orbital_speed
            vy = math.cos(angle) * orbital_speed
            
            particle = self.create_body(
                x, y, 'particle', mass_per_particle,
                vx=vx, vy=vy,
                angular_velocity=angular_velocity,
                spin_direction=1,
                accretion_rate=kwargs.get('accretion_rate', mass_per_particle * 0.001),
                trail=kwargs.get('trail', True),
                trail_length=kwargs.get('trail_length', 30),
                temperature=kwargs.get('temperature', 100),
                **kwargs
            )
            self.add(particle)
            particles.append(particle)
        
        # Create a group for the cloud
        cloud_id = f"cloud_{self.group_id_counter}"
        self.group(particles, cloud_id)
        
        return particles
    
    def get_bodies_at_point(self, x: int, y: int):
        """Get all bodies at a specific point"""
        bodies_at_point = []
        for body in self.bodies:
            dx = x - body.x
            dy = y - body.y
            if (dx**2 + dy**2) ** 0.5 <= body.radius:
                bodies_at_point.append(body)
        return bodies_at_point
    
    def clear_all(self):
        """Remove all bodies from the manager"""
        for body in self.bodies.copy():
            self.kill(body)
    
    def set_gravity(self, enabled: bool):
        """Enable or disable gravity"""
        self.gravity_enabled = enabled
    
    def set_time_scale(self, scale: float):
        """Set simulation speed (1.0 = normal, 2.0 = 2x speed, etc.)"""
        self.time_scale = scale
    
    def get_total_momentum(self) -> tuple[float, float]:
        """Calculate total momentum of system"""
        px = sum(body.mass * body.velocity_x for body in self.bodies)
        py = sum(body.mass * body.velocity_y for body in self.bodies)
        return px, py
    
    def get_total_energy(self) -> float:
        """Calculate total energy (kinetic + potential)"""
        kinetic = sum(0.5 * body.mass * (body.velocity_x**2 + body.velocity_y**2) 
                     for body in self.bodies)
        return kinetic
    
    def set_visualization_all(self, show_trajectory=None, show_forces=None, show_velocity=None):
        """Set visualization options for all bodies"""
        for body in self.bodies:
            if show_trajectory is not None:
                body.show_trajectory = show_trajectory
            if show_forces is not None:
                body.show_forces = show_forces
            if show_velocity is not None:
                body.show_velocity = show_velocity
    
    def set_visualization_by_id(self, body_id: str, show_trajectory=None, show_forces=None, show_velocity=None):
        """Set visualization options for a specific body"""
        body = self.get_body_by_id(body_id)
        if body:
            if show_trajectory is not None:
                body.show_trajectory = show_trajectory
            if show_forces is not None:
                body.show_forces = show_forces
            if show_velocity is not None:
                body.show_velocity = show_velocity
    
    def __len__(self):
        """Return number of bodies in manager"""
        return len(self.bodies)
    
    def __repr__(self):
        return f"BodyManager({len(self.bodies)} bodies, {len(self.groups)//2} groups, gravity={'on' if self.gravity_enabled else 'off'})"
    

om = ObjectManager()
cm = CardManager()


# ---------------------- FisX: Interactive Physics Sandbox ----------------------
import math
import random
import sys


class Units:
    """Very small units helper (display and simple conversions)."""
    G = Body.GRAVITATIONAL_CONSTANT

    @staticmethod
    def newton_from_mass_acc(mass: float, accel: float) -> float:
        return mass * accel

    @staticmethod
    def kinetic_energy(mass: float, vx: float, vy: float) -> float:
        v2 = vx * vx + vy * vy
        return 0.5 * mass * v2

    @staticmethod
    def momentum(mass: float, vx: float, vy: float) -> tuple[float, float]:
        return mass * vx, mass * vy


class FisXSettings:
    """Global toggles and parameters for extended physics."""
    use_coulomb = True
    coulomb_k = 8.9875517923e9  # N·m²/C² (scaled)
    radiation_pressure_enabled = True
    cosmic_expansion_enabled = False
    hubble_constant = 2.2e-18  # s^-1 (scaled for visuals)
    hawking_enabled = True
    hawking_rate = 1e-10  # mass loss per second for demo (scaled)
    relativistic_corrections = True
    speed_of_light = 3e8  # m/s (for lorentz factor)
    dark_matter_enabled = True
    # Unit scaling: how many real meters correspond to one pixel in the simulation.
    # Increase pixels_per_meter to make gravity weaker in screen-space.
    pixels_per_meter = 1e6
    # Additional gravity scale multiplier for tuning gameplay
    gravity_scale = 1.0
    # Spatial hashing cell size for approximate neighbor queries (pixels)
    spatial_cell_size = 400
    # Maximum neighbors to consider per body (safety)
    max_neighbors = 64


def apply_coulomb_force(body: Body, other: Body):
    """Apply Coulomb interaction if bodies have 'charge' attribute (very simplified)."""
    q1 = getattr(body, 'charge', 0)
    q2 = getattr(other, 'charge', 0)
    if q1 == 0 or q2 == 0:
        return 0, 0

    dx = other.x - body.x
    dy = other.y - body.y
    r = max((dx * dx + dy * dy) ** 0.5, 1)
    force = FisXSettings.coulomb_k * (q1 * q2) / (r * r)
    fx = force * (dx / r)
    fy = force * (dy / r)
    return fx, fy


def apply_radiation_pressure(emitter: Body, target: Body):
    """Very simple radiation pressure: emitter pushes target along line-of-sight.
    Uses emitter.radiative_power (Watts) attribute if present.
    """
    power = getattr(emitter, 'radiative_power', 0)
    if power <= 0:
        return 0, 0

    dx = target.x - emitter.x
    dy = target.y - emitter.y
    r = max((dx * dx + dy * dy) ** 0.5, 1)
    # Radiation flux = power / (4*pi*r^2)
    flux = power / (4 * math.pi * r * r)
    # Pressure = flux / c
    pressure = flux / FisXSettings.speed_of_light
    # Force = pressure * cross_section. Approx cross_section ~ pi * radius^2
    area = math.pi * (getattr(target, 'radius', 1) ** 2)
    force = pressure * area
    fx = force * (dx / r)
    fy = force * (dy / r)
    return fx, fy


def apply_hawking_radiation(body: Body, dt: float):
    """Evaporate black holes slowly (toy model)."""
    if body.bodytype != 'black_hole' or not FisXSettings.hawking_enabled:
        return
    loss = FisXSettings.hawking_rate * dt
    body.mass = max(0.0, body.mass - loss)
    # Shrink radius accordingly
    if body.auto_size:
        body.radius = body._calculate_radius_from_mass()


def create_particles(bm: BodyManager, x: float, y: float, total_mass: float, num: int = 8, speed: float = 50.0):
    """Spawn several particle bodies around (x,y) distributing total_mass."""
    import random, math
    if num <= 0 or total_mass <= 0:
        return []
    m_per = total_mass / num
    particles = []
    for i in range(num):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(1, 5)
        px = x + math.cos(angle) * r
        py = y + math.sin(angle) * r
        vx = math.cos(angle) * speed * random.uniform(0.2, 1.2)
        vy = math.sin(angle) * speed * random.uniform(0.2, 1.2)
        p = bm.create_body(int(px), int(py), 'particle', m_per, vx=vx, vy=vy, trail=False)
        bm.add(p)
        particles.append(p)
    return particles


def resolve_collision(bm: BodyManager, a: Body, b: Body):
    """Resolve collision between two bodies with varied outcomes.
    Outcomes: merge (sum up), cancel out (both -> particles), consumption (larger eats smaller), partial consumption,
    gravitational compress (produce particles due to tidal forces).
    """
    # If either body no longer in manager, skip
    if a not in bm.bodies or b not in bm.bodies:
        return

    # Compute basic params
    dx = b.x - a.x
    dy = b.y - a.y
    dist = max((dx*dx + dy*dy) ** 0.5, 1)
    rel_vx = a.velocity_x - b.velocity_x
    rel_vy = a.velocity_y - b.velocity_y
    rel_speed = (rel_vx*rel_vx + rel_vy*rel_vy) ** 0.5

    # effective G in pixel units
    eff_G = Body.GRAVITATIONAL_CONSTANT / (FisXSettings.pixels_per_meter ** 2) * FisXSettings.gravity_scale

    # binding energy estimate ~ G*m1*m2 / r
    binding = eff_G * a.mass * b.mass / max(dist, 1)
    ke_a = 0.5 * a.mass * (a.velocity_x**2 + a.velocity_y**2)
    ke_b = 0.5 * b.mass * (b.velocity_x**2 + b.velocity_y**2)
    total_ke = ke_a + ke_b

    # mass ratio
    if a.mass >= b.mass:
        big, small = a, b
    else:
        big, small = b, a
    mass_ratio = big.mass / max(small.mass, 1)

    # Black hole special: consumption
    if a.bodytype == 'black_hole' or b.bodytype == 'black_hole':
        bh = a if a.bodytype == 'black_hole' else b
        other = b if bh is a else a
        consumed = other.mass * 0.995
        leftover = other.mass - consumed
        bh.mass += consumed
        if leftover > 0:
            create_particles(bm, other.x, other.y, leftover, num=6, speed=30)
        bm.kill(other)
        return

    # If KE >> binding => catastrophic collision: cancel out into particles
    if total_ke > binding * 5e3 or rel_speed > 2000:
        tot_mass = a.mass + b.mass
        create_particles(bm, (a.x + b.x)/2, (a.y + b.y)/2, tot_mass * 0.95, num=max(8, int(tot_mass**0.1)))
        bm.kill(a)
        bm.kill(b)
        return

    # If masses similar and moderate speed => merge (sum up) but lose fraction to particles
    if mass_ratio < 2.5:
        loss_frac = min(0.05 + rel_speed/10000.0, 0.4)
        tot = a.mass + b.mass
        lost = tot * loss_frac
        merged_mass = tot - lost
        # create merged body at center of mass
        nx = (a.x*a.mass + b.x*b.mass) / tot
        ny = (a.y*a.mass + b.y*b.mass) / tot
        nvx = (a.velocity_x*a.mass + b.velocity_x*b.mass) / tot
        nvy = (a.velocity_y*a.mass + b.velocity_y*b.mass) / tot
        merged = bm.create_body(int(nx), int(ny), 'planet' if merged_mass < 1e29 else 'star', merged_mass, vx=nvx, vy=nvy)
        bm.add(merged)
        if lost > 0:
            create_particles(bm, nx, ny, lost, num=8, speed= max(20, rel_speed*0.5))
        bm.kill(a)
        bm.kill(b)
        return

    # Partial consumption or full consumption depending on mass ratio and speed
    if mass_ratio >= 2.5 and mass_ratio < 50:
        # partial consumption: big gains most of small mass
        consumed = small.mass * (0.7 + min(0.29, rel_speed/10000.0))
        leftover = small.mass - consumed
        big.mass += consumed
        if leftover > 0:
            create_particles(bm, small.x, small.y, leftover, num=6, speed= max(20, rel_speed*0.3))
        bm.kill(small)
        return

    # Strong mass_ratio => consumption (big eats small)
    if mass_ratio >= 50:
        big.mass += small.mass
        bm.kill(small)
        return

    # Default fallback: merge
    tot = a.mass + b.mass
    nx = (a.x*a.mass + b.x*b.mass) / tot
    ny = (a.y*a.mass + b.y*b.mass) / tot
    nvx = (a.velocity_x*a.mass + b.velocity_x*b.mass) / tot
    nvy = (a.velocity_y*a.mass + b.velocity_y*b.mass) / tot
    merged = bm.create_body(int(nx), int(ny), 'planet', tot, vx=nvx, vy=nvy)
    bm.add(merged)
    bm.kill(a)
    bm.kill(b)


def apply_cosmic_expansion(bm: 'BodyManager', dt: float):
    """Apply Hubble-like expansion: add velocity proportional to distance from origin (center of screen).
    This is for demonstration and is heavily scaled.
    """
    if not FisXSettings.cosmic_expansion_enabled:
        return
    # Use screen center as local comoving frame
    cx = Screen_Width / 2
    cy = Screen_Height / 2
    for body in bm.bodies:
        dx = body.x - cx
        dy = body.y - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist == 0:
            continue
        v = FisXSettings.hubble_constant * dist
        body.velocity_x += (dx / dist) * v * dt
        body.velocity_y += (dy / dist) * v * dt


def relativistic_velocity_correction(body: Body):
    """Clamp velocities and optionally apply Lorentz factor to mass for visual effect (toy model)."""
    if not FisXSettings.relativistic_corrections:
        return
    vx, vy = body.velocity_x, body.velocity_y
    speed = math.hypot(vx, vy)
    c = FisXSettings.speed_of_light * 1e-6  # scaled c for game speeds
    if speed >= c:
        # clamp to slightly below c
        factor = (c - 1) / max(speed, 1)
        body.velocity_x *= factor
        body.velocity_y *= factor
    else:
        # optional relativistic mass increase for near-c speeds
        if speed > 0.1 * c:
            gamma = 1.0 / math.sqrt(1 - (speed * speed) / (c * c))
            body.mass *= min(gamma, 1.0001)  # tiny effect


def spawn_preset(bm: BodyManager, kind: str, x: int, y: int, mass: float = None):
    """Create common presets: planet, star, black_hole, rocket, cloud, dark_matter."""
    if kind == 'planet':
        m = mass if mass else 5.972e24
        b = bm.create_body(x, y, 'planet', m, vx=0, vy=0, trail=True, trail_length=100)
        bm.add(b)
        return b
    if kind == 'star':
        m = mass if mass else 1.989e30
        b = bm.create_body(x, y, 'star', m, vx=0, vy=0, radiative_power=3.828e26, trail=False)
        bm.add(b)
        return b
    if kind == 'black_hole':
        m = mass if mass else 1e31
        b = bm.create_body(x, y, 'black_hole', m, vx=0, vy=0, trail=False)
        bm.add(b)
        return b
    if kind == 'rocket':
        m = mass if mass else 2e5
        b = bm.create_body(x, y, 'rocket', m, vx=0, vy=0, trail=True)
        # rockets are artificial (belongs handled in Body)
        b.thrust = 0.0
        b.fuel = 1e6
        bm.add(b)
        return b
    if kind == 'cloud':
        return bm.create_particle_cloud(x, y, num_particles=120, cloud_radius=80, total_mass=1e22)
    if kind == 'dark_matter':
        # Invisible mass that affects gravity
        m = mass if mass else 1e28
        b = bm.create_body(x, y, 'dark_matter', m, vx=0, vy=0)
        # Mark so not drawn
        b._is_dark = True
        bm.add(b)
        return b


def draw_overlay(surface: pygame.Surface, bm: BodyManager, paused: bool):
    """Draw HUD overlay with units and current toggles."""
    font = pygame.font.Font(None, 18)
    lines = []
    lines.append(f"FisX — Sandbox (Bodies: {len(bm.bodies)})")
    lines.append(f"Gravity: {'On' if bm.gravity_enabled else 'Off'}  |  Time scale: {bm.time_scale}x  |  Paused: {paused}")
    lines.append(f"Units: kg, m, s, N, J  |  G = {Body.GRAVITATIONAL_CONSTANT:.3e}  |  c(scaled)={FisXSettings.speed_of_light:.3e}")
    lines.append("Controls: Left-click spawn (P/S/B/R/C/D), drag to set velocity, Space pause, L toggle gravity, +/- time scale")
    lines.append("Physics toggles: C Coulomb, R Radiation, E Expansion, H Hawking, T Relativity")

    x = 8
    y = 8
    for line in lines:
        surf = font.render(line, True, (255, 255, 255))
        surface.blit(surf, (x, y))
        y += 20


def main():
    bm = BodyManager()
    # Add a simple demo: star + planet
    star = spawn_preset(bm, 'star', Screen_Width // 2 - 150, Screen_Height // 2, None)
    planet = spawn_preset(bm, 'planet', Screen_Width // 2 + 150, Screen_Height // 2, None)
    # Give planet initial tangential velocity for orbit
    planet.velocity_y = -120.0

    paused = False
    dragging = False
    drag_body = None
    drag_start = (0, 0)
    # Camera/panning
    cam_x = 0
    cam_y = 0
    cam_speed = 800.0

    # UI manager: create a bottom bar with categorized buttons
    ui = om
    ui.clear_all()
    btn_w = 140
    btn_h = 34
    margin = 8
    world_wrap = True

    # Bottom bar coordinates
    bar_y = Screen_Height - btn_h - margin
    bar_x = margin
    categories = ['Spawn', 'Physics', 'View', 'Tools', 'Debug']
    category_buttons = {}

    # Create category buttons along bottom bar using ObjectManager
    for i, cat in enumerate(categories):
        bx = bar_x + i * (btn_w + margin)
        o = ui.create_object(bx, bar_y, (btn_w, btn_h), ui_type=True, text=cat, text_size=16, position_center=True, color=(30,30,40), border_color=(180,180,180), border_thickness=1)
        added = ui.add(o)
        # store uid for potential event handling elsewhere
        added.uid = f"ui_cat_{cat.lower()}"
        category_buttons[cat] = added

    # Create spawn preset sub-buttons placed just above the bottom bar
    sub_y = bar_y - btn_h - (margin // 2)
    sub_btn_w = 110
    sub_margin = 6
    spawn_presets = [
        ('Planet', 'ui_spawn_planet'),
        ('Star', 'ui_spawn_star'),
        ('BlackHole', 'ui_spawn_bh'),
        ('Rocket', 'ui_spawn_rocket'),
        ('Cloud', 'ui_spawn_cloud'),
        ('Dark', 'ui_spawn_dark')
    ]
    spawn_buttons = {}
    # center the spawn buttons above the bar
    total_width = len(spawn_presets) * (sub_btn_w + sub_margin) - sub_margin
    start_x = max(margin, (Screen_Width - total_width) // 2)
    for i, (label, uid) in enumerate(spawn_presets):
        sx = start_x + i * (sub_btn_w + sub_margin)
        o = ui.create_object(sx, sub_y, (sub_btn_w, btn_h), ui_type=True, text=label, text_size=14, position_center=True, color=(40,40,50), border_color=(160,160,160), border_thickness=1)
        added = ui.add(o)
        added.uid = uid
        spawn_buttons[uid] = added

    # A small helper clear button on the right side of the bar
    clear_x = Screen_Width - margin - 120
    o_clear = ui.create_object(clear_x, bar_y, (120, btn_h), ui_type=True, text='Clear All', text_size=14, position_center=True, color=(60,30,30), border_color=(200,80,80), border_thickness=1)
    added_clear = ui.add(o_clear)
    added_clear.uid = 'ui_clear'

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds per frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_l:
                    bm.set_gravity(not bm.gravity_enabled)
                elif event.key == pygame.K_c:
                    FisXSettings.use_coulomb = not FisXSettings.use_coulomb
                elif event.key == pygame.K_r:
                    FisXSettings.radiation_pressure_enabled = not FisXSettings.radiation_pressure_enabled
                elif event.key == pygame.K_e:
                    FisXSettings.cosmic_expansion_enabled = not FisXSettings.cosmic_expansion_enabled
                elif event.key == pygame.K_h:
                    FisXSettings.hawking_enabled = not FisXSettings.hawking_enabled
                elif event.key == pygame.K_t:
                    FisXSettings.relativistic_corrections = not FisXSettings.relativistic_corrections
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    bm.time_scale = max(0.1, bm.time_scale - 0.1)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    bm.time_scale = min(10.0, bm.time_scale + 0.1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    # spawn based on modifier keys (P,S,B,R,C,D mapped to keyboard) or simple spawn menu
                    # For simplicity: spawn planet with left-click; shift+click star; ctrl+click black hole
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT:
                        spawn_preset(bm, 'star', mx, my)
                    elif mods & pygame.KMOD_CTRL:
                        spawn_preset(bm, 'black_hole', mx, my)
                    else:
                        # Check UI click first (use ui manager)
                        clicked = ui.get_objects_at_point(mx, my)
                        if clicked:
                            uid = clicked[0].uid
                            if uid == 'ui_spawn_planet':
                                spawn_preset(bm, 'planet', mx, my)
                            elif uid == 'ui_spawn_star':
                                spawn_preset(bm, 'star', mx, my)
                            elif uid == 'ui_spawn_bh':
                                spawn_preset(bm, 'black_hole', mx, my)
                            elif uid == 'ui_clear':
                                bm.clear_all()
                            elif uid == 'ui_wrap':
                                world_wrap = not world_wrap
                        else:
                            b = spawn_preset(bm, 'planet', mx + cam_x, my + cam_y)
                            dragging = True
                            drag_body = b
                            drag_start = (mx + cam_x, my + cam_y)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and dragging and drag_body:
                    mx, my = pygame.mouse.get_pos()
                    vx = (mx + cam_x - drag_start[0]) * 2
                    vy = (my + cam_y - drag_start[1]) * 2
                    drag_body.velocity_x = vx
                    drag_body.velocity_y = vy
                    dragging = False
                    drag_body = None

        # Camera movement (keyboard)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            cam_x -= cam_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            cam_x += cam_speed * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            cam_y -= cam_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            cam_y += cam_speed * dt

        # Update physics
        if not paused:
            # Apply extra physics interactions
            # Pairwise coulomb & radiation
            if FisXSettings.use_coulomb or FisXSettings.radiation_pressure_enabled:
                for i, b1 in enumerate(bm.bodies):
                    for b2 in bm.bodies[i+1:]:
                        if FisXSettings.use_coulomb:
                            fx, fy = apply_coulomb_force(b1, b2)
                            b1.apply_force(fx, fy)
                            b2.apply_force(-fx, -fy)
                        if FisXSettings.radiation_pressure_enabled:
                            fx, fy = apply_radiation_pressure(b1, b2)
                            b2.apply_force(fx, fy)
                            fx2, fy2 = apply_radiation_pressure(b2, b1)
                            b1.apply_force(fx2, fy2)

            # Hawking evaporation & relativistic corrections
            for b in bm.bodies:
                apply_hawking_radiation(b, dt)
                relativistic_velocity_correction(b)

            # Cosmic expansion
            apply_cosmic_expansion(bm, dt)

            # Standard gravity and updates
            bm.update_all(dt)

            # World wrapping: wrap positions to screen rect if enabled
            if world_wrap:
                for body in bm.bodies:
                    # apply modulo in world coordinates
                    body.x = body.x % Screen_Width
                    body.y = body.y % Screen_Height

            # Collision handling: detect collisions and resolve
            collisions = bm.check_collisions()
            for a, b in collisions:
                # ensure both still present
                if a in bm.bodies and b in bm.bodies:
                    resolve_collision(bm, a, b)

        # Draw
        screen.fill((8, 8, 24))
        # Draw bodies, hiding dark matter
        for b in bm.bodies:
            if getattr(b, '_is_dark', False):
                continue
            # set camera offset for this draw call
            # prefer to pass cam tuple directly by setting attribute used by draw
            b._cam_offset = (cam_x, cam_y)
            b.draw(screen)

        # Draw UI on top
        ui.draw_all(screen)

        # Draw overlay
        draw_overlay(screen, bm, paused)

        # Draw drag line
        if dragging and drag_body:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(screen, (255, 255, 0), drag_start, (mx, my), 2)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print('Error running FisX:')
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)

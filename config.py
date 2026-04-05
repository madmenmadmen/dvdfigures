# config.py

# Размеры окна
WIDTH = 1000
HEIGHT = 700
FPS = 60

# ЦВЕТА
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
PURPLE = (200, 50, 200)
CYAN = (50, 220, 220)
BUTTON_COLOR = (60, 60, 80)
BUTTON_RED = (200, 60, 60)

# Цвета DVD логотипа
DVD_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 100, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (255, 165, 0), (255, 192, 203),
]

# Пути к изображению DVD логотипа
DVD_LOGO_PATHS = [
    "/storage/emulated/0/Download/DVD_VIDEO_logo.png",
    "C:/Users/madmen3733/Documents/DVD_VIDEO_logo.png"
]

# Вершины куба
CUBE_VERTICES = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
]

CUBE_FACES = [
    [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
    [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]
]

BASE_SHAPES = ['cube', 'sphere', 'cone', 'cylinder', 'pyramid', 'torus', "cut_torus",
          'octahedron', 'tetrahedron', 'prism', 'cuboid', 'star', 'crystal',
          'icosahedron', 'dodecahedron', 'frustum', 'ellipsoid', 'mobius', 'spiral', "stick"]
          
CUSTOM_SHAPES = []

SHAPES = BASE_SHAPES.copy()

SHAPE_NAMES = ["КУБ", "СФЕРА", "КОНУС", "ЦИЛИНДР", "ПИРАМИДА", "ТОР", "УСЕЧ. ТОР", 
               "ОКТАЭДР", "ТЕТРАЭДР", "ПРИЗМА", "ПАРАЛЛЕЛЕПИПЕД", "ЗВЕЗДА", "КРИСТАЛЛ",
               "ИКОСАЭДР", "ДОДЕКАЭДР", "УСЕЧ.ПИРАМИДА", "ЭЛЛИПСОИД", "ЛЕНТА МЁБИУСА", "СПИРАЛЬ", "ПАЛКА"]

# Параметры фигур
PRISM_SIDES = 6
CUBOID_WIDTH = 1.5
CUBOID_HEIGHT = 0.8
CUBOID_DEPTH = 1.2
SPHERE_SEGMENTS = 8
SPHERE_RINGS = 6
CONE_SEGMENTS = 16
CYLINDER_SEGMENTS = 16
TORUS_RING_SEGMENTS = 24
TORUS_TUBE_SEGMENTS = 12
STAR_POINTS = 10
CRYSTAL_FACETS = 6
ICOSAHEDRON_RADIUS = 1.0
FRUSTUM_TOP_RADIUS = 0.5
FRUSTUM_BOTTOM_RADIUS = 1.0
FRUSTUM_HEIGHT = 1.5
ELLIPSOID_RADIUS_X = 1.2
ELLIPSOID_RADIUS_Y = 0.8
ELLIPSOID_RADIUS_Z = 1.0
MOBIUS_SEGMENTS = 24
MOBIUS_WIDTH = 0.3
MOBIUS_RADIUS = 1.0
SPIRAL_TURNS = 3
SPIRAL_HEIGHT = 2.0
SPIRAL_RADIUS = 1.0
SPIRAL_SEGMENTS = 24

# Начальные значения
INITIAL_ROTATION_SPEED = 1.0
INITIAL_CUBE_VELOCITY = [3, 2]
INITIAL_ANGLES = [0, 0, 0]
INITIAL_CUBE_POS = [WIDTH // 2, HEIGHT // 2]
RENDER_SCALE = 300
CAMERA_DISTANCE = 5
ELASTICITY = 0.8

# Управление
ROTATION_BUTTONS_TEXT = ["W", "S", "A", "D", "Q", "E"]
ROTATION_BUTTONS_CONTROLS = ["X+", "X-", "Y+", "Y-", "Z+", "Z-"]
ROTATION_INCREMENT = 0.2

# config.py
# Скорость движения
MIN_SPEED = 0
MAX_SPEED = 12.0
DEFAULT_SPEED = 3.0
SPEED_SLIDER_WIDTH = 200
SPEED_SLIDER_HEIGHT = 20

# Эффекты камеры
FLASH_DURATION = 200  # мс длительность вспышки
SCREENSHOT_COUNTER = 0  # Счетчик скриншотов

# Освещение
LIGHT_POS = [5, 5, 5]      # позиция источника света
LIGHT_AMBIENT = 0.3        # фоновое освещение (минимум)
LIGHT_INTENSITY = 1.0      # яркость
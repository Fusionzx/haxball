from enum import IntEnum

class Teams(IntEnum):
    SPECTATORS = 0
    RED = 1
    BLUE = 2

class ChatStyle:
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    SMALL = "small"
    SMALL_BOLD = "small-bold"
    SMALL_ITALIC = "small-italic"

class ChatSounds(IntEnum):
    NONE = 0
    NORMAL = 1
    NOTIFICATION = 2

class Stadiums:
    CLASSIC = "Classic"
    BIG = "Big"
    SMALL = "Small"
    ROUND = "Round"
    BIG_BEACH = "BigBeach"
    SMALL_BEACH = "SmallBeach"
    HUGE = "Huge"
    DOUBLE_TROUBLE = "Double Trouble"
    EASY_ICE = "Easy Ice"
    PRO = "Pro"

class Colors:
    WHITE = 0xFFFFFF
    BLACK = 0x000000
    RED = 0xFF0000
    GREEN = 0x00FF00
    BLUE = 0x0000FF
    YELLOW = 0xFFFF00
    CYAN = 0x00FFFF
    MAGENTA = 0xFF00FF
    SILVER = 0xC0C0C0
    GRAY = 0x808080
    MAROON = 0x800000
    OLIVE = 0x808000
    DARK_GREEN = 0x008000
    PURPLE = 0x800080
    TEAL = 0x008080
    NAVY = 0x000080
    ORANGE = 0xFFA500
    GOLD = 0xFFD700
    LIME = 0x00FF00
    AQUA = 0x00FFFF
    PINK = 0xFFC0CB
    MEDIUM_SEA_GREEN = 0x3CB371
    CORNFLOWER_BLUE = 0x6495ED
    DEEP_PINK = 0xFF1493
    ORANGE_RED = 0xFF4500
    TOMATO = 0xFF6347
    CORAL = 0xFF7F50
    DARK_ORANGE = 0xFF8C00
    HOT_PINK = 0xFF69B4
    VIOLET = 0xEE82EE
    PLUM = 0xDDA0DD
    ORCHID = 0xDA70D6
    THISTLE = 0xD8BFD8
    PEACH_PUFF = 0xFFDAB9
    MISTY_ROSE = 0xFFE4E1
    LAVENDER = 0xE6E6FA

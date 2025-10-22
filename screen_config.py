from screeninfo import get_monitors

class ScreenConfig:
    def __init__(self):
        monitor = get_monitors()[0]
        self.screen_width = monitor.width
        self.screen_height = monitor.height

    def aspect_ratio(self, fmt):
        if isinstance(fmt, tuple):
            w_ratio, h_ratio = fmt
        elif isinstance(fmt, (int, float)):
            w_ratio, h_ratio = fmt, fmt
        elif isinstance(fmt, str):
            fmt = fmt.lower().strip()
            presets = {
                "square": (1, 1),
                "wide": (16, 9),
                "portrait": (9, 16),
                "ultrawide": (21, 9),
            }
            if fmt in presets:
                w_ratio, h_ratio = presets[fmt]
            else:
                sep = "x" if "x" in fmt else ":"
                w_ratio, h_ratio = map(float, fmt.split(sep))
        else:
            raise TypeError("Formato inválido")

        if w_ratio >= h_ratio:
            width = self.screen_width * 0.6
            height = width * (h_ratio / w_ratio)
        else:
            height = self.screen_height * 0.6
            width = height * (w_ratio / h_ratio)

        return int(width), int(height)

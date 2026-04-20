import datetime

class TimeManager:
    def __init__(self, start_date=None, time_scale=60):
        """
        Initializes the time manager.
        :param start_date: datetime object for start time (default Jan 1st 2000).
        :param time_scale: Multiplier for real-time (default 60 = 1 game minute per real second).
        """
        if start_date is None:
            self.current_date = datetime.datetime(2000, 1, 1, 8, 0, 0)
        else:
            self.current_date = start_date
        
        self.time_scale = time_scale

    def update(self, dt_seconds):
        """Advances game time by scaled delta time."""
        delta = datetime.timedelta(seconds=dt_seconds * self.time_scale)
        self.current_date += delta

    def get_time_string(self):
        """Returns formatted Date - Time string."""
        return self.current_date.strftime("%b %d, %Y - %H:%M")

    def get_formatted_date(self):
        return self.current_date.strftime("%b %d, %Y")

    def get_formatted_time(self):
        return self.current_date.strftime("%H:%M:%S")

    def get_lighting_tint(self):
        """
        Calculates an RGB tint based on the hour of the day.
        Returns (R, G, B) tuple to be used with BLEND_RGBA_MULT.
        """
        hour = self.current_date.hour + self.current_date.minute / 60.0
        
        # Color definitions
        DAY_COLOR = (255, 255, 255)
        SUNRISE_COLOR = (255, 180, 120)
        SUNSET_COLOR = (255, 140, 80)
        NIGHT_COLOR = (40, 40, 100)
        
        if 5.0 <= hour < 7.0: # Sunrise transition
            t = (hour - 5.0) / 2.0
            return self._interpolate(NIGHT_COLOR, SUNRISE_COLOR, t)
        elif 7.0 <= hour < 9.0: # Morning transition
            t = (hour - 7.0) / 2.0
            return self._interpolate(SUNRISE_COLOR, DAY_COLOR, t)
        elif 9.0 <= hour < 17.0: # Clear day
            return DAY_COLOR
        elif 17.0 <= hour < 19.0: # Sunset transition
            t = (hour - 17.0) / 2.0
            return self._interpolate(DAY_COLOR, SUNSET_COLOR, t)
        elif 19.0 <= hour < 21.0: # Late sunset to night
            t = (hour - 19.0) / 2.0
            return self._interpolate(SUNSET_COLOR, NIGHT_COLOR, t)
        else: # Full night
            return NIGHT_COLOR

    def _interpolate(self, col1, col2, t):
        r = int(col1[0] + (col2[0] - col1[0]) * t)
        g = int(col1[1] + (col2[1] - col1[1]) * t)
        b = int(col1[2] + (col2[2] - col1[2]) * t)
        return (r, g, b)

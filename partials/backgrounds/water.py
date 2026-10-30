# The water itself: the layer at the very back

from partials.backgrounds.base import Layer


class WaterSurface(Layer):
    # For now just the plain background color; depth and reflections come later

    def draw(self, surface, palette):
        surface.fill(palette["bg"])

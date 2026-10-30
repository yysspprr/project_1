# The building blocks every background is made of
#
# A background is a stack of layers, drawn back to front.
# Each layer looks after one thing (the water, the ripples, the rain...)
# and has the same three methods the game already calls on a background:
#   update(dt)                  move things along; dt is milliseconds since the last frame
#   wobble()                    called on every wobble tick, for the hand-drawn boil
#   draw(surface, palette)      paint itself


class Layer:
    # A layer that does nothing: real layers replace the methods they need

    def __init__(self, scene):
        self.scene = scene          # the background this layer belongs to, so layers can reach each other

    def update(self, dt):
        pass

    def wobble(self):
        pass

    def draw(self, surface, palette):
        pass


class LayeredBackground:
    # Runs a list of layers: the first one added is drawn first (at the back)

    def __init__(self):
        self.layers = []

    def add(self, layer):
        self.layers.append(layer)
        return layer                # handy: self.ripples = self.add(Ripples(self))

    def update(self, dt):
        for layer in self.layers:
            layer.update(dt)

    def wobble(self):
        for layer in self.layers:
            layer.wobble()

    def draw(self, surface, palette):
        for layer in self.layers:
            layer.draw(surface, palette)

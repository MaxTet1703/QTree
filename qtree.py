import threading
from PIL import Image, ImageDraw


class Quadrant:

    def __init__(self, image: Image.Image, box, depth):
        self.box = box
        self.depth = depth
        self.children = None
        self.leaf = False

        image = image.crop(box)
        self.width, self.height = image.size
        hist = image.histogram()
        self.color, self.error = Quadrant.color_from_histogram(hist)

    @staticmethod
    def weighted_average(hist):
        total = sum(hist)
        value, error = 0, 0
        if total > 0:
            value = sum(i * x for i, x in enumerate(hist)) / total
            error = sum(x * (value - i) ** 2 for i, x in enumerate(hist)) / total
            error = error ** 0.5
        return value, error

    @staticmethod
    def color_from_histogram(hist):
        r, re = Quadrant.weighted_average(hist[:256])
        g, ge = Quadrant.weighted_average(hist[256:512])
        b, be = Quadrant.weighted_average(hist[512:768])
        e = re * 0.2989 + ge * 0.5870 + be * 0.1140
        return (int(r), int(g), int(b)), e

    def is_leaf(self):
        return self.leaf

    def split(self, image):
        left, top, right, bottom = self.box
        left_right = left + (right-left) // 2
        top_bottom = top + (bottom - top) // 2
        north_west = Quadrant(image, (left, top, left_right, top_bottom), self.depth + 1)
        nort_east = Quadrant(image, (left_right, top, right, top_bottom), self.depth + 1)
        south_west = Quadrant(image, (left, top_bottom, left_right, bottom), self.depth + 1)
        south_east = Quadrant(image, (left_right, top_bottom, right, bottom), self.depth + 1)
        self.children = [
            north_west,
            nort_east,
            south_west,
            south_east
        ]



class QTree:
    def __init__(self):
        pass

import threading
from PIL import Image, ImageDraw

PADDING = 0
OUTPUT_SCALE = 1
ERROR_THRESHOLD = 7


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
        left_right = left + (right - left) // 2
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
    def __init__(self, image: Image.Image, max_depth=1024):
        self.root = Quadrant(image, image.getbbox(), 0)
        self.width, self.height = image.size

        self.max_depth = 0
        self.build_tree(image, self.root, max_depth)

    def build_tree(self, image, node, max_depth):
        """Recursively adds nodes untill max_depth is reached or error is less than 5"""
        if (node.depth >= max_depth) or (node.error <= ERROR_THRESHOLD):
            if node.depth > self.max_depth:
                self.max_depth = node.depth
            node.leaf = True
            return

        node.split(image)
        if node == 0:
            threaders = []
            for child in node.children:
                thread = threading.Thread(target=self.build_tree, args=(image, child, max_depth))
                threaders.append(thread)
                thread.start()
            for thread in threaders:
                thread.join()
        else:
            for child in node.children:
                self.build_tree(image, child, max_depth)

    def get_leaf_nodes(self, depth):
        """Gets all the nodes on a given depth/level"""

        def get_leaf_nodes_recusion(tree, node, depth, func):
            """Recusivley gets leaf nodes based on whether a node is a leaf or the given depth is reached"""
            if node.leaf is True or node.depth == depth:
                func(node)
            elif node.children is not None:
                for child in node.children:
                    get_leaf_nodes_recusion(tree, child, depth, func)

        if depth > self.max_depth:
            raise ValueError('A depth larger than the trees depth was given')

        leaf_nodes = []
        get_leaf_nodes_recusion(self, self.root, depth, leaf_nodes.append)
        return leaf_nodes

    def create_image_from_depth(self, depth, show_tree = False):
        """Creates a Pillow image object from a given level/depth of the tree"""
        m = OUTPUT_SCALE
        dx, dy = (PADDING, PADDING)  # padding for each image section
        image = Image.new('RGB', (int(self.width * m + dx),
                                  int(self.height * m + dy)))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.width * m + dx,
                        self.height * m + dy), (0, 0, 0))

        leaf_nodes = self.get_leaf_nodes(depth)
        for node in leaf_nodes:
            l, t, r, b = node.box
            box = (l * m + dx, t * m + dy, r * m - 1, b * m - 1)
            draw.rectangle(box, node.color)
        return image

    def render_at_depth(self, depth=0):
        """Renders the image of a given depth/level"""
        if depth > self.max_depth:
            raise ValueError('A depth larger than the trees depth was given')

        image = self.create_image_from_depth(depth)
        image.show()

    def create_gif(self, file_name, duration=1000, loop=0):
        """Creates a gif at the given filename from each level of the tree"""
        images = []
        end_product_image = self.create_image_from_depth(self.max_depth)
        for i in range(self.max_depth):
            image = self.create_image_from_depth(i)
            images.append(image)
        for _ in range(4):
            images.append(end_product_image)
        images[0].save(
            file_name,
            save_all=True,
            append_images=images[1:],
            duration=duration, loop=loop)


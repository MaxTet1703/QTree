import threading
from PIL import Image, ImageDraw

ERROR_THRESHOLD = 7


class QuadNode:

    def __init__(self, image: Image.Image, box, depth):

        """
        Создание узла квадродерева на изображении

        :param image: изображение
        :param box:
        :param depth: глубина узла
        """

        self.box = box
        self.depth = depth
        self.children = None
        self.leaf = False

        image = image.crop(box)
        self.width, self.height = image.size
        hist = image.histogram()
        self.color, self.error = QuadNode.get_colors(hist)

    @staticmethod
    def color_average(hist):
        """
        Вычисление среднего значение для каждого цвета и его ошибки

        :param hist: Часть гистограммы где находятся данные про rgb
        :return:
        """
        total = sum(hist)
        value, error = 0, 0
        if total > 0:
            value = sum(i * x for i, x in enumerate(hist)) / total
            error = sum(x * (value - i) ** 2 for i, x in enumerate(hist)) / total
            error = error ** 0.5
        return value, error

    @staticmethod
    def get_colors(hist):

        """
        Получение среднего цвета в квадранте и ошибки

        :param hist:
        :return:
        """

        r, re = QuadNode.color_average(hist[:256])
        g, ge = QuadNode.color_average(hist[256:512])
        b, be = QuadNode.color_average(hist[512:768])
        e = re * 0.2989 + ge * 0.5870 + be * 0.1140
        return (int(r), int(g), int(b)), e

    @property
    def is_leaf(self):

        """
        Указание на то, что узел лист, т.е является листом с максимальной глубиной
        в квадродереве, либо ошибка цвета переходит за порог ошибки

        :return:
        """

        return self.leaf

    @is_leaf.setter
    def is_leaf(self, leaf: bool):

        """
        Сеттер для is_leaf

        :param leaf: Новое значение для self.leaf
        :return:
        """

        self.leaf = leaf

    def split(self, image):

        """
        Разделение родительского квадранта узла на 4 квадранта

        :param image: Часть изображения, где происходит разбитие
        :return:
        """

        left, top, right, bottom = self.box
        left_right = left + (right - left) // 2
        top_bottom = top + (bottom - top) // 2

        north_west = QuadNode(image, (left, top, left_right, top_bottom), self.depth + 1)
        nort_east = QuadNode(image, (left_right, top, right, top_bottom), self.depth + 1)
        south_west = QuadNode(image, (left, top_bottom, left_right, bottom), self.depth + 1)
        south_east = QuadNode(image, (left_right, top_bottom, right, bottom), self.depth + 1)

        self.children = [
            north_west,
            nort_east,
            south_west,
            south_east
        ]


class QTree:
    def __init__(self, image: Image.Image, max_depth=None):

        """
        Создание квадродерева, способного сживать изображение

        :param image: Изображение для сжатия
        :param max_depth: Глубина, до которого хотим сжать изображение
        """

        self.root = QuadNode(image, image.getbbox(), 0)
        self.width, self.height = image.size

        if max_depth is None:
            self.max_depth = 0
        self.max_depth = max_depth
        self.build(image, self.root, self.max_depth)

    def build(self, image, node, max_depth):

        """
        Рекурсивное построение квадродерева

        :param image: путь к изображению
        :param node: корневой узел в квадранте изображения
        :param max_depth: Максимальная глубина построения дерева
        :return:
        """

        if (node.depth >= max_depth) or (node.error <= ERROR_THRESHOLD):
            if node.depth > self.max_depth:
                self.max_depth = node.depth
            node.is_leaf = True
            return

        node.split(image)

        if node.depth == 0:
            threaders = []

            for child in node.children:
                thread = threading.Thread(target=self.build, args=(image, child, max_depth))
                threaders.append(thread)
                thread.start()

            for thread in threaders:
                thread.join()

        else:
            for child in node.children:
                self.build(image, child, max_depth)

    def get_nodes(self, depth):

        """
        Полечение списка узлов, глубиной меньше depth

        :param depth: глубина, до которой нам нужны узла дерева
        :return: список узлов квадродерево
        """

        if depth > self.max_depth:
            raise ValueError('A depth larger than the trees depth was given')

        nodes = []
        QTree.search_nodes(self, self.root, depth, nodes.append)
        return nodes

    @staticmethod
    def search_nodes(tree, node, depth, func):

        """
        Рекурсивное получение узлов квадродерева

        :param tree: квадродерево
        :param node: текущий узел
        :param depth: глубина узла
        :param func: функция, добавляющая узел в список узлов
        :return:
        """

        if node.is_leaf is True or node.depth == depth:
            func(node)
        elif node.children is not None:
            for child in node.children:
                QTree.search_nodes(tree, child, depth, func)

    def create_image(self, depth):

        """
        Создание сжатого изображения, учитывая глубину сжатия
        :param depth: глубина сжатия
        :return: Сжатое изображение
        """

        image = Image.new('RGB', (int(self.width), int(self.height)))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.width, self.height), (0, 0, 0))

        nodes = self.get_nodes(depth)

        for node in nodes:
            left, top, right, bottom = node.box
            box = (left, top, right, bottom)
            draw.rectangle(box, node.color)
        return image

    def save_image(self, filename):

        """
        Сохранение сжатой фотографии

        :param filename: Путь, по которому сохранится сжатое изображение
        :return:
        """

        image = self.create_image(self.max_depth)
        image.save(filename)

    def create_gif(self, file_name, duration=1000, loop=0):

        """
        Создание gif-файла

        :param file_name: путь к изображение
        :param duration: Число циклв в gif-файле
        :param loop:
        :return:
        """

        images = []
        end_product_image = self.create_image(self.max_depth)
        for i in range(self.max_depth):
            image = self.create_image(i)
            images.append(image)
        for _ in range(4):
            images.append(end_product_image)
        images[0].save(
            file_name,
            save_all=True,
            append_images=images[1:],
            duration=duration, loop=loop)

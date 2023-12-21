import argparse
from pathlib import Path

from PIL import Image

from qtree import QTree


def cli():

    """
    CLI для сжатия изображения и создании gif-файла

    :return:
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str, help="Путь к изображению")
    parser.add_argument("-d", "--depth", type=int, help="Глубина сжатия")
    parser.add_argument("-g", "--gif", type=bool, action=argparse.BooleanOptionalAction,
                        help="Флаг для создания gif Фотографии")

    pars = parser.parse_args()

    image = Image.open(pars.image)

    if not pars.depth:
        pars.depth = 0

    tree = QTree(image, pars.depth)
    if pars.gif:
        filename = f'results/{Path(pars.image).stem}.gif'
        tree.create_gif(filename)
    else:
        filename = f'results/{Path(pars.image).name}'
        tree.save_image(filename)


if __name__ == "__main__":
    cli()
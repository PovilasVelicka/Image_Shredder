import os.path

import numpy as np
from PIL import Image

class ImageShredder:
    def __init__(self, image_path: str):
        if os.path.exists(image_path):
            self.__image = Image.open(image_path)
            self.__image_array = np.array(self.__image.convert('RGB'))
        else:
            raise IOError(f'File {image_path} not exists')
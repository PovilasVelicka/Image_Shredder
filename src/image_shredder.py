import os.path
from typing import Self
import numpy as np
from PIL import Image



class ImageShredder:
    def __init__(self):
        self.__image_array: np.ndarray = np.array([])


    def save_image(self, path: str) -> Self:
        Image.fromarray(self.__image_array).save(path)
        return Self


    def show_image(self) -> Self:
        Image.fromarray(self.__image_array).show()
        return Self


    def get_image_array(self) -> np.ndarray:
        return self.__image_array.copy()


    def set_from_list(self, images: list[np.ndarray], axis: int = 0) -> Self:
        self.__image_array = np.concatenate(images, axis=axis)
        return self


    def set_from_file(self, path: str) -> Self:
        if os.path.exists(path):
            img = Image.open(path)
            img = img.convert('RGB')
            self.__image_array = np.array(img)
        else:
            raise IOError(f'File {path} not exists')


    def set_from_array(self, np_array: np.ndarray) -> Self:
        self.__image_array = np_array.copy()
        return Self


    def add_image_border(self, color: tuple[int, int, int], width: int = 1) -> Self:
        """
        Adds a border of specified color and thickness around the input image.

        Parameters:
            color (tuple): Border color as a tuple of uint8 values (e.g., (255, 0, 0) for red).
            width (int): Thickness of the border in pixels.
        Returns:
            np.ndarray: New image array with the border added.

        """
        border_color = np.array(color, dtype=np.uint8)

        # Get original image dimensions
        h, w, _ = self.__image_array.shape

        # Compute new dimensions including the border
        new_h = h + 2 * width
        new_w = w + 2 * width

        # Create a new image array filled with the border color
        new_image_array = np.full((new_h, new_w, len(border_color)), border_color, dtype=np.uint8)

        # Insert the original image into the center of the new array
        new_image_array[width:width + h, width:width + w] = self.__image_array

        self.__image_array = new_image_array

        return self


    def crop_image_by_slice(self, slice_width: int, v_slice_count: int | None = None, h_slice_count: int | None = None) -> Self:
        img_height, img_width, _ = self.__image_array.shape

        # Compute the largest crop size divisible by full block layout
        full_block_height = slice_width * v_slice_count if v_slice_count else img_height
        full_block_width = slice_width * h_slice_count if h_slice_count else img_width

        cropped_height = (img_height // full_block_height) * full_block_height
        cropped_width = (img_width // full_block_width) * full_block_width

        self.crop_image(cropped_height, cropped_width)

        return self


    def crop_image(self, new_height: int, new_width: int) -> Self:
        """
        Adjusts the image to the exact size (new_height, new_width) by cropping
        or padding as needed. The content stays centered.

        Parameters:
            new_height (int): Desired output height.
            new_width (int): Desired output width.

        Returns:
            np.ndarray: Image of shape (new_height, new_width, C).
        """
        h, w, c = self.__image_array.shape

        # Determine cropping margins
        crop_top = max((h - new_height) // 2, 0)
        crop_bottom = crop_top + min(new_height, h)
        crop_left = max((w - new_width) // 2, 0)
        crop_right = crop_left + min(new_width, w)

        # Crop image to center
        cropped = self.__image_array[crop_top:crop_bottom, crop_left:crop_right, :]

        # Determine padding if needed
        pad_top = max((new_height - cropped.shape[0]) // 2, 0)
        pad_bottom = new_height - cropped.shape[0] - pad_top
        pad_left = max((new_width - cropped.shape[1]) // 2, 0)
        pad_right = new_width - cropped.shape[1] - pad_left

        # Apply padding (black by default)
        if any([pad_top, pad_bottom, pad_left, pad_right]):
            cropped = np.pad(
                cropped,
                ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
                mode='constant',
                constant_values=0
            )
        self.__image_array = cropped
        return Self


    def _get_sliced_blocks(self, block_size: int, num_blocks_y: int = 1, num_blocks_x: int = 1) -> list[np.ndarray]:
        """
        Slices the input image into smaller blocks based on the block size and number of blocks in Y and X directions.
        The slicing wraps modulo-style if the number of blocks is less than the number of full blocks in the image.

        Parameters:
            block_size (int): The size of each square block in pixels.
            num_blocks_y (int): Number of vertical block groups.
            num_blocks_x (int): Number of horizontal block groups.

        Returns:
            list[np.ndarray]: A list of image blocks, each as a NumPy array.
        """
        # Create row mask to assign each pixel row to a vertical block index
        row_mask = np.array([
            (row // block_size) % num_blocks_y
            for row in range(self.__image_array.shape[0])
        ])

        # Create column mask to assign each pixel column to a horizontal block index
        col_mask = np.array([
            (col // block_size) % num_blocks_x
            for col in range(self.__image_array.shape[1])
        ])

        # Generate all (row, col) block index pairs
        block_indices = np.array([
            (row_idx, col_idx)
            for col_idx in range(num_blocks_x)
            for row_idx in range(num_blocks_y)
        ])

        # Extract and return all blocks matching their respective masks
        return [
            self.__image_array[np.ix_(row_mask == row, col_mask == col)]
            for row, col in block_indices
        ]


    def slice(self, slice_width: int, v_slice_count: int, h_slice_count: int, stack_vertical: bool = False ) -> Self:
        """
        Slices the image into a grid of blocks and concatenates them into a single image.
        Blocks are arranged row-wise (vertically stacked) if stack_vertical is True,
        otherwise column-wise (horizontally stacked).

        Parameters:
            slice_width (int): Size of each square slice in pixels.
            v_slice_count (int): Number of vertical slices (along height).
            h_slice_count (int): Number of horizontal slices (along width).
            stack_vertical (bool): If True, stacks blocks vertically; otherwise horizontally.

        Returns:
            np.ndarray: Image formed by concatenating the sliced blocks.
        """
        # Slice the image into blocks using the helper function
        sliced_blocks = self._get_sliced_blocks(slice_width, v_slice_count, h_slice_count)

        # Choose axis to concatenate blocks
        axis = 1 if stack_vertical else 0

        # Concatenate all blocks into a single image
        self.__image_array =  np.concatenate(sliced_blocks, axis=axis, dtype=np.uint8)

        return self


    def slice_vertical(self, slice_width: int, slice_count: int, rotate: bool = False ) -> Self:
        """
        Vertically slices an image into horizontal blocks and then reassembles them
        either vertically (default) or horizontally (if rotate=True).

        Parameters:
            slice_width (int): Height of each horizontal slice in pixels.
            slice_count (int): Number of slices to extract across the height.
            rotate (bool): If True, stack the slices horizontally instead of vertically.

        Returns:
            np.ndarray: Concatenated image formed by stacking the slices.
        """
        # Slice image into horizontal blocks using a helper
        sliced_blocks = self._get_sliced_blocks(slice_width, 1, slice_count)

        # Choose axis to concatenate: 0 = vertical, 1 = horizontal
        axis = 1 if rotate else 0

        # Concatenate slices along the chosen axis
        self.__image_array = np.concatenate(sliced_blocks, axis=axis, dtype=np.uint8)

        return self


    def slice_horizontal(self, slice_width: int, slice_count: int, rotate: bool = False ) -> Self:
        """
        Horizontally slices an image into vertical blocks and then reassembles them
        either horizontally (default) or vertically (if rotate=True).

        Parameters:
            slice_width (int): Width of each vertical slice in pixels.
            slice_count (int): Number of slices to extract across the width.
            rotate (bool): If True, stack the slices vertically instead of horizontally.

        Returns:
            np.ndarray: Concatenated image formed by stacking the slices.
        """
        # Slice image into vertical blocks using a helper
        sliced_blocks = self._get_sliced_blocks(slice_width, slice_count, 1)

        # Choose axis to concatenate: 1 = horizontal, 0 = vertical
        axis = 0 if rotate else 1

        # Concatenate slices along the chosen axis
        self.__image_array = np.concatenate(sliced_blocks, axis=axis, dtype=np.uint8)

        return self

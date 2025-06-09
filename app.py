from src.image_shredder import ImageShredder
import config

def main():
    # Initialize image shredder
    shredder = ImageShredder()

    # Load original image
    shredder.set_from_file(config.SOURCE_PATH)
    original = shredder.get_image_array()

    # Crop image to ensure clean slicing
    shredder.crop_image_by_slice(config.SLICE_WIDTH, config.H_SLICE_COUNT, config.V_SLICE_COUNT)

    # Perform vertical slicing
    shredder.slice_vertical(config.SLICE_WIDTH, config.V_SLICE_COUNT, rotate=True)
    v_sliced = shredder.get_image_array()

    # Perform horizontal slicing on vertically sliced image
    shredder.set_from_array(v_sliced)
    shredder.slice_horizontal(config.SLICE_WIDTH, config.H_SLICE_COUNT, rotate=False)
    h_sliced = shredder.get_image_array()

    # Prepare all images for display with padding
    images = [original, v_sliced, h_sliced]
    max_width = max(img.shape[1] for img in images) + config.SPACE_AROUND_IMAGE * 2

    for i, img in enumerate(images):
        shredder.set_from_array(img)
        padded_height = img.shape[0] + config.SPACE_AROUND_IMAGE * 2
        shredder.crop_image(padded_height, max_width)
        images[i] = shredder.get_image_array()

    # Display all images stacked vertically
    shredder.set_from_list(images, axis=0)
    shredder.add_image_border(config.BORDER_COLOR, config.BORDER_WIDTH)
    shredder.save_image(config.DESTINATION_PATH)

if __name__ == "__main__":
    main()

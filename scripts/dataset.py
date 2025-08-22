import os
import random
from PIL import Image, ImageEnhance, ImageFilter
import shutil

# Directories
OUT_DIR = 'datasets'
ANIMAL_DIR = 'animals'
BACKGROUND_DIR = 'backgrounds'

# Parameters for transformations and data generation
SCALE_RANGE = (0.2, 1)
ROTATION_RANGE = (-15, 15)
BRIGHTNESS_RANGE = (0.5, 1.2)  # Brightness adjustment range
BLURINESS_RANGE = (0, 1)  # Adjusted: Skewed towards less blur
BLUR_PROBABILITY = 1  # Probability that any blur is applied (30%)
SETS = ['train', 'val', 'test']
SETS_DISTRIBUTION = [0.7, 0.2, 0.1]  # 70% train, 20% val, 10% test
REPEATS_PER_ANIMAL = 20  # Number of times each animal image is used
ALPHA_TOLERANCE = 30
CLASS_NAMES = ['capsicum', 'garlic', 'lemon', 'lime', 'pear', 'potato', 'pumpkin', 'tomato']

# Seed for reproducibility
random.seed("meowmeowmeowmeow")

# Directory setup
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
    
os.makedirs(OUT_DIR, exist_ok=True)

# Sub-directories for train, test, val
for subdir in SETS:
    os.makedirs(os.path.join(OUT_DIR, subdir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, subdir, 'labels'), exist_ok=True)

# Paths to animal and background images
animals = [f for f in os.listdir(ANIMAL_DIR) if f.endswith('.png')]
backgrounds = [b for b in os.listdir(BACKGROUND_DIR) if b.endswith('.png')]

def get_label_index(animal_name):
    for idx, name in enumerate(CLASS_NAMES):
        if animal_name.startswith(name):
            return idx
    return None  # In case the animal name does not match any class

def random_transform(image):
    # Scale
    scale = random.uniform(*SCALE_RANGE)
    new_size = (int(image.width * scale), int(image.height * scale))
    image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Rotate
    rotation = random.uniform(*ROTATION_RANGE)
    image = image.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))

    # Flip
    image = image.transpose(Image.FLIP_LEFT_RIGHT)

    # Brightness
    brightness = random.uniform(*BRIGHTNESS_RANGE)
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)

    # Blurriness
    if random.random() < BLUR_PROBABILITY:  # Only apply blur with a certain probability
        bluriness = random.uniform(*BLURINESS_RANGE)
        image = image.filter(ImageFilter.GaussianBlur(bluriness))

    return image

def composite_image(animal_path, background_path, set_name, instance):
    animal = Image.open(animal_path).convert('RGBA')
    background = Image.open(background_path).convert('RGBA')
    animal_transformed = random_transform(animal)

    # Calculate effective dimensions after transformation
    animal_mask = animal_transformed.split()[-1]  # Get the alpha channel as a mask
    thresholded_mask = animal_mask.point(lambda p: p > ALPHA_TOLERANCE and 255)
    bbox = thresholded_mask.getbbox()
    animal_transformed = animal_transformed.crop(bbox)

    animal_width = bbox[2] - bbox[0]
    animal_height = bbox[3] - bbox[1]

    # Ensure at least 50% of the animal is visible
    x_min = -animal_width // 2
    x_max = background.width - animal_width // 2
    y_min = -animal_height // 2
    y_max = background.height - animal_height // 2

    x = random.randint(x_min, x_max)
    y = random.randint(y_min, y_max)

    background.paste(animal_transformed, (x, y), animal_transformed)
    background_rgb = background.convert('RGB')

    file_name = f"{os.path.splitext(os.path.basename(animal_path))[0]}_{instance}.jpg"
    img_path = os.path.join(OUT_DIR, set_name, 'images', file_name)
    background_rgb.save(img_path)

    # Calculate the visible bounding box
    visible_x = max(x, 0)
    visible_y = max(y, 0)
    visible_width = animal_width + (x - visible_x)
    visible_height = animal_height + (y - visible_y)
    centre_x = visible_x + visible_width // 2
    centre_y = visible_y + visible_height // 2

    # Normalize bounding box
    norm_bbox = [
        centre_x / background.width,
        centre_y / background.height,
        visible_width / background.width,
        visible_height / background.height
    ]

    label_index = get_label_index(os.path.basename(animal_path))
    label_path = os.path.join(OUT_DIR, set_name, 'labels', file_name.replace('.jpg', '.txt'))
    with open(label_path, 'w') as label_file:
        label_file.write(f"{label_index} {' '.join(map(str, norm_bbox))}\n")

total_images = len(animals) * REPEATS_PER_ANIMAL
images_processed = 0

# Image generation process (adjust as needed for your environment)
for animal in animals:
    for i in range(REPEATS_PER_ANIMAL):
        images_processed += 1
        percent_complete = (images_processed / total_images) * 100
        chosen_set = random.choices(SETS, weights=SETS_DISTRIBUTION)[0]
        background = random.choice(backgrounds)
        composite_image(os.path.join(ANIMAL_DIR, animal), os.path.join(BACKGROUND_DIR, background), chosen_set, i)
    print(f"{percent_complete:.2f}% - Processed {animal}")

print(f"Generated {images_processed} images in total.")

import os
import random
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Directory setup
base_dir = 'datasets/train'
image_dir = os.path.join(base_dir, 'images')
label_dir = os.path.join(base_dir, 'labels')

# List all images
images = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]

# Function to display an image with its bounding box
def display_image_with_boxes(image_path, label_path):
    image = Image.open(image_path)
    fig, ax = plt.subplots()

    # Display the image
    ax.imshow(image)

    # Read the label file for bounding box coordinates
    with open(label_path, 'r') as file:
        data = file.read().strip().split()
        x_center, y_center, width, height = map(float, data[1:])
        x_center *= image.width
        y_center *= image.height
        width *= image.width
        height *= image.height
        x1 = x_center - width / 2
        y1 = y_center - height / 2
        rect = patches.Rectangle((x1, y1), width, height, linewidth=1, edgecolor='r', facecolor='none')
        ax.add_patch(rect)

    # Display the image name as the title of the plot
    ax.set_title(os.path.basename(image_path))

    # Adjust the layout to ensure everything is displayed properly
    plt.tight_layout()

    # Handle key press event to close the figure and move to next image
    def on_key(event):
        if event.key == 'enter':
            plt.close(fig)

    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()

while True:  # Continuous loop to show images
    random_image_name = random.choice(images)
    image_path = os.path.join(image_dir, random_image_name)
    label_name = random_image_name.replace('.jpg', '.txt')
    label_path = os.path.join(label_dir, label_name)
    display_image_with_boxes(image_path, label_path)

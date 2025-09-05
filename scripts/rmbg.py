import os
from rembg import remove

input_dir = 'unprocessed'
output_dir = 'animals'

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.lower().endswith('.jpg'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Open image and remove background
        with open(input_path, 'rb') as inp_file:
            input_data = inp_file.read()
            output_data = remove(input_data)

        # Save processed image (default PNG with alpha channel, but we keep the original name extension)
        # If you want transparency, save as PNG
        base_name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, base_name + '.png')  # PNG keeps transparency

        with open(output_path, 'wb') as out_file:
            out_file.write(output_data)

        print(f'Processed {filename} -> {output_path}')

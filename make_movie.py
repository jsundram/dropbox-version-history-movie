import click
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy import ColorClip, ImageSequenceClip, ImageClip, concatenate_videoclips


def format_timestamp(timestamp):
    """Format the timestamp into a readable format."""
    timestamp_obj = datetime.fromisoformat(timestamp)
    return timestamp_obj.strftime("%a %b %d - %H:%M:%S")


def resize_and_timestamp(versions, font):
    # Sort by timestamps so the most recent version is last.
    versions = sorted(versions, key=lambda x: x[1])

    # Determine the dimensions of the most recent version.
    newest = versions[-1]
    max_width, max_height = Image.open(newest[0]).size

    # Use bottom as text_height, even though bottom - top might be more accurate?
    left, top, right, text_height = font.getbbox(format_timestamp(newest[1]))
    padding = 10
    header_height = text_height + padding
    max_height += header_height

    # Pad each image, overlay the timestamp, and save it.
    frames = []
    for file, timestamp in versions:
        overlaid_file = file.replace(".png", "_overlaid.png")
        if not os.path.exists(overlaid_file):
            image = Image.open(file)

            # Pad the image to the size of the most recent version
            padded_image = pad_image_to_size(image, max_width, max_height, header_height)

            # Overlay timestamp
            overlaid = overlay_timestamp(padded_image, font, timestamp, padding)

            # Save overlayed image
            overlaid.save(overlaid_file)
        frames.append(overlaid_file)

    return frames


def pad_image_to_size(image, target_width, target_height, header_height):
    padded_image = Image.new("RGB", (target_width, target_height), color=(255, 255, 255))

    x_offset = (target_width - image.width) // 2
    padded_image.paste(image, (x_offset, header_height))
    return padded_image


def overlay_timestamp(image, font, timestamp, padding):
    draw = ImageDraw.Draw(image)

    # Overlay text
    text = format_timestamp(timestamp)
    text_position = (padding, padding)  # Top-left corner
    shadow_color = (255, 255, 255)      # White
    text_color = (0, 0, 0)              # Black

    # Draw shadow
    shadow_offset = 2
    draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset),
              text, font=font, fill=shadow_color)

    # Draw text
    draw.text(text_position, text, font=font, fill=text_color)

    return image


def create_movie(frames, output_file, fps):
    clip = ImageSequenceClip(frames, fps=fps)
    last_frame = ImageClip(frames[-1], duration=5)
    fade_clip = ColorClip(size=last_frame.size, duration=2)
    final_clip = concatenate_videoclips([clip, last_frame, fade_clip])
    final_clip.write_videofile(output_file, fps=fps, codec="libx264")


@click.command()
@click.option('-m', '--metadata-file', type=click.File('r'), required=True,
    help="json file containing filepaths and dates for all the retrieved versions.")
@click.option('-o', '--output-file', type=click.Path(writable=True, dir_okay=False), required=True,
    help="output filename for the generated movie.")
@click.option('-f', '--fps', type=int, default=1 ,
    help="frames per second that the generated movie will play back at.")
def main(metadata_file, output_file, fps):
    versions = json.load(metadata_file)

    # Define font (use default if specific font not available)
    font_path = os.path.expanduser("~/Library/Fonts/DejaVuSans.ttf")
    font_size = 24
    try:
        font = ImageFont.truetype(font_path, size=font_size)
    except IOError:
        font = ImageFont.load_default(font_size)

    print("Resizing and Overlaying timestamps...")
    frames = resize_and_timestamp(versions, font)

    print("Creating movie...")
    create_movie(frames, output_file, fps)

    print(f"Done! Movie saved as {output_file}.")


if __name__ == "__main__":
    main()

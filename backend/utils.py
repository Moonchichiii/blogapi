from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions


def validate_image(image):
    """
    Validate the uploaded image for format and size.
    """
    if image:
        # Check file format
        if not image.name.lower().endswith(("jpg", "jpeg", "png", "gif", "webp")):
            raise ValidationError(
                "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
            )

        # Check file size
        if image.size > 2 * 1024 * 1024:
            raise ValidationError("Image file too large ( > 2mb )")

        # Check image dimensions
        width, height = get_image_dimensions(image)
        if width > 4096 or height > 4096:
            raise ValidationError(
                "Image dimensions too large. Maximum dimensions are 4096x4096 pixels."
            )

    return image

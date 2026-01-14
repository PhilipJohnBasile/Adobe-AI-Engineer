"""
Image Editor Module

Provides AI-powered image editing capabilities:
- Image upscaling (super-resolution)
- Background removal
- Color adjustments
- Filters and effects
- Format conversion
- Batch processing
"""

import os
import io
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

# Optional imports with fallbacks
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from rembg import remove as remove_background
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats."""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"


class FilterType(Enum):
    """Available image filters."""
    BLUR = "blur"
    SHARPEN = "sharpen"
    CONTOUR = "contour"
    DETAIL = "detail"
    EDGE_ENHANCE = "edge_enhance"
    EMBOSS = "emboss"
    SMOOTH = "smooth"
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    VINTAGE = "vintage"
    WARM = "warm"
    COOL = "cool"
    HIGH_CONTRAST = "high_contrast"
    DRAMATIC = "dramatic"


@dataclass
class ImageMetadata:
    """Image metadata information."""
    width: int
    height: int
    format: str
    mode: str
    file_size: Optional[int] = None
    dpi: Optional[Tuple[int, int]] = None
    has_transparency: bool = False
    color_space: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "mode": self.mode,
            "file_size": self.file_size,
            "dpi": self.dpi,
            "has_transparency": self.has_transparency,
            "color_space": self.color_space
        }


@dataclass
class EditResult:
    """Result of an image editing operation."""
    success: bool
    image: Optional[Any]  # PIL Image
    original_metadata: ImageMetadata
    new_metadata: Optional[ImageMetadata]
    operation: str
    processing_time_ms: float
    error: Optional[str] = None

    def save(self, path: str, format: Optional[str] = None, quality: int = 95) -> bool:
        """Save the edited image to a file."""
        if not self.success or self.image is None:
            return False

        try:
            save_kwargs = {}
            if format and format.lower() in ['jpeg', 'jpg']:
                save_kwargs['quality'] = quality
            elif format and format.lower() == 'webp':
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6  # Best compression

            self.image.save(path, format=format, **save_kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return False


class LocalUpscaler:
    """
    Local image upscaling using interpolation methods.
    For better results, use AI-powered upscaling services.
    """

    def __init__(self):
        self.enabled = HAS_PIL

    def upscale(self, image: "Image.Image", scale: float = 2.0,
                method: str = "lanczos") -> "Image.Image":
        """
        Upscale image using interpolation.

        Args:
            image: PIL Image to upscale
            scale: Scale factor (e.g., 2.0 = 2x size)
            method: Resampling method (lanczos, bicubic, bilinear)

        Returns:
            Upscaled PIL Image
        """
        if not self.enabled:
            raise RuntimeError("PIL not available")

        # Calculate new size
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)

        # Select resampling method
        resample_methods = {
            "lanczos": Image.Resampling.LANCZOS,
            "bicubic": Image.Resampling.BICUBIC,
            "bilinear": Image.Resampling.BILINEAR,
            "nearest": Image.Resampling.NEAREST
        }
        resample = resample_methods.get(method.lower(), Image.Resampling.LANCZOS)

        return image.resize((new_width, new_height), resample)

    def upscale_with_sharpening(self, image: "Image.Image", scale: float = 2.0,
                                sharpen_amount: float = 1.2) -> "Image.Image":
        """Upscale with post-sharpening for better perceived quality."""
        # First upscale
        upscaled = self.upscale(image, scale, "lanczos")

        # Apply sharpening
        enhancer = ImageEnhance.Sharpness(upscaled)
        sharpened = enhancer.enhance(sharpen_amount)

        return sharpened


class AIUpscaler:
    """
    AI-powered image upscaling using external APIs.
    Supports multiple providers: Replicate, DeepAI, etc.
    """

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.deepai_key = os.getenv("DEEPAI_API_KEY")
        self.enabled = bool(self.replicate_token or self.deepai_key)

    def upscale(self, image: "Image.Image", scale: int = 2,
                model: str = "auto") -> Optional["Image.Image"]:
        """
        Upscale image using AI model.

        Args:
            image: PIL Image to upscale
            scale: Scale factor (2 or 4)
            model: Model to use (auto, real-esrgan, swinir)

        Returns:
            Upscaled PIL Image or None if failed
        """
        if not HAS_REQUESTS:
            logger.error("requests library not available")
            return None

        # Try Replicate first
        if self.replicate_token:
            return self._upscale_replicate(image, scale)

        # Fall back to DeepAI
        if self.deepai_key:
            return self._upscale_deepai(image)

        logger.warning("No AI upscaling API configured")
        return None

    def _upscale_replicate(self, image: "Image.Image", scale: int) -> Optional["Image.Image"]:
        """Upscale using Replicate API (Real-ESRGAN model)."""
        try:
            import replicate

            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            # Run Real-ESRGAN model
            output = replicate.run(
                "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                input={
                    "image": buffer,
                    "scale": scale,
                    "face_enhance": False
                }
            )

            # Download result
            if output:
                response = requests.get(output, timeout=60)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))

        except Exception as e:
            logger.error(f"Replicate upscaling failed: {e}")

        return None

    def _upscale_deepai(self, image: "Image.Image") -> Optional["Image.Image"]:
        """Upscale using DeepAI API."""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            response = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={"image": buffer},
                headers={"api-key": self.deepai_key},
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            if "output_url" in result:
                img_response = requests.get(result["output_url"], timeout=60)
                img_response.raise_for_status()
                return Image.open(io.BytesIO(img_response.content))

        except Exception as e:
            logger.error(f"DeepAI upscaling failed: {e}")

        return None


class BackgroundRemover:
    """
    Remove backgrounds from images using AI.
    Uses rembg library or external APIs.
    """

    def __init__(self):
        self.local_enabled = HAS_REMBG
        self.remove_bg_key = os.getenv("REMOVE_BG_API_KEY")
        self.enabled = self.local_enabled or bool(self.remove_bg_key)

    def remove(self, image: "Image.Image",
               method: str = "auto",
               alpha_matting: bool = False) -> Optional["Image.Image"]:
        """
        Remove background from image.

        Args:
            image: PIL Image
            method: Method to use (auto, local, api)
            alpha_matting: Use alpha matting for better edge detection

        Returns:
            Image with transparent background
        """
        if method == "auto":
            if self.local_enabled:
                return self._remove_local(image, alpha_matting)
            elif self.remove_bg_key:
                return self._remove_api(image)

        elif method == "local" and self.local_enabled:
            return self._remove_local(image, alpha_matting)

        elif method == "api" and self.remove_bg_key:
            return self._remove_api(image)

        logger.warning("No background removal method available")
        return None

    def _remove_local(self, image: "Image.Image",
                      alpha_matting: bool = False) -> Optional["Image.Image"]:
        """Remove background using rembg library."""
        try:
            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()

            # Process with rembg
            result_bytes = remove_background(
                image_bytes,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10
            )

            return Image.open(io.BytesIO(result_bytes))

        except Exception as e:
            logger.error(f"Local background removal failed: {e}")
            return None

    def _remove_api(self, image: "Image.Image") -> Optional["Image.Image"]:
        """Remove background using remove.bg API."""
        if not HAS_REQUESTS:
            return None

        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": buffer},
                data={"size": "auto"},
                headers={"X-Api-Key": self.remove_bg_key},
                timeout=60
            )

            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                logger.error(f"remove.bg API error: {response.text}")

        except Exception as e:
            logger.error(f"API background removal failed: {e}")

        return None

    def remove_and_replace(self, image: "Image.Image",
                           background_color: Tuple[int, int, int] = (255, 255, 255),
                           background_image: Optional["Image.Image"] = None) -> Optional["Image.Image"]:
        """Remove background and replace with color or image."""
        # First remove background
        no_bg = self.remove(image)
        if no_bg is None:
            return None

        # Create new background
        if background_image:
            # Resize background to match
            bg = background_image.resize(no_bg.size, Image.Resampling.LANCZOS)
            if bg.mode != "RGBA":
                bg = bg.convert("RGBA")
        else:
            bg = Image.new("RGBA", no_bg.size, (*background_color, 255))

        # Composite
        return Image.alpha_composite(bg, no_bg.convert("RGBA"))


class ImageFilters:
    """Apply various filters and effects to images."""

    def __init__(self):
        self.enabled = HAS_PIL

    def apply_filter(self, image: "Image.Image", filter_type: FilterType) -> "Image.Image":
        """Apply a predefined filter to the image."""
        if not self.enabled:
            raise RuntimeError("PIL not available")

        filter_map = {
            FilterType.BLUR: self._apply_blur,
            FilterType.SHARPEN: self._apply_sharpen,
            FilterType.CONTOUR: self._apply_contour,
            FilterType.DETAIL: self._apply_detail,
            FilterType.EDGE_ENHANCE: self._apply_edge_enhance,
            FilterType.EMBOSS: self._apply_emboss,
            FilterType.SMOOTH: self._apply_smooth,
            FilterType.GRAYSCALE: self._apply_grayscale,
            FilterType.SEPIA: self._apply_sepia,
            FilterType.VINTAGE: self._apply_vintage,
            FilterType.WARM: self._apply_warm,
            FilterType.COOL: self._apply_cool,
            FilterType.HIGH_CONTRAST: self._apply_high_contrast,
            FilterType.DRAMATIC: self._apply_dramatic
        }

        filter_func = filter_map.get(filter_type)
        if filter_func:
            return filter_func(image)

        return image

    def _apply_blur(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.GaussianBlur(radius=2))

    def _apply_sharpen(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.SHARPEN)

    def _apply_contour(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.CONTOUR)

    def _apply_detail(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.DETAIL)

    def _apply_edge_enhance(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.EDGE_ENHANCE)

    def _apply_emboss(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.EMBOSS)

    def _apply_smooth(self, image: "Image.Image") -> "Image.Image":
        return image.filter(ImageFilter.SMOOTH_MORE)

    def _apply_grayscale(self, image: "Image.Image") -> "Image.Image":
        return ImageOps.grayscale(image).convert("RGB")

    def _apply_sepia(self, image: "Image.Image") -> "Image.Image":
        """Apply sepia tone effect."""
        if image.mode != "RGB":
            image = image.convert("RGB")

        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                r, g, b = pixels[x, y]

                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)

                pixels[x, y] = (min(255, tr), min(255, tg), min(255, tb))

        return image

    def _apply_vintage(self, image: "Image.Image") -> "Image.Image":
        """Apply vintage effect (sepia + vignette + slight blur)."""
        # Apply sepia
        result = self._apply_sepia(image.copy())

        # Reduce contrast slightly
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(0.85)

        # Add slight warmth
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(0.9)

        return result

    def _apply_warm(self, image: "Image.Image") -> "Image.Image":
        """Apply warm color temperature."""
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Split channels and adjust
        r, g, b = image.split()

        # Increase red, decrease blue
        r = r.point(lambda x: min(255, int(x * 1.1)))
        b = b.point(lambda x: int(x * 0.9))

        return Image.merge("RGB", (r, g, b))

    def _apply_cool(self, image: "Image.Image") -> "Image.Image":
        """Apply cool color temperature."""
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Split channels and adjust
        r, g, b = image.split()

        # Decrease red, increase blue
        r = r.point(lambda x: int(x * 0.9))
        b = b.point(lambda x: min(255, int(x * 1.1)))

        return Image.merge("RGB", (r, g, b))

    def _apply_high_contrast(self, image: "Image.Image") -> "Image.Image":
        """Apply high contrast effect."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5)

    def _apply_dramatic(self, image: "Image.Image") -> "Image.Image":
        """Apply dramatic effect (high contrast + sharpening + slight desaturation)."""
        # Increase contrast
        result = ImageEnhance.Contrast(image).enhance(1.3)

        # Sharpen
        result = result.filter(ImageFilter.SHARPEN)

        # Slightly desaturate
        result = ImageEnhance.Color(result).enhance(0.85)

        return result


class ColorAdjuster:
    """Adjust color properties of images."""

    def __init__(self):
        self.enabled = HAS_PIL

    def adjust_brightness(self, image: "Image.Image", factor: float) -> "Image.Image":
        """Adjust brightness. factor > 1 = brighter, < 1 = darker."""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def adjust_contrast(self, image: "Image.Image", factor: float) -> "Image.Image":
        """Adjust contrast. factor > 1 = more contrast, < 1 = less contrast."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def adjust_saturation(self, image: "Image.Image", factor: float) -> "Image.Image":
        """Adjust saturation. factor > 1 = more saturated, < 1 = less saturated."""
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    def adjust_sharpness(self, image: "Image.Image", factor: float) -> "Image.Image":
        """Adjust sharpness. factor > 1 = sharper, < 1 = blurrier."""
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    def adjust_all(self, image: "Image.Image",
                   brightness: float = 1.0,
                   contrast: float = 1.0,
                   saturation: float = 1.0,
                   sharpness: float = 1.0) -> "Image.Image":
        """Apply multiple adjustments at once."""
        result = image

        if brightness != 1.0:
            result = self.adjust_brightness(result, brightness)
        if contrast != 1.0:
            result = self.adjust_contrast(result, contrast)
        if saturation != 1.0:
            result = self.adjust_saturation(result, saturation)
        if sharpness != 1.0:
            result = self.adjust_sharpness(result, sharpness)

        return result

    def auto_enhance(self, image: "Image.Image") -> "Image.Image":
        """Automatically enhance image (auto-contrast, brightness, color balance)."""
        # Auto contrast
        result = ImageOps.autocontrast(image, cutoff=1)

        # Slight sharpening
        result = ImageEnhance.Sharpness(result).enhance(1.1)

        return result


class ImageEditor:
    """
    Main image editor interface combining all editing capabilities.

    Usage:
        editor = ImageEditor()
        result = editor.load("photo.jpg")
        result = editor.upscale(result.image, scale=2)
        result = editor.remove_background(result.image)
        result.save("output.png")
    """

    def __init__(self):
        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow is required for image editing")

        self.local_upscaler = LocalUpscaler()
        self.ai_upscaler = AIUpscaler()
        self.bg_remover = BackgroundRemover()
        self.filters = ImageFilters()
        self.color_adjuster = ColorAdjuster()

        # Processing cache
        self.cache: Dict[str, Any] = {}

        # Statistics
        self.stats = {
            "images_processed": 0,
            "upscales": 0,
            "bg_removals": 0,
            "filters_applied": 0
        }

        logger.info("Image editor initialized")
        logger.info(f"AI upscaling: {'enabled' if self.ai_upscaler.enabled else 'disabled'}")
        logger.info(f"Background removal: {'enabled' if self.bg_remover.enabled else 'disabled'}")

    def load(self, source: Union[str, bytes, io.BytesIO, "Image.Image"]) -> EditResult:
        """
        Load an image from various sources.

        Args:
            source: File path, bytes, BytesIO, or PIL Image

        Returns:
            EditResult with loaded image
        """
        start_time = datetime.now()

        try:
            if isinstance(source, Image.Image):
                image = source
            elif isinstance(source, str):
                image = Image.open(source)
            elif isinstance(source, bytes):
                image = Image.open(io.BytesIO(source))
            elif isinstance(source, io.BytesIO):
                image = Image.open(source)
            else:
                raise ValueError(f"Unsupported source type: {type(source)}")

            # Get metadata
            metadata = self._get_metadata(image, source if isinstance(source, str) else None)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=True,
                image=image,
                original_metadata=metadata,
                new_metadata=metadata,
                operation="load",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Failed to load image: {e}")

            return EditResult(
                success=False,
                image=None,
                original_metadata=ImageMetadata(0, 0, "", ""),
                new_metadata=None,
                operation="load",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def upscale(self, image: "Image.Image",
                scale: float = 2.0,
                use_ai: bool = True) -> EditResult:
        """
        Upscale image.

        Args:
            image: PIL Image to upscale
            scale: Scale factor (2 or 4 for AI, any for local)
            use_ai: Use AI upscaling if available

        Returns:
            EditResult with upscaled image
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            result_image = None

            # Try AI upscaling first
            if use_ai and self.ai_upscaler.enabled:
                result_image = self.ai_upscaler.upscale(image, int(scale))

            # Fall back to local upscaling
            if result_image is None:
                result_image = self.local_upscaler.upscale_with_sharpening(image, scale)

            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["upscales"] += 1
            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation=f"upscale_{scale}x",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Upscaling failed: {e}")

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="upscale",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def remove_background(self, image: "Image.Image",
                          method: str = "auto",
                          replace_color: Optional[Tuple[int, int, int]] = None,
                          replace_image: Optional["Image.Image"] = None) -> EditResult:
        """
        Remove background from image.

        Args:
            image: PIL Image
            method: Removal method (auto, local, api)
            replace_color: Optional background color to replace with
            replace_image: Optional background image to replace with

        Returns:
            EditResult with background removed
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            if replace_color or replace_image:
                result_image = self.bg_remover.remove_and_replace(
                    image,
                    background_color=replace_color or (255, 255, 255),
                    background_image=replace_image
                )
            else:
                result_image = self.bg_remover.remove(image, method)

            if result_image is None:
                raise RuntimeError("Background removal failed")

            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["bg_removals"] += 1
            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation="remove_background",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Background removal failed: {e}")

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="remove_background",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def apply_filter(self, image: "Image.Image",
                     filter_type: Union[FilterType, str]) -> EditResult:
        """
        Apply a filter to the image.

        Args:
            image: PIL Image
            filter_type: Filter to apply

        Returns:
            EditResult with filtered image
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            if isinstance(filter_type, str):
                filter_type = FilterType(filter_type.lower())

            result_image = self.filters.apply_filter(image, filter_type)
            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["filters_applied"] += 1
            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation=f"filter_{filter_type.value}",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Filter application failed: {e}")

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="filter",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def adjust(self, image: "Image.Image",
               brightness: float = 1.0,
               contrast: float = 1.0,
               saturation: float = 1.0,
               sharpness: float = 1.0) -> EditResult:
        """
        Adjust image color properties.

        Args:
            image: PIL Image
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor
            saturation: Saturation factor
            sharpness: Sharpness factor

        Returns:
            EditResult with adjusted image
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            result_image = self.color_adjuster.adjust_all(
                image, brightness, contrast, saturation, sharpness
            )

            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation="adjust",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Adjustment failed: {e}")

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="adjust",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def auto_enhance(self, image: "Image.Image") -> EditResult:
        """Automatically enhance image quality."""
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            result_image = self.color_adjuster.auto_enhance(image)
            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation="auto_enhance",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="auto_enhance",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def resize(self, image: "Image.Image",
               width: Optional[int] = None,
               height: Optional[int] = None,
               maintain_aspect: bool = True) -> EditResult:
        """
        Resize image to specific dimensions.

        Args:
            image: PIL Image
            width: Target width (or None to calculate from height)
            height: Target height (or None to calculate from width)
            maintain_aspect: Maintain aspect ratio

        Returns:
            EditResult with resized image
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            if width is None and height is None:
                raise ValueError("Must specify width or height")

            if maintain_aspect:
                if width and not height:
                    ratio = width / image.width
                    height = int(image.height * ratio)
                elif height and not width:
                    ratio = height / image.height
                    width = int(image.width * ratio)

            result_image = image.resize((width, height), Image.Resampling.LANCZOS)
            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation=f"resize_{width}x{height}",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="resize",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def crop(self, image: "Image.Image",
             left: int, top: int, right: int, bottom: int) -> EditResult:
        """Crop image to specified box."""
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            result_image = image.crop((left, top, right, bottom))
            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation="crop",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="crop",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def rotate(self, image: "Image.Image", angle: float,
               expand: bool = True) -> EditResult:
        """Rotate image by specified angle."""
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            result_image = image.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)
            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation=f"rotate_{angle}deg",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="rotate",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def convert_format(self, image: "Image.Image",
                       target_format: Union[ImageFormat, str],
                       output_path: Optional[str] = None,
                       quality: int = 95) -> EditResult:
        """
        Convert image to different format.

        Args:
            image: PIL Image
            target_format: Target format (png, jpeg, webp, etc.)
            output_path: Optional output file path
            quality: Quality for lossy formats

        Returns:
            EditResult with converted image
        """
        start_time = datetime.now()
        original_metadata = self._get_metadata(image)

        try:
            if isinstance(target_format, str):
                target_format = ImageFormat(target_format.lower())

            # Handle mode conversion for JPEG
            result_image = image
            if target_format == ImageFormat.JPEG and image.mode in ["RGBA", "P"]:
                # Convert to RGB for JPEG
                result_image = image.convert("RGB")

            # Save if path provided
            if output_path:
                save_kwargs = {"quality": quality} if target_format in [ImageFormat.JPEG, ImageFormat.WEBP] else {}
                result_image.save(output_path, format=target_format.value.upper(), **save_kwargs)

            new_metadata = self._get_metadata(result_image)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            self.stats["images_processed"] += 1

            return EditResult(
                success=True,
                image=result_image,
                original_metadata=original_metadata,
                new_metadata=new_metadata,
                operation=f"convert_to_{target_format.value}",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return EditResult(
                success=False,
                image=None,
                original_metadata=original_metadata,
                new_metadata=None,
                operation="convert",
                processing_time_ms=processing_time,
                error=str(e)
            )

    def _get_metadata(self, image: "Image.Image",
                      file_path: Optional[str] = None) -> ImageMetadata:
        """Extract metadata from image."""
        file_size = None
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        dpi = image.info.get("dpi")

        return ImageMetadata(
            width=image.width,
            height=image.height,
            format=image.format or "unknown",
            mode=image.mode,
            file_size=file_size,
            dpi=dpi,
            has_transparency=image.mode in ["RGBA", "LA", "PA"],
            color_space=image.mode
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get editor statistics."""
        return {
            **self.stats,
            "ai_upscaling_available": self.ai_upscaler.enabled,
            "bg_removal_available": self.bg_remover.enabled,
            "available_filters": [f.value for f in FilterType]
        }


class BatchImageEditor:
    """Process multiple images with the same operations."""

    def __init__(self, editor: Optional[ImageEditor] = None):
        self.editor = editor or ImageEditor()

    def process_batch(self, images: List[Union[str, "Image.Image"]],
                      operations: List[Dict[str, Any]],
                      output_dir: Optional[str] = None) -> List[EditResult]:
        """
        Apply operations to multiple images.

        Args:
            images: List of image paths or PIL Images
            operations: List of {"operation": "...", **kwargs} dicts
            output_dir: Optional output directory

        Returns:
            List of EditResults
        """
        results = []

        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        for i, source in enumerate(images):
            # Load image
            result = self.editor.load(source)

            if not result.success:
                results.append(result)
                continue

            current_image = result.image

            # Apply each operation
            for op in operations:
                op_name = op.get("operation", "")
                op_kwargs = {k: v for k, v in op.items() if k != "operation"}

                if op_name == "upscale":
                    result = self.editor.upscale(current_image, **op_kwargs)
                elif op_name == "remove_background":
                    result = self.editor.remove_background(current_image, **op_kwargs)
                elif op_name == "filter":
                    result = self.editor.apply_filter(current_image, **op_kwargs)
                elif op_name == "adjust":
                    result = self.editor.adjust(current_image, **op_kwargs)
                elif op_name == "resize":
                    result = self.editor.resize(current_image, **op_kwargs)
                elif op_name == "auto_enhance":
                    result = self.editor.auto_enhance(current_image)

                if result.success:
                    current_image = result.image
                else:
                    break

            # Save if output directory specified
            if output_dir and result.success:
                filename = f"processed_{i}.png"
                if isinstance(source, str):
                    filename = f"processed_{Path(source).stem}.png"

                output_path = Path(output_dir) / filename
                result.save(str(output_path))

            results.append(result)

        return results


# Convenience functions
def upscale_image(source: Union[str, "Image.Image"], scale: float = 2.0,
                  output_path: Optional[str] = None) -> EditResult:
    """Quick upscale function."""
    editor = ImageEditor()
    result = editor.load(source)

    if result.success:
        result = editor.upscale(result.image, scale)

        if output_path and result.success:
            result.save(output_path)

    return result


def remove_bg(source: Union[str, "Image.Image"],
              output_path: Optional[str] = None) -> EditResult:
    """Quick background removal function."""
    editor = ImageEditor()
    result = editor.load(source)

    if result.success:
        result = editor.remove_background(result.image)

        if output_path and result.success:
            result.save(output_path, format="PNG")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("IMAGE EDITOR MODULE")
    print("=" * 60)

    editor = ImageEditor()
    stats = editor.get_stats()

    print("\nCapabilities:")
    print(f"  AI Upscaling: {'Available' if stats['ai_upscaling_available'] else 'Not configured'}")
    print(f"  Background Removal: {'Available' if stats['bg_removal_available'] else 'Not configured'}")
    print(f"\nAvailable Filters:")
    for f in stats['available_filters']:
        print(f"    - {f}")

    print("\n" + "-" * 60)
    print("Usage Example:")
    print("-" * 60)
    print("""
    from src.image_editor import ImageEditor

    editor = ImageEditor()

    # Load image
    result = editor.load("photo.jpg")

    # Upscale 2x
    result = editor.upscale(result.image, scale=2)

    # Remove background
    result = editor.remove_background(result.image)

    # Apply filter
    result = editor.apply_filter(result.image, "vintage")

    # Save result
    result.save("output.png")
    """)

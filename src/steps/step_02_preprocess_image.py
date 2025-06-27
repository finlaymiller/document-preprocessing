import os
from typing import Any, Dict

import cv2
import numpy as np

from utils.files import ensure_dir


def _apply_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert a BGR image to grayscale.

    Parameters
    ----------
    image : np.ndarray
        The input image in BGR format.

    Returns
    -------
    np.ndarray
        The grayscale image.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _apply_denoise(image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Apply Gaussian blur to denoise an image.

    Parameters
    ----------
    image : np.ndarray
        The input image.
    params : dict
        A dictionary containing the kernel size.
        Example: {'kernel_size': [5, 5]}

    Returns
    -------
    np.ndarray
        The denoised image.
    """
    kernel_size = tuple(params.get("kernel_size", (5, 5)))
    return cv2.GaussianBlur(image, kernel_size, 0)


def _apply_threshold(image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Apply thresholding to an image.

    Parameters
    ----------
    image : np.ndarray
        The input image (should be grayscale).
    params : dict
        A dictionary containing the thresholding method and its parameters.
        Example: {'method': 'adaptive_gaussian', 'block_size': 11, 'c': 2}

    Returns
    -------
    np.ndarray
        The binary thresholded image.
    """
    method = params.get("method", "adaptive_gaussian")
    if method == "adaptive_gaussian":
        block_size = params.get("block_size", 11)
        c = params.get("c", 2)
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
        )
    elif method == "otsu":
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    elif method == "simple":
        thresh_value = params.get("threshold", 127)
        _, thresh = cv2.threshold(image, thresh_value, 255, cv2.THRESH_BINARY)
        return thresh
    else:
        raise ValueError(f"Unknown threshold method: {method}")


def _apply_deskew(image: np.ndarray) -> np.ndarray:
    """
    Deskew a binary image by rotating it.

    Parameters
    ----------
    image : np.ndarray
        The input binary image.

    Returns
    -------
    np.ndarray
        The deskewed image.
    """
    # this function works best on thresholded images
    if len(image.shape) > 2 and image.shape[2] > 1:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        grayscale = image

    # assumes light text on a dark background
    if np.mean(grayscale) > 127:
        grayscale = 255 - grayscale

    coords = np.column_stack(np.where(grayscale > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    m = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        image, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return deskewed


def process_image(image_path: str, config: Dict[str, Any]) -> str:
    """
    Process a single image through the preprocessing pipeline.

    Parameters
    ----------
    image_path : str
        The path to the input image.
    config : dict
        The configuration dictionary for this step.

    Returns
    -------
    str
        The path to the final processed image.
    """
    step_config = config["step_02_preprocess_image"]
    output_dir = step_config["output_dir"]
    intermediate_dir = step_config.get("intermediate_dir")
    save_intermediate = step_config.get("save_intermediate_steps", False)
    pipeline_steps = step_config.get("pipeline", [])

    ensure_dir(output_dir)
    if save_intermediate and intermediate_dir:
        ensure_dir(intermediate_dir)

    filename = os.path.basename(image_path)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image from path: {image_path}")

    processed_img = img

    for step in pipeline_steps:
        if not step.get("enabled", False):
            continue

        step_type = step["type"]
        params = step

        if step_type == "grayscale":
            processed_img = _apply_grayscale(processed_img)
        elif step_type == "denoise":
            processed_img = _apply_denoise(processed_img, params)
        elif step_type == "threshold":
            processed_img = _apply_threshold(processed_img, params)
        elif step_type == "deskew":
            processed_img = _apply_deskew(processed_img)
        else:
            # consider logging a warning here
            continue

        if save_intermediate and intermediate_dir:
            step_output_dir = os.path.join(intermediate_dir, step_type)
            ensure_dir(step_output_dir)
            save_path = os.path.join(step_output_dir, filename)
            cv2.imwrite(save_path, processed_img)

    final_path = os.path.join(output_dir, filename)
    cv2.imwrite(final_path, processed_img)
    return final_path

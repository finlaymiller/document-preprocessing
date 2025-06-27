import os
from typing import List, Union

from pdf2image import convert_from_path
from PIL import Image

from utils.files import ensure_dir


def process_pdf(
    pdf_path: str, output_dir: str, dpi: int, output_format: str
) -> List[str]:
    """
    Convert a PDF file to a series of images.

    Parameters
    ----------
    pdf_path : str
        The path to the PDF file.
    output_dir : str
        The directory to save the output images.
    dpi : int
        The resolution (dots per inch) for the output images.
    output_format : str
        The format for the output images (e.g., 'png', 'jpeg').

    Returns
    -------
    List[str]
        A list of paths to the created image files.
    """
    ensure_dir(output_dir)
    pages = convert_from_path(pdf_path, dpi=dpi)
    output_paths = []
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    for i, page in enumerate(pages):
        output_path = os.path.join(
            output_dir, f"{base_filename}_page_{i + 1}.{output_format.lower()}"
        )
        page.save(output_path, output_format.upper())
        output_paths.append(output_path)
    return output_paths


def process_image(image_path: str, output_dir: str, output_format: str) -> str:
    """
    Convert an image to a standard format (PNG).

    Parameters
    ----------
    image_path : str
        The path to the input image file.
    output_dir : str
        The directory to save the output image.
    output_format : str
        The desired output format (e.g., 'png').

    Returns
    -------
    str
        The path to the created image file.
    """
    ensure_dir(output_dir)
    with Image.open(image_path) as img:
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(
            output_dir, f"{base_filename}.{output_format.lower()}"
        )
        img.save(output_path, output_format.upper())
        return output_path


def normalize_file(
    file_path: str, output_dir: str, pdf_dpi: int, output_format: str
) -> Union[List[str], str]:
    """
    Normalize a single file (PDF or image) to a standard image format.

    This function acts as a dispatcher, calling the appropriate
    processing function based on the file extension.

    Parameters
    ----------
    file_path : str
        The path to the file to process.
    output_dir : str
        The directory to save the normalized image(s).
    pdf_dpi : int
        The DPI to use for PDF conversion.
    output_format : str
        The image format for the output files.

    Returns
    -------
    Union[List[str], str]
        A list of output paths for a PDF, or a single output path for an image.
    """
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        return process_pdf(file_path, output_dir, pdf_dpi, output_format)
    else:
        return process_image(file_path, output_dir, output_format)

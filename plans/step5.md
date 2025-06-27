# Step 5: OCR (Optical Character Recognition) - Implementation Plan

This plan details the implementation of the fifth step of the pipeline: performing Optical Character Recognition (OCR) on the pre-processed and analyzed document images. This step is the core of the text extraction process, and its design emphasizes accuracy, configurability, and the generation of rich output formats for downstream tasks like quality assurance and data structuring.

## 1. Goal

To extract textual content from the prepared images using the Tesseract OCR engine. The step will be highly configurable, allowing the user to choose between full-page OCR and region-specific OCR (guided by the layout analysis from Step 3). It will produce multiple output formats, including plain text, word-level confidence data (TSV), and structured hOCR files.

## 2. Proposed Project Structure

This step adds a new module for the OCR logic and a corresponding directory structure for its various outputs.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── ... (previous steps)
│   └── 05_ocr/                   # Output of this step
│       ├── txt/                  # Plain text output (.txt)
│       ├── tsv/                  # Word-level confidence data from Tesseract (.tsv)
│       └── hocr/                 # hOCR output (.hocr)
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── ...
        ├── step_04_enhance_image.py
        └── step_05_ocr.py        # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` will be extended with a new section to control the OCR process. This provides granular control over Tesseract's behavior and the strategy for text extraction.

```yaml
# ... (previous settings) ...

# Step 5: OCR Configuration
step_05_ocr:
  # Input directory for images. This should point to the output of the last active
  # image processing step (e.g., step 2, 3, or 4).
  # The pipeline manager will resolve the correct input directory dynamically.
  
  # Set to true to use the layout analysis results from Step 3 to guide OCR.
  # If false, OCR will be performed on the full page.
  use_layout_analysis: true
  # Directory where layout analysis JSON files are stored.
  layout_analysis_dir: "output/03_layout_analysis/json"

  # Root directory for all OCR outputs.
  output_dir: "output/05_ocr"

  # Tesseract OCR engine configuration
  tesseract_config:
    # Language(s) to use for OCR. For multiple, use '+', e.g., 'eng+fra'.
    lang: "eng"
    # OCR Engine Mode (OEM): 1 for LSTM, 3 for default (legacy + LSTM).
    # Use '1' for better accuracy on many documents.
    oem: 1
    # Page Segmentation Mode (PSM): Defines how Tesseract segments the page.
    # '3': Fully automatic page segmentation (default).
    # '6': Assume a single uniform block of text.
    # '11': Sparse text with OSD.
    # This will be used for full-page OCR. When using layout analysis, PSM should be
    # set per-block, often to '6' or '7' (treat as single line).
    psm: 3
    # Additional Tesseract configuration variables can be passed here.
    # For example, to whitelist certain characters:
    # tessedit_char_whitelist: "0123456789abcdef"
    extra_options: ""
```

## 4. Core Components & Logic

### `src/steps/step_05_ocr.py`
- **Purpose:** This module contains all the business logic for performing OCR. It will interface with the Tesseract engine via the `pytesseract` library.
- **Key Functions:**
    - `process_image(image_path: str, layout_path: str | None, config: dict) -> tuple[str, str, str]`:
        - The main entry point for running OCR on a single document page.
        - Loads the `step_05_ocr` configuration.
        - Loads the image using OpenCV/Pillow.
        - **If `use_layout_analysis` is `true` and `layout_path` is provided:**
            - Reads the JSON layout data.
            - Iterates through the detected text blocks (e.g., 'Text', 'Title', 'List').
            - For each block, it crops the corresponding region from the image.
            - It runs Tesseract on the cropped region. A more specific PSM like '6' (single block) might be used here for better results on isolated blocks.
            - It aggregates the text, TSV, and hOCR data from all blocks.
        - **If `use_layout_analysis` is `false`:**
            - It runs Tesseract on the full image using the PSM defined in the config.
        - Calls helper functions to save the three output formats (`.txt`, `.tsv`, `.hocr`) to their respective directories.
        - Returns a tuple of paths to the three output files.
    - **Private Helper Functions:**
        - `_run_tesseract(image: 'Image', config: dict) -> tuple[str, bytes, bytes]`:
            - Takes a Pillow image and the Tesseract config.
            - Constructs the Tesseract command-line options string from the config (`-l`, `--oem`, `--psm`, and `extra_options`).
            - Uses `pytesseract.image_to_string`, `pytesseract.image_to_data`, and `pytesseract.image_to_pdf_or_hocr` to get the plain text, TSV data, and hOCR data.
            - Returns the three outputs.
        - `_save_output(data: str | bytes, output_path: str)`:
            - A simple utility to write string or byte data to a file, ensuring the output directory exists.

### `src/pipeline_manager.py`
- **Purpose:** Extend orchestration to include the OCR step.
- **Updated Logic:**
    1. After Step 3 (Layout Analysis) completes, the manager has the paths to the images and the corresponding layout JSON files.
    2. It reads the `step_05_ocr` configuration.
    3. It will create a Dask `delayed` object for each document. The task will wrap a call to `steps.step_05_ocr.process_image`.
    4. The manager will intelligently pass the correct arguments: the image path (from step 2 or 4) and, if `use_layout_analysis` is true, the corresponding JSON path from step 3.
    5. It will execute all OCR tasks in parallel using `dask.compute()`.
    6. The results (tuples of output file paths) will be collected and passed to the next step (e.g., Post-OCR Cleanup).

## 5. Dependencies and Setup

### `requirements.txt`
The following dependency is required and should be added to `requirements.txt`.

```
# Python wrapper for Tesseract
pytesseract
```

### External Dependencies
- **Tesseract OCR Engine:** This is a critical system-level dependency. The `README.md` must be updated with clear, platform-specific installation instructions.
    - **macOS (via Homebrew):** `brew install tesseract tesseract-lang`
    - **Debian/Ubuntu:** `sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng` (replace `-eng` with other languages as needed).
    - **Windows:** Requires downloading an official installer from the [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) project. The installer must be configured to add Tesseract to the system's PATH.

This plan provides a robust and flexible framework for integrating OCR into the pipeline, producing rich data that will be essential for quality control and final output generation.

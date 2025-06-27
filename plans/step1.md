# Step 1: Input Normalization - Implementation Plan

This plan details the implementation of the first step of the OCR pre-processing pipeline, "Input Normalization". The design focuses on modularity, configurability, and parallel execution, laying a solid foundation for subsequent pipeline stages.

## 1. Goal

Convert all input files (PDFs and various image formats) into a consistent, high-quality PNG image format, with one file per page. These normalized images will be the input for all subsequent processing steps.

## 2. Proposed Project Structure

A modular structure will separate concerns and make the pipeline easier to manage and extend.

```
document-preprocessing/
├── .gitignore
├── config.yaml
├── input/
│   └── (place source PDFs and images here)
├── output/
│   └── 01_normalized/
│       └── (normalized PNG images will be saved here)
├── requirements.txt
└── src/
    ├── __init__.py
    ├── main.py                     # Main entry point to run the pipeline
    ├── pipeline_manager.py         # Orchestrates pipeline steps and Dask jobs
    ├── steps/
    │   ├── __init__.py
    │   └── step_01_normalize_input.py # Logic for the normalization step
    └── utils/
        ├── __init__.py
        ├── config.py               # Loads and validates configuration
        └── files.py                # File system utilities
```

## 3. Configuration (`config.yaml`)

A central `config.yaml` file will control the pipeline's behavior, making it easy to adjust parameters without changing code.

```yaml
# General Settings
app_name: "Document Preprocessing Pipeline"
log_level: "INFO"

# Dask configuration for parallel processing
dask:
  # Number of parallel workers. Use 'auto' to let Dask decide based on CPU cores.
  num_workers: "auto"

# Step 1: Input Normalization Configuration
step_01_normalize_input:
  input_dir: "input"
  output_dir: "output/01_normalized"
  # DPI for converting PDFs. 300-400 is ideal for OCR. 304 is a multiple of 8.
  pdf_dpi: 304
  # The consistent image format to use for all outputs of this step.
  output_format: "png"
```

## 4. Core Components & Logic

### `src/utils/config.py`
- **Purpose:** Load and provide access to settings from `config.yaml`.
- **Key Function:** `load_config(path: str) -> dict`. This function will read the YAML file, perhaps using a singleton pattern or a simple global object to make the config accessible throughout the application.

### `src/utils/files.py`
- **Purpose:** Provide robust file system utilities.
- **Key Functions:**
    - `ensure_dir(path: str)`: Creates a directory if it doesn't exist.
    - `find_files(directory: str, extensions: list[str]) -> Generator[str, None, None]`: Scans a directory and yields paths for files with the given extensions. This will be used to find all PDFs and images to process.

### `src/steps/step_01_normalize_input.py`
- **Purpose:** Contains the business logic for converting input documents. This module will be called by the pipeline manager for each file.
- **Key Functions:**
    - `process_pdf(pdf_path: str, output_dir: str, dpi: int, output_format: str) -> list[str]`:
        - Takes the path to a single PDF.
        - Uses `pdf2image.convert_from_path` to convert each page into a `Pillow` image object at the specified `dpi`.
        - Saves each page as a separate PNG file in `output_dir`.
        - Naming convention: `{original_filename}_page_{page_number}.png`.
        - Returns a list of file paths for the created images.
    - `process_image(image_path: str, output_dir: str, output_format: str) -> str`:
        - Takes the path to a single image file (e.g., JPG, TIFF).
        - Uses `Pillow` to open the image.
        - Saves it in the standard `output_format` (PNG) to the `output_dir`. This ensures all subsequent steps deal with a single, consistent format.
        - Returns the path of the newly created image file.
    - `run_step(config: dict) -> list[str]`:
        - This will be the main entry function for this step, but the actual orchestration of looping through files will be in `pipeline_manager.py` to facilitate Dask integration. This function will act as a wrapper to decide whether to call `process_pdf` or `process_image` based on file extension.

### `src/pipeline_manager.py`
- **Purpose:** Orchestrate the entire pipeline. It will read the config, find input files, and schedule processing tasks using Dask.
- **Logic for Step 1:**
    1. Load configuration.
    2. Use `utils.files.find_files` to get a list of all processable PDFs and images from the `input_dir`.
    3. Create a Dask `delayed` object for each file. This object will wrap a call to the appropriate processing function (`process_pdf` or `process_image`) from `step_01_normalize_input.py`.
    4. Use `dask.compute(*tasks)` to execute all normalization tasks in parallel.
    5. Collect the list of resulting image paths to pass to the next pipeline step.

### `src/main.py`
- **Purpose:** The main entry point of the application.
- **Logic:**
    1. Initialize logging (e.g., using `rich.logging`).
    2. Instantiate and run the `PipelineManager`.
    3. Print a summary of the results (e.g., number of files processed).

## 5. Dependencies and Setup

### `requirements.txt`
```
# For PDF conversion
pdf2image

# For image manipulation
Pillow

# For configuration files
PyYAML

# For parallel processing
dask[complete]

# For user-friendly CLI output
rich
```

### External Dependencies
- **`poppler`**: This is a system-level dependency required by `pdf2image`. Instructions for installation should be included in the `README.md`.
    - **macOS (via Homebrew):** `brew install poppler`
    - **Debian/Ubuntu:** `sudo apt-get update && sudo apt-get install -y poppler-utils`
    - **Windows:** Requires manual download of binaries and adding them to the system's PATH.

This detailed plan provides a clear roadmap for building the first stage of the document processing pipeline.

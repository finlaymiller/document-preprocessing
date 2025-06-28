# Document Preprocessing Pipeline

A configurable and extensible pipeline for cleaning and preparing documents for OCR.

![Pipeline Diagram](https://mermaid.ink/svg/pako:eNqVVMFuwyAM_BVL55xYcO4g6LBLp912mGY3MOImsGViJEFU1X_fSWqnSdNtsn2S7L2DDoIhwkpgvWIFK1nBWfBGkGvWqXgJbLgYQoP20x3sQ8Qk_FpAAsZLxjPZ-E1Y474JzPjAQsE4K1mHjV7bK5g2pT0m2G44lU3DqT8kM6wJzD01D0gE7V0fI_hWdI3uUqJpXU_fQY8_bL1Fk3k21M_x7Sj6lX3kGvK52PUNe1z9rP1Uf6W9Ln6kP1oD7P5D5-9hP1bVnO6F7V_XG2V6z8BvWf0rC2Z39A8n3V2-P_l-cEwWwLp-870pX0lqB4r05qC7F0D0S_wE25k0s)

## Overview

This project provides a modular pipeline to preprocess PDFs and images, enhancing their quality for more accurate Optical Character Recognition (OCR). It includes steps for normalization, image correction, layout analysis, and more. Each step is configurable and its output can be inspected, allowing for a transparent and iterative workflow.

## Features

-   **PDF and Image Support:** Process both PDF files and common image formats.
-   **Configurable Pipeline:** Enable, disable, and tune each processing step via a YAML configuration file.
-   **Intermediate Outputs:** Each step saves its output, making it easy to debug and visualize the pipeline's effects.
-   **Quality Assurance:** Designed to support QA loops by exposing intermediate results.

## Pipeline Flow

The pipeline processes documents through a series of steps:

```mermaid
graph TD
    A[Input Files <br/>(PDFs, Images)] --> B(Step 1: Normalize);
    B --> C(Step 2: Preprocess Image);
    C --> D{Optional: Enhance?};
    D -- Yes --> E[Step 4: Enhance Image];
    D -- No --> F[Step 3: Layout Analysis];
    E --> F;
    F --> G(Step 5: OCR);
    G --> H{QA Check};
    H -- Passes --> I[Step 6: Post-OCR Cleanup];
    H -- Fails --> J(Retry with new params);
    J --> C;
    I --> K[Step 7: Final Output];
    K --> L[Structured Data <br/>(JSON, Searchable PDF)];
```

## Installation

### Prerequisites

You must have Tesseract OCR and Poppler installed on your system.

**macOS:**
```bash
brew install tesseract poppler
```

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

**Windows:**
-   **Tesseract:** Can be installed using the installer from the [official Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html) or via Chocolatey: `choco install tesseract-ocr`.
-   **Poppler:** Download the latest binaries from [the Poppler for Windows releases page](https://github.com/oschwartz10612/poppler-windows/releases/) and add the `bin/` directory to your system's PATH.

### Repository Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/document-preprocessing.git
    cd document-preprocessing
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    For development, also install the development dependencies:
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Set up pre-commit hooks (for developers):**
    ```bash
    pre-commit install
    ```

### ML Models

Some optional steps, like super-resolution (`ESRGAN`) or de-warping (`DocUNet`), require pre-trained models.

1.  Create a `models/` directory in the project root.
2.  Download the required model files and place them in this directory.

## Configuration

The pipeline is configured using `config.yaml`. To get started, copy the sample configuration:

```bash
cp config.sample.yaml config.yaml
```

Edit `config.yaml` to enable, disable, or tune the pipeline steps. See `config.sample.yaml` for a full list of available parameters.

## Usage

1.  Place your input PDFs or images in the `input/` directory.
2.  Run the pipeline:
    ```bash
    python src/main.py
    ```
3.  Inspect the results in the `output/` directory. Each step of the pipeline will create a subdirectory in `output/` containing its results.

## Project Structure

```
document-preprocessing/
├── input/                # Place input files here
├── output/               # Processed files are saved here
├── models/               # Place ML models here
├── src/                  # Main source code
│   ├── steps/            # Individual pipeline steps
│   ├── utils/            # Utility functions
│   ├── main.py           # Main script to run the pipeline
│   └── pipeline_manager.py # Orchestrates the pipeline
├── tests/                # Test suite
├── .gitignore
├── .pre-commit-config.yaml
├── config.sample.yaml    # Sample configuration
├── CONTRIBUTING.md       # Contribution guidelines
├── LICENSE
├── README.md
└── requirements.txt
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


(and with Cursor Agents)

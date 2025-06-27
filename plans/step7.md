# Step 7: Output Formatting - Implementation Plan

This plan details the implementation of the seventh and final active step of the pipeline, "Output Formatting." This step is responsible for taking the cleaned and structured data produced by the upstream processes and generating a set of final, user-facing output files in various formats. The design emphasizes utility, providing outputs suitable for both machine consumption (JSON) and human use (searchable PDF, plain text).

## 1. Goal

To produce the final, permanent outputs of the document processing pipeline. This step will consolidate the results of all previous stages (like layout analysis and post-OCR cleanup) into one or more of the following formats for each document:
1.  **Structured JSON:** A comprehensive JSON file containing the cleaned text, its logical structure (paragraphs, tables), and the precise coordinates (bounding boxes) for each structural block. This is the canonical machine-readable output.
2.  **Plain Text:** A simple `.txt` file containing the clean, corrected text, suitable for easy indexing or consumption by other tools.

## 2. Proposed Project Structure

This step introduces a new module for its logic and a final `output/` directory to house the final artifacts.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── ... (intermediate steps 01-06)
│   └── 07_final_output/          # Output of this step
│       ├── json/                 # Final structured JSON files
│       ├── pdf/                  # Searchable PDF files
│       └── txt/                  # Plain text files
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── ...
        ├── step_06_post_ocr_cleanup.py
        └── step_07_output_formatting.py # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` will be extended with a section to control which final output formats are generated. This allows the user to opt-in to only the formats they need.

```yaml
# ... (previous settings) ...

# Step 7: Output Formatting Configuration
step_07_output_formatting:
  # This entire step can be enabled or disabled.
  enabled: true
  
  # Input directories. The pipeline manager will resolve these dynamically.
  # post_processed_input_dir: "output/06_post_processed/json/"
  # layout_input_dir: "output/03_layout_analysis/json/"
  # image_input_dir: "output/02_preprocessed/final/" # Use preprocessed images for PDFs

  # Root directory for all final outputs.
  output_dir: "output/07_final_output"

  # Specify which output formats to generate.
  formats:
    json:
      enabled: true
    searchable_pdf:
      enabled: true
    plain_text:
      enabled: true
```

## 4. Core Components & Logic

### `src/steps/step_07_output_formatting.py`
- **Purpose:** Contains all business logic for generating the final output files. It will synthesize information from multiple previous steps.
- **Key Functions:**
    - `process_document(post_processed_path: str, layout_path: str, image_path: str, config: dict) -> dict`:
        - The main entry point for generating final outputs for a single document page.
        - `post_processed_path` points to the structured JSON from Step 6.
        - `layout_path` points to the layout JSON from Step 3.
        - `image_path` points to the pre-processed image to be used for the PDF.
        - Loads the `step_07_output_formatting` configuration.
        - Reads the data from the input JSON files.
        - If `formats.json.enabled` is true, calls `_generate_final_json`.
        - If `formats.searchable_pdf.enabled` is true, calls `_generate_searchable_pdf`.
        - If `formats.plain_text.enabled` is true, calls `_generate_plain_text`.
        - Returns a dictionary of paths to the created output files.

    - **Private Helper Functions:**
        - `_generate_final_json(post_processed_data: list, layout_data: list, output_path: str) -> str`:
            - **Merges** the cleaned text from `post_processed_data` with the bounding box coordinates from `layout_data`.
            - The goal is to produce a single, rich JSON object where each logical block (paragraph, table) has both its cleaned `content` and its `box` coordinates.
            - Saves the merged data to a new JSON file in the `json/` output directory.
            - Returns the path to the created file.
        - `_generate_searchable_pdf(post_processed_data: list, image_path: str, output_path: str) -> str`:
            - Uses the `PyMuPDF` (or `fitz`) library.
            - Creates a new PDF document from the `image_path`.
            - Iterates through the text blocks in `post_processed_data`.
            - For each block of text, it uses `page.insert_textbox()` to draw the text onto the PDF in a hidden layer (e.g., by setting `render_mode=3`). This makes the text selectable and searchable but not visible.
            - The bounding box for `insert_textbox` will come from the layout data (which should be included in the `post_processed_data` after the merge).
            - Saves the final PDF to the `pdf/` output directory.
            - Returns the path to the created file.
        - `_generate_plain_text(post_processed_data: list, output_path: str) -> str`:
            - Iterates through the blocks in `post_processed_data`.
            - Concatenates the `content` of each text-based block (e.g., 'Title', 'Paragraph', 'List').
            - For tables, it could format them as simple, tab-separated text.
            - Saves the resulting string to a `.txt` file in the `txt/` output directory.
            - Returns the path to the created file.

### `src/pipeline_manager.py`
- **Purpose:** Extend orchestration to include the final output generation step.
- **Updated Logic:**
    1. After Step 6 completes, the manager has paths to the final cleaned data, the layout data, and the source images.
    2. It checks if `step_07_output_formatting.enabled` is `true`.
    3. If enabled, it creates a Dask `delayed` object for each document, wrapping a call to `steps.step_07_output_formatting.process_document`.
    4. It passes the necessary inputs: the path to the Step 6 JSON, the Step 3 layout JSON, and the relevant image.
    5. It executes all finalization tasks in parallel using `dask.compute()`.
    6. Upon completion, the pipeline run is finished. The manager can log a summary of the final output file locations.
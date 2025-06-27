# Step 6: Post-OCR Cleanup - Implementation Plan

This plan details the implementation of the sixth step of the pipeline, "Post-OCR Cleanup." This step is crucial for transforming the raw, and often error-prone, output from the OCR engine into clean, structured, and usable data. The design focuses on leveraging the rich outputs from previous steps (Layout Analysis and OCR) to achieve high-fidelity text and structure reconstruction.

## 1. Goal

To correct common OCR errors, reconstruct the logical structure of the document (paragraphs, headings, tables), and produce a clean, structured representation of the document's content. This step will:
1.  Correct spelling errors using a fast, dictionary-based approach.
2.  Utilize the layout information from Step 3 to group OCR'd text into meaningful blocks like paragraphs and lists.
3.  Reconstruct tables by aligning the OCR text with the table structure detected in the layout analysis step.
4.  Optionally, flag low-confidence words or regions for manual review.
5.  Produce a final structured output (e.g., Markdown or JSON) that represents the cleaned content and its structure.

## 2. Proposed Project Structure

This step introduces a new module for its logic and a corresponding directory structure for its structured outputs.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── ... (previous steps)
│   ├── 05_ocr/
│   └── 06_post_processed/        # Output of this step
│       ├── json/                 # Structured JSON output per document
│       └── markdown/             # Human-readable Markdown output per document
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── ...
        ├── step_05_ocr.py
        └── step_06_post_ocr_cleanup.py # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` will be extended with a section to control the post-processing step. This allows for fine-tuning of the cleanup operations.

```yaml
# ... (previous settings) ...

# Step 6: Post-OCR Cleanup Configuration
step_06_post_ocr_cleanup:
  # This entire step can be enabled or disabled.
  enabled: true
  
  # Input directories. The pipeline manager will resolve these dynamically.
  # ocr_input_dir: "output/05_ocr/" # Contains txt, tsv, hocr
  # layout_input_dir: "output/03_layout_analysis/json/"

  # Root directory for all post-processed outputs.
  output_dir: "output/06_post_processed"

  # Spell correction configuration
  spell_correction:
    enabled: true
    # A pre-built dictionary for SymSpellPy.
    dictionary_path: "models/symspell_dictionary.txt"
    # The maximum edit distance for suggestions.
    max_edit_distance: 2

  # Structure restoration configuration
  structure_restoration:
    enabled: true
    # The minimum confidence level from Tesseract's TSV to consider a word valid.
    # Words below this threshold might be flagged or ignored.
    min_word_confidence: 60 # Value from 0-100

  # The desired final output formats. Can be ["json", "markdown"].
  output_formats: ["json", "markdown"]
```

## 4. Core Components & Logic

### `src/steps/step_06_post_ocr_cleanup.py`
- **Purpose:** Contains all business logic for cleaning text and reconstructing the document structure.
- **Key Functions:**
    - `process_document(ocr_outputs: tuple, layout_path: str, config: dict) -> dict`:
        - The main entry point for post-processing a single document.
        - `ocr_outputs` will be a tuple containing paths to the `.txt`, `.tsv`, and `.hocr` files from Step 5.
        - Loads the `step_06_post_ocr_cleanup` configuration.
        - Reads the layout data from `layout_path` (from Step 3).
        - Reads the detailed word/confidence data from the `.tsv` file.
        - **Spell Correction:** If enabled, it initializes the spell checker and runs it on the extracted text.
        - **Structure Restoration:** Calls `_reconstruct_structure`, passing the layout blocks and word data.
        - Saves the final structured content using `_save_json` and/or `_save_markdown`.
        - Returns a dictionary of paths to the created output files.

    - **Private Helper Functions:**
        - `_initialize_spell_checker(config: dict) -> 'SymSpell'`:
            - Initializes and caches a `SymSpell` object with a pre-loaded dictionary to avoid reloading for each document.
        - `_reconstruct_structure(layout_blocks: list, word_data: list) -> list`:
            - This is the core function of this step.
            - It iterates through each layout block (e.g., Title, Text, Table, List) from the layout JSON.
            - For each block, it finds all the words from the OCR `.tsv` data that fall within that block's bounding box.
            - It filters words based on `min_word_confidence`.
            - **For Text/Title/List blocks:** It assembles the words into lines and lines into paragraphs, respecting their geometry.
            - **For Table blocks:** It performs a more detailed analysis to place words into a 2D grid structure (rows/columns). This can be a complex task and might initially be a "best-effort" reconstruction.
            - It returns a list of structured elements (e.g., `{'type': 'paragraph', 'content': '...'}, {'type': 'table', 'content': [['c1', 'c2'], ['d1', 'd2']]}`).
        - `_save_json(data: list, output_path: str)`:
            - Saves the structured content list as a well-formatted JSON file.
        - `_save_markdown(data: list, output_path: str)`:
            - Converts the structured content list into a Markdown string.
            - `Title` -> `# Title Text`
            - `Paragraph` -> `Paragraph text.`
            - `Table` -> Markdown table format.
            - Saves the string to a `.md` file.

### `src/pipeline_manager.py`
- **Purpose:** Extend orchestration to include the post-OCR cleanup step.
- **Updated Logic:**
    1. After Step 5 (OCR) completes, the manager has the paths to the image, layout JSON, and the OCR output files (`txt`, `tsv`, `hocr`).
    2. It checks if `step_06_post_ocr_cleanup.enabled` is `true`.
    3. If enabled, it creates a Dask `delayed` object for each document, wrapping a call to `steps.step_06_post_ocr_cleanup.process_document`.
    4. It passes the necessary inputs: the tuple of OCR output paths and the path to the corresponding layout JSON file.
    5. It executes all cleanup tasks in parallel using `dask.compute()`.
    6. The results (paths to the final structured files) are collected for the final output formatting step.

## 5. Dependencies and Setup

### `requirements.txt`
The following dependencies are required for this step and should be added to `requirements.txt`.

```
# For fast dictionary-based spell correction
symspellpy-bp

# For parsing TSV data efficiently
pandas

# For converting structured data to Markdown
markdown-it-py
```

### External Dependencies & Models
- **SymSpell Dictionary:** This step requires a frequency dictionary file for the spell checker to work. The `README.md` should include instructions on how to download a standard one (e.g., from the SymSpell repository) and place it in the `models/` directory.

This plan provides a clear path for turning raw OCR text into valuable, structured information, making the entire pipeline significantly more powerful and useful.

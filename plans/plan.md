# PDF OCR Pre-Processing Pipeline

This document outlines a complete, modular pipeline for pre-processing PDFs or image-based documents to optimize OCR (Optical Character Recognition) accuracy. Each stage outputs its result to disk so that the effects of that step can be visually inspected and validated. The pipeline supports batch processing with parallelization via Dask.

---

## 1. Input Normalization

**Goal:** Convert all input files (PDFs or images) to a consistent, high-quality image format suitable for OCR.

### Steps:

- For PDFs, convert each page to an image at high resolution (300–400 DPI, ideally a multiple of 8).
- For existing image files, verify resolution and convert to PNG or TIFF if necessary.
- Save each image to disk for visual verification.

### Example:

`pdf2image` (Python):

```python
from pdf2image import convert_from_path
pages = convert_from_path('input.pdf', dpi=304)
for i, page in enumerate(pages):
    page.save(f'normalized/page_{i+1}.png', 'PNG')
```

---

## 2. Image Preprocessing

**Goal:** Enhance image clarity and normalize content for improved OCR.

### Steps:

- **Convert to Grayscale:**

```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

- **Denoise:**

```python
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
```

- **Thresholding:**

```python
thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)
```

- **Deskew:**

```python
coords = np.column_stack(np.where(thresh > 0))
angle = cv2.minAreaRect(coords)[-1]
angle = -(90 + angle) if angle < -45 else -angle
(h, w) = gray.shape[:2]
M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
deskewed = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
```

- **Morphology (Optional):**

```python
kernel = np.ones((1, 1), np.uint8)
dilated = cv2.dilate(thresh, kernel, iterations=1)
```

- Save each intermediate output image (grayscale, thresholded, deskewed) to disk for verification.

---

## 3. Layout Analysis

**Goal:** Detect and separate content regions (text blocks, tables, images).

### Tools:

- `pdfplumber` or `PyMuPDF` for vector PDFs
- `LayoutParser` for ML-based layout detection
- Tesseract `--psm` modes

### Tips:

- Use `--psm 1` (automatic layout) or `--psm 4` (column layout)
- Visualize detected blocks (e.g., rectangles overlaid on image)
- Save visual overlays for verification

---

## 4. Image Enhancement (Optional)

**Goal:** Recover quality from degraded scans or photographed documents.

### Techniques:

- **De-warping:** via DocUNet
- **Super-resolution:** via ESRGAN
- **Contrast Enhancement:**

```python
equalized = cv2.equalizeHist(gray)
```

- Save enhanced images separately for QA.

---

## 5. OCR

**Goal:** Extract text from the prepared images.

### Tools:

- **Tesseract OCR:**

```bash
tesseract input.png output -l eng --oem 1 --psm 6
```

- Save both plain text (`.txt`) and TSV confidence (`.tsv`) outputs.

### Options:

- `--oem 1`: LSTM OCR engine
- `--psm 6`: Single uniform block of text

---

## 6. Post-OCR Cleanup

**Goal:** Fix OCR errors and restore logical structure.

### Steps:

- **Spell Correction:** `SymSpell`
- **Language Correction (Optional):** BERT or similar transformer
- **Structure Restoration:** Group lines into paragraphs, detect titles/headers
- **Table Extraction:** For scanned docs, use `layoutparser` + OCR over bounding boxes
- Save corrected text and reconstructed structure to disk (e.g., JSON, Markdown).

---

## 7. Output Formatting

**Goal:** Save extracted and structured text in accessible formats.

### Options:

- Plaintext (`.txt`)
- Structured JSON with layout metadata
- Searchable PDF (optional with OCRmyPDF or PyMuPDF)

---

## 8. Quality Assurance

**Goal:** Evaluate OCR performance and trigger retries if needed.

### Techniques:

- **Confidence Scoring:** Use Tesseract `.tsv` outputs
- **Bounding Box Visualization:** Overlay detected words/lines on images
- **Retry Logic:** Reprocess low-confidence pages with alternative thresholds, deskewing, or `--psm` values

---

## 9. Parallelization with Dask

**Goal:** Speed up processing for large batches of documents.

### Steps:

- Use `dask.delayed` to wrap each processing step
- Use `dask.compute()` to evaluate in parallel

### Example:

```python
from dask import delayed, compute

@delayed
def process_image(path):
    # normalize, preprocess, OCR, QA, output to disk
    return path

tasks = [process_image(p) for p in image_paths]
results = compute(*tasks)
```

- Store intermediate files per image to inspect steps if errors arise

---

## Summary Flow

```text
PDF/Image --> Normalized Image --> Preprocess (gray, binarize, deskew) --> Layout Analysis --> OCR
          --> Post-OCR Correction --> Structured Output --> QA + Retry
                          ↘ (Parallelized with Dask)
```

This pipeline handles both PDFs and image inputs, outputs each step to disk for validation, and scales efficiently using Dask.


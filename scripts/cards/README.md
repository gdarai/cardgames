# Documentation: `scripts/cards/cards.py`

# Install dependencies
sudo apt-get install python3-opencv
sudo apt-get install python3-numpy
sudo apt-get install python3-pyexcel-ods
sudo apt-get install inkscape
sudo apt-get install texlive-latex-base

## Overview

This script is a card/image processing and printing tool, designed to automate the creation, combination, and export of card images and related assets. It uses configuration files (primarily JSON) to define tasks, card layouts, and data sources. The script supports various operations such as exporting tables, converting SVGs, printing cards, combining PNGs, and generating LaTeX files for PDF output.

---

Main purpose of this script is to allow for rapid prototyping of a card based game. Setup templates for simple cards. Setup individual card data in a collective ods source file(s). Setup randomized data, say counters or card ID's only as templates.

And use the script to quickly regenerate the whole game set every time you do a prototype design change.

---

## Main Inputs

### 1. Command-Line Arguments

- **First argument**: Path to the main settings JSON file (default: `cards.json`)
- **Second argument**: Task name (default: `prototype`)

### 2. Settings JSON File

The main configuration is a JSON file (e.g., `cards.json`) that defines the workflow, card templates, data sources, and parameters. It can be a list of tasks or a nested structure with `_sub` keys.

#### Top-Level Parameters

- `_process`: The operation to perform. Allowed values:
    - `EXPORT_TABLE`
    - `CONVERT_SVGS`
    - `PRINT_CARDS`
    - `PRINT_A_CARD`
    - `COMBINE_PNGS`
    - `SPLIT_TEX`
    - `ADD_TEXT`
    - `TERMINATE`
- `_card`: The base name of the card template (expects `<name>.png` and `<name>.json` to exist).
- `_out`: Output file name or parameter.
- `_count`: Number of times to repeat the operation.
- `_resize`: Resize value for output images.
- `_break`: Line break character for text fields.
- `_yspace`: Vertical space between lines.
- `_onOneLine`: Number of images per line in LaTeX output.
- `_randomize`: Whether to randomize image order.
- `_exportTableParams`: List of parameters for table export.
- `_lists`, `_list`: Definitions for parameter lists (for batch processing).
- `_sub`: List of sub-tasks (for hierarchical processing).

#### Card Parameter Definitions

Each card template (`<name>.json`) defines fields for text and image placement, e.g.:

- `type`: `text` or `img`
- `position`: Coordinates for placement
- `padding`: Padding for text/image
- `font`, `align`, `line`, `fixed`, `color`, `fixed_space`: Text rendering options
- `mask`, `maskTolerance`, `useMask`: Image masking options

#### Data Sources

- `_sourceOds`: Path to an ODS spreadsheet for table export.
- `sheet`, `table`, `target`, `_opp`, `skipTitle`: Table export options.

#### List and Parameter Expansion

- Parameters can be defined as:
    - Constant values (`value`)
    - Regular expressions/ranges (`reg`)
    - Lists (`list`)
    - Linked to other parameters (`{name}`)
    - Conditional (`?{name}{ifNot}`)

---

## Supported Operations

### EXPORT_TABLE

Exports a table from an ODS file to CSV, using parameters for sheet, table index, and output file.

### CONVERT_SVGS

Converts all SVG files in the `svg` directory to PNGs using Inkscape, with optional resizing.

### PRINT_CARDS / PRINT_A_CARD

Generates card images by overlaying text and images onto a template, using parameters from the settings and card JSON.

### COMBINE_PNGS

Combines multiple PNG images into a single image, according to a formula and layout (row/column).

### SPLIT_TEX

Inserts a separator (newline) in the LaTeX output.

### ADD_TEXT

Adds a text block to the LaTeX output.

### TERMINATE

Stops processing.

---

## Output

- **Images**: PNG files in the `print` directory.
- **LaTeX**: A `.tex` file (default: `cards.tex`) for PDF generation.
- **PDF**: Generated via `pdflatex` from the LaTeX file.
- **CSV**: Exported tables from ODS files.

---

## Example Minimal JSON Input

```json
[
  {
    "_process": "PRINT_CARDS",
    "_card": "my_card_template",
    "_count": 10,
    "title": { "list": ["Card 1", "Card 2", "..."] },
    "image": { "list": ["img1.png", "img2.png", "..."] }
  }
]
```

---

## Example: cards.json Input File

Below are annotated examples from a real `cards.json` file, demonstrating how to configure various tasks:

### 1. Exporting Tables from ODS

```
{
  "_process": "EXPORT_TABLE",
  "_sourceOds": "cards.ods",
  "target": "csv_A.csv",
  "sheet": "Test A",
  "skipTitle": 1,
  "table": 1
}
```
- **Purpose:** Exports a table from the `cards.ods` spreadsheet (sheet "Test A", table 1) to `csv_A.csv`.
- **Parameters:**
  - `_sourceOds`: Source ODS file.
  - `target`: Output CSV file.
  - `sheet`: Sheet name in ODS.
  - `skipTitle`: Number of title rows to skip.
  - `table`: Table index in the sheet.

### 2. Converting SVGs

```
{
  "_process": "CONVERT_SVGS"
}
```
- **Purpose:** Converts SVG files to PNG or other formats as needed.

### 3. Printing a Single Card

```
{
  "_resize": 512,
  "_process": "PRINT_A_CARD",
  "_out": { "reg": "png/{name}.png" },
  "_card": "png/card_150x150",
  "_list": { "values": ["name", "text"] },
  "values": [
    { "list": ["two", "four"] },
    { "list": ["2", "4"] }
  ]
}
```
- **Purpose:** Generates individual card images using the template `png/card_150x150`.
- **Parameters:**
  - `_resize`: Output image size.
  - `_out`: Output file pattern.
  - `_card`: Card template.
  - `_list.values`: Parameter names for batch processing.
  - `values`: Lists of values for each parameter.

### 4. Combining PNGs

```
{
  "_process": "COMBINE_PNGS",
  "_formula": ["Ax", "Bx", "Cx"],
  "_skipMissing": "True",
  "_align": "center",
  "_shape": "row",
  "_out": { "reg": "png/comb_{colTgt}.png" },
  "Ax": { "reg": "png/{colA}.png" },
  "Bx": { "reg": "?{colB}{}png/{colB}.png" },
  "Cx": { "reg": "?{colC}{}png/{colC}.png" },
  "_list": { "values": ["colA", "colB", "colC", "colTgt"] },
  "values": "csv_comb.csv"
}
```
- **Purpose:** Combines multiple PNG images into a single image per row, using data from `csv_comb.csv`.
- **Parameters:**
  - `_formula`: Order of image layers.
  - `_align`, `_shape`: Layout options.
  - `_out`: Output file pattern.
  - `Ax`, `Bx`, `Cx`: Input image patterns.
  - `_list.values`: Parameter names.
  - `values`: Source CSV for batch values.

### 5. Printing Multiple Cards

```
{
  "_process": "PRINT_CARDS",
  "_out": "_OUT_A.tex",
  "_card": "png/card_100x150",
  "_onOneLine": 6,
  "_randomize": "True",
  "_list": { "values": ["name", "text", "speed", "img"] },
  "values": "csv_A.csv"
}
```
- **Purpose:** Generates a LaTeX file for printing cards, using data from `csv_A.csv`.
- **Parameters:**
  - `_onOneLine`: Number of cards per line.
  - `_randomize`: Shuffle card order.
  - `_list.values`: Card data fields.

---

## Example Card Template JSON

Below is an example of a card template JSON file (`card_100x150.json`). This file defines the layout and properties for each field on the card:

```json
{
  "name":{
    "type":"text",
    "position":[[0, 0],[100, 30]],
    "padding":[[5,5], [5,5]],
    "font":"HERSHEY_PLAIN",
    "size":4,
    "line":1,
    "color":[0,0,0],
    "align":"center"
  },
  "text":{
    "type":"text",
    "position":[[0, 30],[100, 90]],
    "padding":[[5,5], [5,5]],
    "font":"HERSHEY_PLAIN",
    "size":4,
    "line":1,
    "color":[0,0,0],
    "align":"center"
  },
  "speed":{
    "type":"text",
    "position":[[0, 90],[100, 110]],
    "padding":[[5,5], [5,5]],
    "font":"HERSHEY_PLAIN",
    "size":4,
    "line":1,
    "color":[0,0,0],
    "align":"center"
  },
  "img":{
    "type":"img",
    "position":[[5, 110],[95, 145]]
  }
}
```

**Field Descriptions:**
- `type`: Field type, either `text` or `img`.
- `position`: Coordinates for the top-left and bottom-right corners of the field, in pixels.
- `padding`: Padding for the field, as `[[left,top],[right,bottom]]`.
- `font`: Font used for text fields (e.g., `HERSHEY_PLAIN`).
- `size`: Font size for text fields.
- `line`: Number of lines for text fields.
- `color`: Text color as `[R,G,B]`.
- `align`: Text alignment (e.g., `center`).

This template is referenced by the `_card` parameter in your settings JSON, and the field names (`name`, `text`, `speed`, `img`) must match the data source columns or parameter names used in your configuration.

---

## Notes

- All file paths are relative to the current working directory.
- Card templates require both PNG and JSON files with the same base name.
- The script expects certain directory structures (`svg`, `png`, `print`).
- The script uses OpenCV, NumPy, and pyexcel_ods for image and data processing.

---

## Error Handling

- The script exits with an error message if required files or parameters are missing or malformed.
- It prints progress and error messages to the console.

---

## Summary Table of Key Parameters

| Parameter         | Type      | Description                                      |
|-------------------|-----------|--------------------------------------------------|
| `_process`        | string    | Operation to perform                             |
| `_card`           | string    | Card template base name                          |
| `_out`            | string    | Output file name                                 |
| `_count`          | int       | Number of repetitions                            |
| `_resize`         | int       | Resize value for images                          |
| `_break`          | string    | Line break character for text                    |
| `_yspace`         | int       | Vertical space between lines                     |
| `_onOneLine`      | int       | Images per line in LaTeX output                  |
| `_randomize`      | bool      | Shuffle image order in output                    |
| `_sourceOds`      | string    | Path to ODS file for table export                |
| `_sub`            | list      | List of sub-tasks                                |
| `_list`           | dict      | Parameter lists for batch processing             |

---

For more details, refer to the card template JSON and the main settings JSON structure.
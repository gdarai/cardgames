# FinePrint

FinePrint is a Python script for automating the creation of composite images and text overlays, useful for generating card images, labels, or similar assets. It processes a sequence of tasks defined in a JSON file (by default, `guide.json`).

## Features
- Register and use custom fonts for text rendering
- Compose images from multiple elements
- Generate images from text files
- Clean output directories
- Highly configurable via a JSON task list

## Requirements
- Python 3.x
- [Pillow (PIL)](https://pillow.readthedocs.io/en/stable/): `pip install pillow`
- [ImageMagick](https://imagemagick.org/) (the `convert` command must be available)

## Usage

```bash
python fineprint.py [input.json]
```
- If no argument is given, `guide.json` in the current directory is used.

## Input File Structure
The input JSON file is an array of task objects. Each task must have a `task` field specifying its type. Supported task types:
- `SETUP`: Set global options (e.g., separator character)
- `CLEAN`: Remove a directory and its contents
- `FONT`: Register a font for text rendering
- `BUILD`: Define a composite image build from elements
- `TEXTS`: Generate images from lines of text
- `CARDS`: Compose images using a build and data file

## Task Parameters

### SETUP
- `separator` (string, optional): Field separator for text files (default: `|`).
- `intermediate` (string, optional): File to store an intermediate png state (default: `_intermediate.png`).

### CLEAN
- `target` (string): Directory to remove.

### FONT
- `name` (string): Font identifier for later reference.
- `source` (string): Path to the font file (e.g., TTF).
- `fill` (string): Text color (e.g., `black`).
- `pointSize` (int): Font size in points.
- `rowHeight` (int): Vertical spacing between lines.

### BUILD
- `name` (string): Build identifier for later reference.
- `elements` (array): List of image elements to compose. Each element:
  - `source` (string): Path template for the image (use `[0]`, `[1]`, ... for placeholders).
  - `position` (string): Offset for placement (e.g., `+20+20`).
  - `centered` (bool, optional): Center the element at the position (default: false).

### TEXTS
- `source` (string): Path to the input text file.
- `target` (string): Output image prefix/directory.
- `font` (string): Registered font name.
- `size` (string): Image size and background (e.g., `300x100 xc:none`).
- `firstIsName` (bool, optional): Use the first field as the output file name (default: false).
- `gravity` (string, optional): Setup how the text should be placed in the image (West, NorthWest, default: Center).

### CARDS
- `source` (string): Path to the input data file (text, separated by `separator`). Can be also string '999x999' which will create a new image of the given size for you.
- `base` (string): Path to the base image for composition.
- `target` (string): Output image prefix/directory.
- `build` (string): Registered build name to use for composition.
- `crop` (string, optional): Crop geometry string (e.g., `"10x20+50+100"`). If present, the output image will be cropped to this rectangle using ImageMagick. If not present, no cropping is performed.
- `firstIsName` (bool, optional): Use the first field as the output file name (default: false).

## Example guide.json
```json
[
  { "task": "SETUP", "separator": "|" },
  { "task": "CLEAN", "target": "img" },
  { "task": "FONT", "name": "DejaVu-32", "source": "usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "fill": "black", "pointSize": 32, "rowHeight": 40 },
  { "task": "BUILD", "name": "ExampleBuild", "elements": [
    { "source": "img/titles_[0].png", "position": "+20+20" },
    { "source": "img/texts_[1].png", "centered": true, "position": "+170+250" },
    { "source": "img/values_[2].png", "position": "+20+380" }
  ]},
  { "task": "TEXTS", "source": "text/titles.txt", "target": "img/titles", "font": "DejaVu-32", "size": "300x100 xc:none" },
  { "task": "TEXTS", "source": "text/texts.txt", "target": "img/texts", "font": "DejaVu-32", "size": "300x200 xc:none" },
  { "task": "TEXTS", "source": "text/values.txt", "target": "img/values", "font": "DejaVu-32", "firstIsName": true, "size": "300x100 xc:none" },
  { "task": "CARDS", "source": "src/cards.txt", "base": "src/card.png", "target": "out/card", "build": "ExampleBuild" },
  { "task": "CARDS", "source": "src/cards.txt", "base": "src/card.png", "target": "out/card-crop", "build": "ExampleBuild", "crop": "10x20+50+100" }
]
```

## Notes
- Paths to fonts and images must be valid and accessible.
- For more complex examples, see the provided `guide.json` in this directory.

## License
MIT or project default.

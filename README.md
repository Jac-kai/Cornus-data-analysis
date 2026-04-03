# Cornus-Data-Analysis

A modular Python-based data preprocessing and exploratory data analysis system for tabular datasets.

## Project Overview
Cornus is a Python-based data preprocessing and exploratory data analysis project designed to prepare tabular datasets before machine learning modeling.

This project focuses on the workflow before model training, including data loading, data inspection, data cleaning, computation, transformation, and visualization. It is built with a modular architecture so that each stage of the preprocessing workflow is separated into dedicated components for better readability, maintainability, and future extension.

## Project Purpose
The purpose of Cornus is to help users turn raw tabular datasets into cleaner, more structured, and more understandable data before moving to feature engineering or machine learning workflows.

This project is suitable for:
- data preprocessing practice
- exploratory data analysis workflows
- modular Python project design
- machine learning preparation workflows

## Features
- Load local datasets from multiple file formats
- Inspect dataset structure and summary information
- Check missing values and column-level data conditions
- Clean and preprocess raw tabular data
- Perform column-based calculations and grouped computations
- Reshape datasets for different analysis views
- Generate exploratory visualizations
- Operate through a menu-driven workflow

## Supported File Types
Cornus currently supports:
- CSV
- Excel (`.xlsx`, `.xls`, `.xlsm`)
- JSON
- HTML
- SQL
- TXT

## Workflow Modules

### 1. Data Loading
Handles folder scanning, file discovery, path building, and dataset loading.

### 2. Data Inspection
Handles dataset structure inspection, summary reporting, and missing-value checking.

### 3. Data Cleaning
Handles preprocessing operations such as:
- dropping rows or columns
- handling missing values
- removing duplicates
- trimming string whitespace
- replacing target values

### 4. Data Computation
Handles arithmetic operations, derived columns, grouped summaries, and conditional calculations.

### 5. Data Transformation
Handles reshaping and structure conversion operations such as:
- stack
- unstack
- melt
- pivot
- pivot table

### 6. Data Visualization
Handles exploratory plotting and trend inspection, including:
- line plots
- scatter plots
- pair plots
- histograms
- box plots
- correlation heatmaps

## Project Structure
```text
Cornus-Data-Analysis/
├─ Cornus_Engine.py
├─ Cornus_Main.py
├─ Cornus_Menu1.py
├─ Cornus_Menu2.py
├─ Cornus_Menu3.py
├─ Cornus_Menu4.py
├─ Cornus_Menu5.py
├─ Cornus_Logging.py
├─ Menu_Helper_Decorator.py
├─ Data_Hunter/
└─ MetaUnits/
```

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/Cornus-Data-Analysis.git
cd Cornus-Data-Analysis
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows
```bash
.venv\Scripts\activate
```

### macOS / Linux
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

Run the main program:

```bash
python Cornus_Main.py
```

Then follow the terminal menu to perform data preprocessing and exploratory data analysis tasks.

## Project Goals
This project was built to:

- practice data preprocessing and exploratory data analysis workflows
- improve Python project structuring skills
- build a reusable modular analysis system
- strengthen machine learning preparation skills before model training

## Future Improvements
Possible future extensions include:

- adding more data-cleaning strategies
- supporting more visualization options
- exporting analysis reports automatically
- improving database integration workflows
- adding example datasets and screenshots
- extending preprocessing support for larger datasets

## Author
**Zack**  
GitHub: [Jac-kai](https://github.com/Jac-kai)

## License
This project is for learning, portfolio, and demonstration purposes.
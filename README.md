# Sales Intelligence System

A data analysis project that turns raw e-commerce sales data into
business insights: revenue, product performance, and trends.

Built with Python, pandas, NumPy, and Matplotlib.

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/olistbr/brazilian-ecommerce)
(CC BY-NC-SA 4.0). About 100,000 orders from 2016 to 2018.
The data is not included in this repo; download it from Kaggle and place
the CSV files in `data/raw/`.

## Setup

    python -m venv .venv
    source .venv/Scripts/activate   # Windows (Git Bash)
    pip install -r requirements.txt

## Usage

    python src/inspect_data.py

## Project status

- [x] Milestone 1: Data discovery
- [ ] Milestone 2: Joining and cleaning
- [ ] Milestone 3: Metrics and analysis
- [ ] Milestone 4: Visualisations and recommendations

## Documentation

- [Data discovery notes](docs/data_discovery.md)
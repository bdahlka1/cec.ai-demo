# cec.ai-demo

A Streamlit-based internal tool for evaluating water/wastewater RFPs and generating CEC scorecards.

## Running the app

From the project root, install dependencies and start Streamlit:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to add a new folder

If you need to create a new directory for assets, models, or additional modules, use the built-in `mkdir` command from the project root:

```bash
# create a top-level folder named `data`
mkdir data

# create a nested folder structure (e.g., outputs/reports)
mkdir -p outputs/reports
```

When adding new folders, include a brief `README.md` inside the directory describing its purpose. If the folder should be tracked by git but remain empty, add a `.gitkeep` file so the directory is preserved in commits.

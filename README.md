<p align="center">
  <img src="quail.png" alt="Quail Logo" width="120"/>
</p>

# Quail

**Quail** is a lightweight framework for running data quality checks and tasks, inspired by workflow engines like Snakemake but tailored for data pipelines.

---

## 📦 Installation

### 1. Clone the repo
```bash
git clone https://github.com/your-username/quailtrail.git
cd quailtrail
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 3. Install the package (editable mode for development)
```bash
pip install -e .
```

Alternatively, build and install the wheel:
```bash
python -m pip install --upgrade build
python -m build
pip install dist/*.whl
```

---

## 🚀 Usage

### Run Quail via CLI
If you’ve defined a console script in `pyproject.toml`:
```bash
quail --help
```

### Run as a Python module
```bash
python -m quail
```

### Import in your code
Inside your own scripts or notebooks:
```python
from quail.core import Runner, qtask, qcheck

print("Hello from Quail!")
```

### Prototype example
In `prototype/main.py` you can try:
```python
from quail.core import some_func

if __name__ == "__main__":
    print("Prototype running")
    print(some_func())
```

Run it:
```bash
python prototype/main.py
```

---

## 🧪 Testing

We use **pytest** for tests:
```bash
pip install -e ".[dev]"
pytest -q
```

---

## 📜 License

MIT License © 2025 Your Name

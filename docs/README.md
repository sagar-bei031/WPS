# Wifi Positioning System (WiPS) Documentation

## Build

```bash
# Create Virtual Environment
python3 -m venv docenv
source ./venv/bin/acivate

# Install sphinx package and extensions
pip3 install sphinx sphinx_rtd_theme myst-parser sphinx-copybutton sphinx-tabs

# Build html
make html

# Run Webpages
cd build/html
python3 -m http.server # OR, firefox index.html
```

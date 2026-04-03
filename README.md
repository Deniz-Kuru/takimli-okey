# takimli-okey

Small Pygame prototype for Takimli Okey.

## Project Layout

```text
takimli-okey/
 main.py                 # thin launcher for convenience
 takimli_okey/
  __init__.py
  __main__.py           # supports: python -m takimli_okey
  constants.py          # app constants and colors
  card.py               # Card model + drawing logic
  game.py               # game loop and event handling
 requirements.txt
```

## Setup

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Either command works:

```powershell
python main.py
```

```powershell
python -m takimli_okey
```

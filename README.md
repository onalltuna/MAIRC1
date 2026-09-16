# Restaurant Dialog System

## Requirements

* Python 3
* uv — Python package manager. Check the [uv installation guide](https://docs.astral.sh/uv/#installation) for installation instructions.
* venv (included with standard Python installations)

## Create and activate the Virtual Enviroment

### macOS / Linux

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Windows

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## How to run


```bash
python main.py train --classifier <name>
python main.py test --classifier <name>
python main.py manual --classifier <name>
python main.py dialog --classifier <name>
```

```

#### `train`
Runs the training process for the selected classifier.

#### `test`
Runs the testing process for the selected classifier.

####  `manual`
Runs the manual utterance testing

#### `dialog`
Starts the restaurant dialog system using the selected classifier.

### Allowed classifier names

The valid choices are:

- `rulebased`
- `ml1`
- `ml2`

### Example usage

```bash
python main.py train --classifier rulebased
python main.py test --classifier ml1
python main.py dialog --classifier ml2
python main.py manual --classifier ml1
```

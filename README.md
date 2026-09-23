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
python main.py train --classifier <name> --grouped <y/n> [--bert <y/n>]
python main.py test --classifier <name> --grouped <y/n> [--bert <y/n>]
python main.py manual --classifier <name>--grouped <y/n> [--bert <y/n>]
python main.py dialog --classifier <name>
python main.py heldout --classifier <name> [--bert <y/n>]
```

```

#### `train`
Runs the training process for the selected classifier.

#### `test`
Runs the testing process for the selected classifier.

#### `dialog`
Starts the restaurant dialog system using the selected classifier.

#### `heldout`
Loads the held-out test set and applies testing on that file
For this command to be usable held-out data file needs to be stored in data/raw/dialog_acts_test.dat

### Allowed classifier names

- `rulebased`
- `ml1`
- `ml2`

### Allowed group options

- `y`
- `n`

### 'bert'
It is optional and default is `n`. To enable DistilBERT, set it to `y`.


### Example usage

```bash
python main.py train --classifier rulebased --grouped n
python main.py test --classifier ml1 --grouped y --bert y
python main.py dialog --classifier ml2 --grouped y --bert y
python main.py manual --classifier ml1
python main.py heldout --classifier rulebased
```

# Library Stickers Generator


## Requirements

- Linux system (Feodra/Ubuntu)
- Python 3.12+


## Usage

Navigate to the repository dir and run the following command:

```
source stickers.sh
```

It will run the app and install the required packages if needed.

To skip the steps ensuring packages, you can use a `--just-run` flag.

## Advanced configuration

Basic user input is collected via frontend app. If you wish to change other parameters, such as *font*, *placement*, *layout*, *database path*, please edit the `config.json` file. You can check out also "NOTE:LAYOUT" phrase in the source code.

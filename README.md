# BlokusAI
A showcase of multiple AI agents to master Blokus.

<p align="center">
    <img src="./docs/images/GUI_screenshot.png" alt="BlokusAI GUI Screenshot" width="400" height="400">
</p>

# Badges
- Link to [Article](https://danhchampion.github.io/BlokusAI/)
- Link to [Documentation](https://danhchampion.github.io/BlokusAI/docs.html) # TODO
- Link to [Demo](https://danhchampion.github.io/BlokusAI/demo.html) # TODO

### Create a Python virtual environment
```bash
python -m venv venv
```

### Activate the virtual environment
```bash
venv\Scripts\activate
```

### Install requirements
```bash
pip install -r requirements.txt
```

### Environment variables
Copy the `.env.template` file in the `configurations` folder to set up the environment variables.
```bash
copy src/configurations/.env.template src/configurations/.env
```

The `.env` file contains the following configurations:

### Global Configs
- `PYGAME_HIDE_SUPPORT_PROMPT=1`: Suppresses the PyGame support prompt message.
- `AI_LIST='["v1", "v3", "v1", "v2"]'`: Specifies the list of AI versions to be used in the simulations.
Available AI versions: `v1`, `v2`, `v3`

### CLI Configs
- `VERBOSITY=True`: Enables detailed logging in the command-line interface.
- `DRAW=False`: Disables drawing the game board in CLI mode.
- `DRAW_RESULTS=False`: Disables drawing the results in CLI mode.
- `STEP_BY_STEP=False`: Disables step-by-step execution in CLI mode.

### PyGame Configs
- `CELL_SIZE=20`: Sets the size of each cell in the PyGame grid.
- `FPS=20`: Sets the frames per second for the PyGame simulation.

### Experiment Configs
- `RECORD=True`: Enables recording of experiment results.
- `GAMES=100`: Specifies the number of games to be played during experiments.

Run the simulations
```bash
python run.py --phase CLI # Light-weight simulation
python run.py --phase GUI # See them play against each other
python run.py --phase GAME # Play against the AIs
python run.py --phase EXP # Incomplete, not working yet
python run.py --phase DQN # Incomplete, not working yet
```

### Game Controls
1. Drag & drop the piece on the the board
2. Whilst holding, press 'f' to flip piece horizontally
3. Whilst holding, press 'r' to rotate piece clockwise

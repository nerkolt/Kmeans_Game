# Clustering Visualizer Game (K‑Means / K‑Medoids / DBSCAN)

An interactive, visually stunning Python application that brings clustering algorithms to life! Watch data points dynamically form clusters with smooth animations, particle effects, and real-time visualizations.

Perfect for:
- Learning how clustering works (K‑Means / K‑Medoids / DBSCAN)
- Experimenting with different datasets and parameters
- Enjoying beautiful data visualizations
- Understanding machine learning concepts visually

![Clustering Visualizer Game](Assets/Start.png)

<a id="toc"></a>
## 📑 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Build a Windows EXE (Release)](#build-windows-exe)
- [Build a Windows Installer (Setup.exe)](#build-windows-installer)
- [Controls & Usage](#controls)
- [Debug Panel](#debug-panel)
- [Data Mining Features](#data-mining-features)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)

<a id="features"></a>
## Features

### Smooth Animations
- **Centroids glide smoothly** to new positions (no teleporting!)
- **Points transition gracefully** when changing clusters
- **Color blending** during cluster reassignment
- **Scale-pop effects** when points switch clusters

### Visual Effects
- ✨ **Glowing, pulsing halos** around centroids
- 💥 **Particle explosions** when points change clusters
- 🌠 **Trailing effects** behind moving points
- 🔗 **Faint connection lines** from points to centroids
- 🎯 **Smooth color transitions** for better visual feedback

### Modern Design
- Rich color palette (Coral, Turquoise, Pink, Peach, Lavender)
- Dark theme for better contrast and reduced eye strain
- Clean, intuitive user interface
- Real-time debug panel with performance metrics

### Interactive Controls
- Add points by clicking
- Manually move centroids
- Adjust number of clusters (K) on the fly
- Step-by-step or automatic iteration
- Custom point generation (1-500 points)
- Real-time performance monitoring

### Data Mining Features
- **Inertia/WCSS Calculation**: Real-time Within-Cluster Sum of Squares metric
- **Dataset Presets**: Pre-built datasets (Blobs, Moons, Circles, Random)
- **Convergence Graph**: Visualize inertia decreasing over iterations
- **Elbow Method**: Automatically test K values to find optimal cluster count
- **Voronoi / Decision Regions**: Visualize cluster regions in the plane
- **DBSCAN (Density-Based Clustering)**: Cluster non-linear shapes and detect **noise/outliers** (no K required)
- **Battle Mode (A/B)**: Compare algorithms side-by-side on the same data (K-Means / K-Medoids / DBSCAN)
- **CSV Import/Export**: Load real datasets and export clustered results
- **Advanced Statistics**: Detailed cluster quality metrics (compactness, separation, variance)
- **Cluster Quality Metrics**: Per-cluster analysis with color-coded visualization

<a id="requirements"></a>
## Requirements

- **Python 3.10+** (recommended; tested on modern Windows Python)
- **Pygame** (for graphics and interaction)

<a id="installation"></a>
## Installation

### Step 1: Clone or Download the Repository

```bash
# Using Git
git clone https://github.com/nerkolt/Clustering_Visualizer_Game.git
cd Clustering_Visualizer_Game

# Or download and extract the ZIP file
```

### Step 2: Install Python Dependencies

Make sure you have Python installed. Then install Pygame:

```bash
# Using pip
pip install pygame

# Or if you're using pip3
pip3 install pygame

# On some systems, you might need:
python -m pip install pygame
```

#### Recommended (one command)

```bash
python -m pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Check Python version (should be 3.7+)
python --version

# Check Pygame installation
python -c "import pygame; print(pygame.version.ver)"
```

<a id="how-to-run"></a>
## How to Run

Navigate to the project directory and run the main script:

```bash
# From the project root directory
python Scripts/Kmeans_Game_Debug.py

# Or if you're in the Scripts folder
cd Scripts
python Kmeans_Game_Debug.py
```

**Note:** `Scripts/Kmeans_Game_Debug.py` is the entry point. Most logic lives in the modular files under `Scripts/` (algorithms, scenes, datasets, rendering, CSV I/O).

<a id="build-windows-exe"></a>
## Build a Windows EXE (Release)

You can create a standalone Windows build using **PyInstaller**.

### Option A (recommended): one-folder build

From the project root:

```bash
tools/release/build_exe.bat onedir
```

Output: `dist/ClusteringVisualizerGame/ClusteringVisualizerGame.exe`

### Option B: single-file build

```bash
tools/release/build_exe.bat onefile
```

Output: `dist/ClusteringVisualizerGame.exe`

### Notes / troubleshooting

- The game uses **Tkinter file dialogs** for CSV import/export; in the EXE build the dialogs will open in your current folder (better UX).
- If Windows Defender flags the EXE, prefer the **one-folder** build (it’s usually less problematic than one-file).

<a id="build-windows-installer"></a>
## Build a Windows Installer (Setup.exe)

If you want a real installer for GitHub Releases (Start Menu shortcut + optional Desktop shortcut + uninstaller), use **Inno Setup**.

### Install Inno Setup

- Option 1: installer from the official Inno Setup website
- Option 2 (recommended): Chocolatey

```powershell
choco install innosetup -y
```

### Build installer (uses your icon + publisher)

```bat
tools/release/build_exe.bat installer
```

Output:
- `dist-installer/ClusteringVisualizerGame-Setup-<version>.exe`

Details:
- **Publisher**: Nour Ltaief
- **Icon**: `Assets/logo.png` converted to `.ico` during build

### GitHub Actions (automatic Release uploads)

This repo includes a workflow that builds the EXE + installer automatically when you push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow will attach these files to the GitHub Release:
- `dist-installer/ClusteringVisualizerGame-Setup-<version>.exe`
- `dist/ClusteringVisualizerGame/ClusteringVisualizerGame.exe`

<a id="controls"></a>
## Controls & Usage

### Keyboard Controls

#### Basic Controls
| Key | Action |
|-----|--------|
| `SPACE` | Run **one step** of the selected algorithm |
| `A` | Toggle **auto-iteration** (runs until convergence) |
| `R` | **Reset** with new random centroids |
| `P` | Open dialog to set number of points (1-500) |
| `K` | Open dialog to set number of clusters (1-10) |
| `↑` / `↓` | Quickly increase/decrease K |
| `D` | Toggle debug panel (top-right) |
| `T` | Toggle **Learning mode** overlay (tutorial/explanations) |
| `TAB` | Next tutorial page (when Learning mode is on) |
| `SHIFT` + `TAB` | Previous tutorial page |
| `C` | Clear all points |
| `5` | Select **K-Means** |
| `6` | Select **K-Medoids** |
| `7` | Select **DBSCAN** |
| `ESC` | Cancel input dialog / Close window |
| `ENTER` | Confirm input in dialog |

#### Data Mining & Analysis Controls
| Key | Action |
|-----|--------|
| `S` | Toggle **advanced stats panel** (cluster quality metrics) |
| `G` | Toggle **convergence graph** (inertia over iterations) |
| `E` | Run **elbow method** (find optimal K) |
| `V` | Toggle **Voronoi / decision regions** |
| `B` | Toggle **battle mode** (A/B split-screen comparison) |
| `I` | **Import CSV** (x,y) |
| `O` | **Export CSV** (x,y + cluster labels; exports both in battle mode) |
| `1` | Generate **Blobs** dataset (well-separated clusters) |
| `2` | Generate **Moons** dataset (crescent-shaped, non-linear) |
| `3` | Generate **Circles** dataset (concentric rings) |
| `4` | Generate **Random** dataset (uniform distribution) |

### Mouse Controls

| Action | Function |
|--------|----------|
| **Left Click** | Add a new data point at mouse position |
| **Right Click** | Move nearest centroid to mouse position |

### Input Dialog System

When you press `P` or `K`:
1. A dialog box appears
2. Type your desired number (digits only)
3. Press `ENTER` to confirm
4. Press `ESC` to cancel

**Example:** Press `P`, type `200`, hit `ENTER` → instantly generate 200 random points!

<a id="debug-panel"></a>
## Debug Panel

Press `D` to toggle the debug overlay (top-right corner). It displays:

- **FPS**: Real-time frame rate
- **Points**: Total number of data points
- **Clusters (K)**: Current number of clusters
- **Iterations**: Number of algorithm iterations performed
- **Particles**: Active particle effects count
- **Converged**: Whether the algorithm has converged
- **Inertia (WCSS)**: Within-Cluster Sum of Squares (lower is better)
- **DBSCAN eps/min_samples**: DBSCAN density parameters (when using DBSCAN)
- **Dataset**: Current dataset type (random/blobs/moons/circles)
- **Cluster Sizes**: Point count per cluster (color-coded)

The panel automatically resizes based on the number of clusters!

<a id="data-mining-features"></a>
## Data Mining Features

### Inertia (WCSS) Metric

**Inertia** (Within-Cluster Sum of Squares) measures how tightly points are clustered around their centroids. Lower inertia means better clustering!

- Displayed in real-time in the debug panel
- Tracked over iterations for the convergence graph
- Used in the elbow method to find optimal K

### Dataset Presets

Test K-Means on different data distributions:

- **Blobs** (`1`): Well-separated Gaussian clusters - perfect for K-Means
- **Moons** (`2`): Two crescent-shaped clusters - challenges K-Means (non-linear)
- **Circles** (`3`): Concentric ring clusters - another non-linear challenge
- **Random** (`4`): Uniform random distribution - baseline test

**Tip**: Try the Moons dataset with K=2 to see how K-Means struggles with non-linear data!

### Convergence Graph

Press `G` to toggle the convergence graph (top-left corner).

- Shows **inertia decreasing** over iterations
- Visualizes algorithm progress in real-time
- Helps identify when convergence is reached
- Updates automatically as the algorithm runs

**What to look for**: A downward trend that flattens out indicates convergence.

### Elbow Method

Press `E` to run the elbow method analysis (bottom-right corner).

The elbow method helps you find the **optimal number of clusters (K)** by:
1. Testing K values from 1 to 10
2. Calculating inertia for each K
3. Plotting K vs Inertia
4. Finding the "elbow" point where adding more clusters doesn't help much

**How to read it**: Look for the point where the line bends sharply (the "elbow"). That's usually the optimal K!

**Note**: The elbow method may take a few seconds to compute as it runs the algorithm for each K value.

### Advanced Statistics Panel

Press `S` to toggle the advanced statistics panel (left side).

Displays comprehensive cluster quality metrics:

#### Overall Metrics
- **Inertia (WCSS)**: Total within-cluster sum of squares
- **Min Separation**: Distance between closest centroids

#### Per-Cluster Metrics
For each cluster (color-coded):
- **Size**: Number of points in the cluster
- **Avg Distance**: Average distance from points to centroid
- **Compactness**: Measure of how tightly packed the cluster is (higher is better)

**Use cases**:
- Compare cluster quality across different K values
- Identify unbalanced clusters
- Analyze cluster compactness and separation
- Validate clustering results

<a id="project-structure"></a>
## Project Structure

```
Kmeans_Game/
│
├── Scripts/
│   ├── Kmeans_Game_Debug.py          # Entry point (launches the app)
│   ├── app.py                        # Game loop + scene management
│   ├── config.py                     # Window + UI layout + colors
│   ├── algorithms.py                 # K-Means / K-Medoids / DBSCAN logic
│   ├── datasets.py                   # Random/Blobs/Moons/Circles generators
│   ├── entities.py                   # Point/Centroid/ParticleEffect classes
│   ├── voronoi.py                    # Voronoi/decision region rendering
│   ├── csv_io.py                     # CSV import/export + file dialogs
│   ├── scenes/
│   │   ├── menu_scene.py             # Main menu UI
│   │   └── game_scene.py             # Main game view + overlays
│
├── Assets/                           # README screenshots + app logo
│   ├── logo.png
│   ├── Start.png
│   ├── Auto Mode.png
│   └── 50Points.png
│
├── tools/
│   └── make_icon.py                  # Converts Assets/logo.png -> build/logo.ico
├── installer.iss                     # Inno Setup installer script (publisher + icon)
├── tools/release/
│   ├── build_exe.bat                 # Windows build helper (PyInstaller + installer)
│   └── build_exe.ps1                 # PowerShell build helper
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── Tutorial.md                       # Detailed tutorial/controls
└── Visualisation.md                  # Visualization guide
```

## Mini‑project checklist (3DNI Data Mining)

This repository is structured to satisfy typical mini‑project constraints (algorithm + visualization + report/demo). Your course PDF/statement is not included in this repo.

- **At least one data mining algorithm**: K‑Means clustering (+ inertia/WCSS, elbow method, convergence graph).
- **Clear README**: install, dependencies, commands, usage, screenshots.
- **Original work**: interactive “game” visualization + added analysis tools (datasets, metrics, elbow method).

Submission note: follow your instructor’s submission instructions (email / LMS / GitHub link), since requirements vary by class.

## 🎓 Understanding the Algorithms

### K‑Means (hard clustering)

K‑Means works in two main steps:

1. **Assignment**: Each point is assigned to the nearest centroid (based on Euclidean distance)
2. **Update**: Centroids move to the mean position of all points in their cluster

These steps repeat until:
- No points change clusters (convergence), or
- Maximum iterations are reached

**Watch it in action:**
- Points change color when reassigned to a different cluster
- Centroids smoothly move to the center of their clusters
- The algorithm converges when no more changes occur

### K‑Medoids (robust alternative)

K‑Medoids is similar to K‑Means, but uses **medoids** (actual data points) instead of the mean. It is often more robust to outliers.

### DBSCAN (density-based)

DBSCAN groups points by density using:
- `eps`: neighborhood radius (pixels)
- `min_samples`: points needed to form a dense region

Points that don’t belong to any dense region are labeled as **noise/outliers** (`-1`).

### Key Concepts (used throughout the app)

**Inertia (WCSS)**: Measures cluster quality by summing squared distances from points to their centroids. Lower inertia = tighter, better clusters.

**Convergence**: The algorithm stops when no points change clusters between iterations, meaning the clusters are stable.

**Optimal K**: Finding the right number of clusters is crucial. Too few = oversimplified, too many = overfitted. Use the elbow method (`E`) to help!

**Limitations**: K-Means assumes clusters are spherical and similar in size. Try the Moons (`2`) or Circles (`3`) datasets to see where it struggles.

<a id="troubleshooting"></a>
## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'pygame'"**
```bash
# Solution: Install pygame
pip install pygame
```

**"Python not found" or "python: command not found"**
```bash
# Try using python3 instead
python3 Scripts/Kmeans_Game_Debug.py

# Or check if Python is in your PATH
```

**Low FPS or performance issues**
- The code is optimized, but with 500+ points you may see some slowdown
- Try reducing the number of points (press `P` and enter a smaller number)
- Close other applications to free up system resources

**Window doesn't appear**
- Make sure you're running the correct file: `Kmeans_Game_Debug.py`
- Check for error messages in the terminal
- Verify pygame is installed correctly: `python -c "import pygame"`

<a id="customization"></a>
## Customization

You can easily customize the game in the modular files:

- **Window size / UI layout / palette**: `Scripts/config.py`
  - `WIDTH`, `HEIGHT`, `UI_PANEL_HEIGHT`, `COLORS`, `BG_COLOR`, etc.
- **Algorithms**: `Scripts/algorithms.py`
  - K‑Means / K‑Medoids / DBSCAN implementation details
- **Datasets**: `Scripts/datasets.py`
  - Random spacing, blobs/moons/circles generation
- **Visuals & overlays**: `Scripts/scenes/game_scene.py` and `Scripts/entities.py`
  - Connection lines, trails, particles, bottom HUD, tutorial overlay
- **Menu options**: `Scripts/scenes/menu_scene.py`
  - What shows up in the menu and the default values

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## Contact & Support

For questions, issues, or suggestions, please open an issue on the GitHub repository.

---

## Quick Start Guide

1. **Run the application**: `python Scripts/Kmeans_Game_Debug.py`
2. **Try a dataset**: Press `1` for blobs, `2` for moons, `3` for circles
3. **Watch it cluster**: Press `A` for auto-mode or `SPACE` to step through
4. **Analyze results**: 
   - Press `G` to see the convergence graph
   - Press `S` to view detailed statistics
   - Press `E` to find optimal K with elbow method
5. **Experiment**: Change K with `↑`/`↓` or `K`, try different datasets, add your own points!

## Pro Tips

- **Start with Blobs** (`1`) to see K-Means at its best
- **Try Moons** (`2`) with K=2 to see K-Means limitations with non-linear data
- **Use Elbow Method** (`E`) before manually choosing K
- **Watch the Convergence Graph** (`G`) to understand algorithm progress
- **Check Stats Panel** (`S`) to compare cluster quality
- **Lower Inertia = Better Clustering** - watch it decrease as clusters improve!

---

**Enjoy exploring K-Means clustering!**

*Press `A` to watch the magic happen automatically, or use `SPACE` to step through each iteration manually.*

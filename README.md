# K-Means Clustering Visualizer 🎮

An interactive, visually stunning Python application that brings the K-Means clustering algorithm to life! Watch data points dynamically form clusters with smooth animations, particle effects, and real-time visualizations.

Perfect for:
- 🎓 Learning how K-Means clustering works
- 🧪 Experimenting with different datasets and parameters
- 🎨 Enjoying beautiful data visualizations
- 📊 Understanding machine learning concepts visually

![K-Means Game](Assets/Start.png)

## ✨ Features

### 🎬 Smooth Animations
- **Centroids glide smoothly** to new positions (no teleporting!)
- **Points transition gracefully** when changing clusters
- **Color blending** during cluster reassignment
- **Scale-pop effects** when points switch clusters

### 🌟 Visual Effects
- ✨ **Glowing, pulsing halos** around centroids
- 💥 **Particle explosions** when points change clusters
- 🌠 **Trailing effects** behind moving points
- 🔗 **Faint connection lines** from points to centroids
- 🎯 **Smooth color transitions** for better visual feedback

### 🎨 Modern Design
- Rich color palette (Coral, Turquoise, Pink, Peach, Lavender)
- Dark theme for better contrast and reduced eye strain
- Clean, intuitive user interface
- Real-time debug panel with performance metrics

### 🎮 Interactive Controls
- Add points by clicking
- Manually move centroids
- Adjust number of clusters (K) on the fly
- Step-by-step or automatic iteration
- Custom point generation (1-500 points)
- Real-time performance monitoring

## 📋 Requirements

- **Python 3.7+**
- **Pygame** (for graphics and interaction)

## 🚀 Installation

### Step 1: Clone or Download the Repository

```bash
# Using Git
git clone https://github.com/yourusername/Kmeans_Game.git
cd Kmeans_Game

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

### Step 3: Verify Installation

```bash
# Check Python version (should be 3.7+)
python --version

# Check Pygame installation
python -c "import pygame; print(pygame.version.ver)"
```

## 🎯 How to Run

Navigate to the project directory and run the main script:

```bash
# From the project root directory
python Scripts/Kmeans_Game_Debug.py

# Or if you're in the Scripts folder
cd Scripts
python Kmeans_Game_Debug.py
```

**Note:** The main file is `Kmeans_Game_Debug.py` which includes all the latest features and optimizations.

## 🎮 Controls & Usage

### Keyboard Controls

| Key | Action |
|-----|--------|
| `SPACE` | Run **one step** of K-Means algorithm |
| `A` | Toggle **auto-iteration** (runs until convergence) |
| `R` | **Reset** with new random centroids |
| `P` | Open dialog to set number of points (1-500) |
| `K` | Open dialog to set number of clusters (1-10) |
| `↑` / `↓` | Quickly increase/decrease K |
| `D` | Toggle debug panel (top-right) |
| `C` | Clear all points |
| `ESC` | Cancel input dialog / Close window |
| `ENTER` | Confirm input in dialog |

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

## 🔧 Debug Panel

Press `D` to toggle the debug overlay (top-right corner). It displays:

- **FPS**: Real-time frame rate
- **Points**: Total number of data points
- **Clusters (K)**: Current number of clusters
- **Iterations**: Number of algorithm iterations performed
- **Particles**: Active particle effects count
- **Converged**: Whether the algorithm has converged
- **Cluster Sizes**: Point count per cluster (color-coded)

The panel automatically resizes based on the number of clusters!

## 📁 Project Structure

```
Kmeans_Game/
│
├── Scripts/
│   ├── Kmeans_Game_Debug.py      # Main file (recommended - includes all features)
│   ├── Kmeans_Game.py            # Basic version
│   └── Kmeans_Game_Optimization.py  # Optimized version
│
├── Assets/
│   ├── Start.png                 # Screenshot
│   ├── Auto Mode.png             # Screenshot
│   └── 50Points.png              # Screenshot
│
├── README.md                     # This file
├── Tutorial.md                   # Detailed tutorial
└── Visualisation.md              # Visualization guide
```

## 🎓 Understanding K-Means

The K-Means algorithm works in two main steps:

1. **Assignment**: Each point is assigned to the nearest centroid (based on Euclidean distance)
2. **Update**: Centroids move to the mean position of all points in their cluster

These steps repeat until:
- No points change clusters (convergence), or
- Maximum iterations are reached

**Watch the algorithm in action:**
- Points change color when reassigned to a different cluster
- Centroids smoothly move to the center of their clusters
- The algorithm converges when no more changes occur

## 🐛 Troubleshooting

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

## 🎨 Customization

You can easily customize the game by editing `Kmeans_Game_Debug.py`:

- **Colors**: Modify the `COLORS` array (lines 15-21)
- **Window Size**: Change `WIDTH` and `HEIGHT` (line 9)
- **FPS**: Adjust `FPS` constant (line 10)
- **Animation Speed**: Modify interpolation values in `Point.update()` and `Centroid.update()`

## 📝 License

This project is open source and available for educational purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📧 Contact & Support

For questions, issues, or suggestions, please open an issue on the GitHub repository.

---

**Enjoy exploring K-Means clustering! 🎉**

*Press `A` to watch the magic happen automatically, or use `SPACE` to step through each iteration manually.*

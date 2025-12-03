# KMeans Game – Interactive K-Means Clustering Visualizer

An engaging, beautiful, and educational Python game that lets you **play with the famous K-Means clustering algorithm in real-time**! Watch clusters form, centroids dance, and points dramatically switch allegiances with smooth animations and satisfying visual effects.

Perfect for learning how K-Means works, experimenting with different datasets, or just enjoying mesmerizing data visualizations.

![demo preview](https://via.placeholder.com/800x450.png?text=KMeans+Game+Demo+Coming+Soon)  
*(Replace with your own screenshot or GIF)*

## ✨ Features & Visual Polish

### Smooth & Satisfying Animations
- Centroids **glide smoothly** to their new positions (no more teleporting!)
- Points **gracefully transition** between clusters with easing
- Colors **blend beautifully** during reassignment

### Eye-Candy Overload
- ✨ **Glowing, pulsing halos** around centroids
- 💥 **Particle explosions** when a point changes cluster
- 🌠 **Trailing effects** behind moving points
- 🎯 **Scale-pop animation** on cluster switch
- Subtle **connection lines** from points to their centroid

### Gorgeous Modern Aesthetics
- Rich color palette: Coral, Turquoise, Pink, Peach, Lavender, and more
- Dark background for maximum contrast and vibrancy
- Smooth color transitions instead of harsh changes
- White highlights on points for added depth

### Clean User Interface
- Sleek bottom control panel
- Clear status indicator: `CONVERGED ✓` | `RUNNING` | `PAUSED` | `AUTO`
- Elegant typography and spacing

## 🎮 Controls

| Key          | Action                                      |
|--------------|---------------------------------------------|
| `Click`      | Add a new data point at mouse position      |
| `Space`      | Pause / Resume the algorithm                |
| `A`          | Run automatically until convergence         |
| `S`          | Step through one iteration manually         |
| `C`          | Clear all points                            |
| `R`          | Randomly generate points (default behavior) |
| `P`          | Open dialog → Set custom number of points (1–500) |
| `K`          | Open dialog → Set number of clusters (1–10) |
| `↑` / `↓`    | Quickly increase/decrease K                 |
| `D`          | Toggle debug overlay (top-right)            |
| `ESC`        | Cancel input dialog                         |
| `Enter`      | Confirm number in dialog                    |

### 💡 Input Dialog (P or K)
1. Press `P` or `K`
2. Type your desired number
3. Press `Enter` → Apply
4. Press `ESC` → Cancel

**Pro tip:** Press `P`, type `300`, hit Enter → instantly generate 300 points!

## 🔧 Debug Overlay (Press D)

Toggles a real-time information panel showing:

- FPS (frames per second)
- Total points
- Current K (number of clusters)
- Iteration count
- Active particle effects
- Convergence status
- Per-cluster point counts (color-coded!)

Great for analyzing performance and understanding cluster balance.

## 🚀 How to Run

```bash
# Clone or download the repository
git clone https://github.com/yourusername/kmeans_game.git
cd kmeans_game

# Install dependencies
pip install pygame numpy
```
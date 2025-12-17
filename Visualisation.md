# Visualisation Notes (Data Mining View)

This document focuses on what the visual elements mean from a **data mining** perspective.

## Screenshots

- Start screen: `Assets/Start.png`
- Auto mode example: `Assets/Auto Mode.png`
- 50 points example: `Assets/50Points.png`

## Visual legend

- **Small colored points**: data samples
  - Color = assigned cluster
  - Animated color blending = cluster reassignment over time
- **Large glowing circles**: centroids
  - Move to the mean of assigned points each iteration
- **Faint lines**: point → assigned centroid (helps you see assignments)
- **Trails**: recent point motion / animation path (purely visual)

## Data mining overlays

### Debug overlay (`D`)

Shows runtime information (FPS, number of points, K, iterations, cluster sizes) plus:
- **Inertia (WCSS)**: lower usually means better cluster compactness
- **Dataset type**: random/blobs/moons/circles

### Convergence graph (`G`)

A mini plot of **inertia over iterations**:
- Downward trend → clustering improving
- Flat line → convergence / no significant improvement

### Advanced stats (`S`)

Adds higher-signal quality indicators:
- **Min separation** (closest centroid-to-centroid distance)
- Per-cluster **avg distance**, **variance/compactness**, and **size**

### Elbow method (`E`)

Runs multiple clustering trials for \(K=1..10\), then plots **K vs inertia**:
- The “elbow” (big improvement slows down) suggests a good K choice

### Voronoi / decision regions (`V`)

Shows an approximate **decision map**: each cell is colored by the nearest centroid/medoid.
- Makes cluster “territories” visible
- Helps explain why points switch clusters near boundaries

### Battle mode (A/B split screen) (`B`)

Splits the screen into two views on the **same dataset**:
- **A** uses your selected algorithm
- **B** uses the other algorithm (K‑Means vs K‑Medoids)

Use it to compare:
- **Convergence speed** (iterations)
- **Final inertia**
- Behavior on non-linear datasets (Moons/Circles)

### CSV import/export (`I` / `O`)

- **Import (`I`)**: load real 2D data from a CSV file with columns `x,y` (header optional)
- **Export (`O`)**: save `x,y` and cluster labels (in battle mode exports both A and B labels)

## Why some datasets “break” K‑Means

- **Blobs**: works well because clusters are roughly spherical.
- **Moons / Circles**: K‑Means struggles because it uses distance-to-centroid and prefers spherical partitions.



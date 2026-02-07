<<<<<<< HEAD
# 🛸 MineGuard.ai: Autonomous Geospatial Forensics
> 
## 📌 Overview
Illegal mining is a global crisis, causing $12B+ in economic losses and devastating environmental damage. Traditional monitoring is slow, dangerous, and easily evaded. 

**MineGuard.ai** turns the tide by providing an autonomous, high-confidence forensic pipeline. By fusing optical, radar, and topographical data, we detect illegal encroachments and calculate stolen volumes in real-time, providing authorities with "court-ready" digital evidence.

## 🚀 The "Quad-Lock" Innovation
Most satellite monitoring relies only on visual (optical) data, which fails under clouds or clever camouflage. MineGuard uses a proprietary **Quad-Lock** verification system:

1.  **Lock 1: Optical Signature (Sentinel-2)** - Detects bare-soil indices (NDBI) and vegetation loss.
2.  **Lock 2: Radar Pulse (Sentinel-1 SAR)** - Pierces through clouds and detect surface roughness changes typical of fresh excavation.
3.  **Lock 3: Topographical Forensics (Copernicus DEM)** - Compares regional focal means against actual DEM to identify physical pits (> 2m depth).
4.  **Lock 4: Temporal Delta (dNDVI)** - Analyzes year-over-year vegetation health to filter out natural rocky terrain from active clearing.

## ✨ Key Features
-   **Immersive 3D Modeling**: Generates volumetric meshes of mining pits for tactical inspection.
-   **Historical Timeline Slider**: Visual evidence of site progress (Current vs 3-6 months ago).
-   **Precision Quantics**: Automatic calculation of Area (m²), Stolen Volume (m³), and Logistics Load (Total Truckloads).
-   **Automated Alerting**: Immediate SMTP-triggered warnings for detections exceeding risk thresholds.
-   **Enterprise Portal**: Sleek, glassmorphic "Command Center" UI designed for professional mission control.

## ⚙️ Additional Capabilities
-   **Multi-Format Data Ingest**: Seamless support for **zipped ESRI Shapefiles, KML, and GeoJSON**, allowing immediate integration with existing legacy government data.
-   **Forensic PDF Generation**: Automatically generates detailed technical reports including timestamped evidence, metrics summaries, and site coordinates for official use.
-   **Encrypted Pipeline**: Secure data handling with UUID-based job tracking and PostGIS spatial indexing for fast, encrypted retrieval.
-   **Custom Temporal Windows**: Users can select custom `Start` and `End` dates for change detection, enabling analysis of specific drought periods or suspicious windows.

## 🧩 Technical Edge
-   **Cloud-Piercing SAR**: Unlike visual drones, our **Sentinel-1 VV/VH Radar** integration allows surveillance through heavy cloud cover, smoke, or nighttime conditions.
-   **Focal-Mean Smoothing**: We utilize a custom spatial smoothing algorithm on the **Copernicus GLO30 DEM** to reconstruct hypothetical "pre-mining" terrain for high-accuracy volume calculation.
-   **Microservice Architecture**: Fully containerized using **Docker Compose**, separating the heavy-weight GEE engine from the responsive React UI for maximum stability.
-   **Frontend**: React 19, Tailwind CSS v4, Lucide Icons, Framer Motion.
-   **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL (PostGIS).
-   **Intelligence**: Google Earth Engine (GEE), Geemap, NumPy.
-   **DevOps**: Docker, Nginx, Docker-Compose.

## 🚦 Getting Started (Hackathon Rapid Deploy)

### 1. Requirements
-   Docker Desktop installed.
-   Earth Engine Service Account Key (`gee-key.json`) placed in `./backend/`.

### 2. Magic Command
```bash
docker-compose up -d --build
```

### 3. Access
-   **The Portal**: `http://localhost:3000`
-   **The Engine (API)**: `http://localhost:8000/docs`

## � Business Impact & Sustainability
-   **Environmental Protection**: Real-time detection stops deforestation before it scales.
-   **Revenue Recovery**: Enables governments to tax/fine unauthorized extraction based on precise volumetric data.
-   **Scalability**: Global coverage with zero on-ground hardware required.

---
| *Orbital Intelligence for Global Sustainability*
=======
# Mineguard
>>>>>>> 31a6fdef232630fa7d6bea461e1326281b3c4cf7

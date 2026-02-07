import ee
import geemap
import os
from google.oauth2 import service_account

# Import Helpers (Keep your existing error handling)
try:
    from phase2_tin_viz import generate_tin_visualization
    from report_generator import generate_pdf_report
except ImportError:
    generate_tin_visualization = None
    generate_pdf_report = None

# --- CONFIGURATION (Updated with Script 2 Values) ---
PROJECT_ID = 'minesector' # Keep your project ID
KEY_PATH = "gee-key.json"
DEFAULT_START = '2024-01-01'
DEFAULT_END = '2024-04-30'

# Updated Sensitivity Parameters (Optical + Depth Only)
CLOUD_THRESHOLD = 20
OPTICAL_THRESHOLD = 0.07  # Increased from 0.05 to 0.07 (Stricter)
NDVI_THRESHOLD = 0.25     # Kept for vegetation filtering
MIN_DEPTH_THRESHOLD = 2.0   
DEM_SOURCE = 'COPERNICUS/DEM/GLO30' 

# Global flag to track initialization status
_ee_initialized = False

def initialize_earth_engine():
    """
    Initialize Earth Engine with explicit service account authentication.
    This is more robust than relying on auto-detection.
    """
    global _ee_initialized
    
    if _ee_initialized:
        print("✅ Earth Engine already initialized")
        return True
    
    print("🌍 Initializing Earth Engine...")
    
    # Method 1: Explicit service account with google.oauth2
    if os.path.exists(KEY_PATH):
        try:
            print(f"📁 Loading service account from: {KEY_PATH}")
            # Use google.oauth2.service_account for more reliable authentication
            credentials = service_account.Credentials.from_service_account_file(
                KEY_PATH,
                scopes=['https://www.googleapis.com/auth/earthengine']
            )
            ee.Initialize(credentials=credentials, project=PROJECT_ID)
            print(f"✅ Earth Engine initialized with service account for project: {PROJECT_ID}")
            _ee_initialized = True
            return True
        except Exception as e:
            print(f"⚠️  Explicit service account auth failed: {e}")
    else:
        print(f"⚠️  Service account key not found at: {KEY_PATH}")
    
    # Method 2: Try EE's ServiceAccountCredentials (legacy method)
    if os.path.exists(KEY_PATH):
        try:
            print("📁 Trying Earth Engine's ServiceAccountCredentials...")
            service_account_email = "mineguard-sa@minesector.iam.gserviceaccount.com"
            credentials = ee.ServiceAccountCredentials(service_account_email, KEY_PATH)
            ee.Initialize(credentials=credentials, project=PROJECT_ID)
            print(f"✅ Earth Engine initialized with EE ServiceAccountCredentials")
            _ee_initialized = True
            return True
        except Exception as e:
            print(f"⚠️  EE ServiceAccountCredentials failed: {e}")
    
    # Method 3: Try environment variable (GOOGLE_APPLICATION_CREDENTIALS)
    try:
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("📁 Trying GOOGLE_APPLICATION_CREDENTIALS environment variable...")
            ee.Initialize(project=PROJECT_ID)
            print(f"✅ Earth Engine initialized with application default credentials")
            _ee_initialized = True
            return True
    except Exception as e:
        print(f"⚠️  Application default credentials failed: {e}")
    
    # Method 4: Try mounted credentials from host (~/.config/earthengine)
    try:
        cred_path = os.path.expanduser("~/.config/earthengine/credentials")
        if os.path.exists(cred_path):
            print(f"📁 Found mounted credentials at: {cred_path}")
            # Let Earth Engine auto-detect the credentials
            ee.Initialize(project=PROJECT_ID)
            print(f"✅ Earth Engine initialized with mounted host credentials")
            _ee_initialized = True
            return True
        else:
            print(f"⚠️  No credentials file found at: {cred_path}")
    except Exception as e:
        print(f"⚠️  Mounted credentials failed: {e}")
    
    # Method 5: Try without project ID (last resort)
    try:
        print("📁 Trying initialization without project ID...")
        ee.Initialize()
        print(f"✅ Earth Engine initialized (no project specified)")
        _ee_initialized = True
        return True
    except Exception as e:
        print(f"⚠️  Initialization without project failed: {e}")
    
    # All methods failed
    print("❌ All authentication methods failed!")
    print("📋 Troubleshooting steps:")
    print("   1. Register project at: https://code.earthengine.google.com/register")
    print("   2. Enable Earth Engine API in Cloud Console")
    print("   3. Grant 'Earth Engine Resource Admin' role to service account")
    print("   4. Or run 'earthengine authenticate' on host machine")
    _ee_initialized = False
    raise Exception("Failed to initialize Earth Engine. Please check credentials and project registration.")
    
    return False

def run_unified_detection(lease_geojson=None, filename="Manual_Input", output_dir="output", start_date=DEFAULT_START, end_date=DEFAULT_END):
    # Ensure Earth Engine is initialized before proceeding
    if not _ee_initialized:
        try:
            initialize_earth_engine()
        except Exception as e:
            raise Exception(f"Cannot run detection: Earth Engine initialization failed - {e}")
    
    os.makedirs(output_dir, exist_ok=True)
    lid_elevation = 0.0
    
    # --- A. INPUT GEOMETRY ---
    if lease_geojson:
        try:
            roi = ee.Geometry(lease_geojson)
        except:
            roi = ee.Geometry.Polygon([[86.40, 23.70], [86.45, 23.70], [86.45, 23.75], [86.40, 23.75]])
    else:
        roi = ee.Geometry.Polygon([[86.40, 23.70], [86.45, 23.70], [86.45, 23.75], [86.40, 23.75]])

    search_zone = roi.buffer(2000) # Keep buffer to find encroachments

    # --- B. SENSOR DETECTION (IMPROVED LOGIC) ---
    print(f"🚀 Step 1: Multi-Sensor Scan ({start_date} to {end_date})...")
    
    # 1. OPTICAL (NDBI + NDVI Check)
    # We keep NDVI check from Script 1 because NDBI alone confuses urban areas/fallow land with mines.
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterBounds(roi)
          .filterDate(start_date, end_date)
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD_THRESHOLD))
          .select(["B4", "B3", "B2", "B8", "B11"]))
    
    s2_image = s2.median().clip(search_zone)
    ndbi = s2_image.normalizedDifference(["B11", "B8"]).rename("NDBI")
    ndvi = s2_image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    
    # Logic: High NDBI (Bare Soil) AND Low NDVI (No Vegetation)
    optical_mask = ndbi.gt(OPTICAL_THRESHOLD).And(ndvi.lt(NDVI_THRESHOLD))

    # 2. DEPTH (Local vs Regional Elevation)
    # Script 2 Logic: Focal Mean (Smoothed) - Raw DEM
    dem = ee.ImageCollection(DEM_SOURCE).select("DEM").mosaic().clip(search_zone)
    
    # Calculate "Smoothed" surface (Hypothetical pre-mining surface)
    smooth_surface = dem.focal_mean(radius=250, units="meters")
    
    # Depth = Smoothed Surface - Actual Ground
    raw_depth = smooth_surface.subtract(dem).rename("depth")
    depth_only_mask = raw_depth.gt(MIN_DEPTH_THRESHOLD)

   # --- C. TRIPLE LOCK FUSION & CLASSIFICATION ---
    print("🔒 Applying Triple Lock Verification...")

# Lock 1: Optical Signature (Is it bare soil/disturbed?)
# ndbi.gt(OPTICAL_THRESHOLD)

# Lock 2: Biological Signature (Is it devoid of vegetation?)
# ndvi.lt(NDVI_THRESHOLD)

# Lock 3: Topographical Signature (Is there a physical pit?)
# depth_only_mask (raw_depth > MIN_DEPTH_THRESHOLD)

# THE TRIPLE LOCK: All three conditions must be TRUE
    triple_lock_mask = optical_mask.And(ndvi.lt(NDVI_THRESHOLD)).And(depth_only_mask)

# Cleanup noise
    mining_base = triple_lock_mask.focal_mode(radius=10, kernelType='circle', units='meters')

# Create Legal Boundary Mask
    boundary_mask = ee.Image.constant(0).byte().paint(roi, 1)

# 🟢 LEGAL: Inside Boundary + Triple Lock
    legal_mining = mining_base.And(boundary_mask.eq(1))

# 🔴 ILLEGAL: Outside Boundary + Triple Lock
    illegal_mining = mining_base.And(boundary_mask.eq(0))

    # --- D. QUANTIFICATION (UNCHANGED) ---
    print("📊 Calculating Metrics...")
    
    def get_metrics(mask, name):
        # Calculate Area
        area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=search_zone, scale=10, maxPixels=1e9
        ).values().get(0).getInfo() or 0.0
        
        # Calculate Volume (Area * Depth at that pixel)
        vol_layer = raw_depth.updateMask(mask)
        vol = vol_layer.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=search_zone, scale=30, maxPixels=1e9
        ).values().get(0).getInfo() or 0.0
        
        return area, vol

    legal_area_m2, legal_vol_m3 = get_metrics(legal_mining, "Legal")
    illegal_area_m2, illegal_vol_m3 = get_metrics(illegal_mining, "Illegal")

    total_area_m2 = legal_area_m2 + illegal_area_m2
    total_vol_m3 = legal_vol_m3 + illegal_vol_m3
    avg_depth_m = illegal_vol_m3 / illegal_area_m2 if illegal_area_m2 > 0 else 0.0

    # Get Lid Elevation (for 3D viz referencing)
    if legal_area_m2 > 0:
        lid_stats = smooth_surface.updateMask(legal_mining).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=search_zone, scale=30, maxPixels=1e9
        )
        lid_val = lid_stats.values().get(0).getInfo()
        lid_elevation = lid_val if lid_val else 0.0

    # --- E. PREPARE 3D DATA ---
    status_band = ee.Image.constant(0) \
        .where(illegal_mining, 1) \
        .where(legal_mining, 2) \
        .rename('status')
    
    combined_image = raw_depth.addBands(status_band)

    # --- F. OUTPUT GENERATION ---
    
    # 1. 2D Map (Updated Layers)
    Map = geemap.Map()
    Map.centerObject(roi, 14)
    Map.addLayer(s2_image, {"min":0, "max":3000, "bands":["B4","B3","B2"]}, "Satellite Image")
    
    # Visualizing the components helps debug
    Map.addLayer(optical_mask.selfMask(), {"palette":["yellow"]}, "Optical Hints (NDBI)")
    Map.addLayer(depth_only_mask.selfMask(), {"palette":["cyan"]}, "Depth Hints")
    
    # Final Result
    Map.addLayer(legal_mining.selfMask(), {"palette":["#00ff00"]}, "✅ LEGAL MINING")
    Map.addLayer(illegal_mining.selfMask(), {"palette":["#ff0000"]}, "🚨 ILLEGAL MINING")
    Map.addLayer(roi, {"color":"blue", "width":3}, "Lease Boundary")
    
    map_filename = "map_2d.html"
    Map.to_html(os.path.join(output_dir, map_filename))

    # 2. 3D TIN
    tin_filename = "model_3d.html"
    tin_full_path = os.path.join(output_dir, tin_filename)
    if (total_area_m2) > 0 and generate_tin_visualization:
        generate_tin_visualization(combined_image, search_zone, total_area_m2, output_path=tin_full_path)

    # 3. PDF Report
    pdf_filename = "report.pdf"
    if generate_pdf_report:
        report_data = {
            "start_date": start_date, "end_date": end_date, "dem_source": DEM_SOURCE,
            "filename": os.path.basename(filename),
            "illegal_area": illegal_area_m2, 
            "legal_area": legal_area_m2,
            "lid_elevation": lid_elevation, 
            "avg_depth": avg_depth_m, 
            "volume": illegal_vol_m3, 
            "total_volume": total_vol_m3,
            "trucks": int(illegal_vol_m3 / 15) if illegal_vol_m3 else 0
        }
        try:
            generate_pdf_report(report_data, output_path=os.path.join(output_dir, pdf_filename))
        except Exception as e:
            print(f"PDF Error: {e}")

    # --- G. RETURN METRICS ---
    return {
        "status": "success",
        "metrics": {
            "illegal_area_m2": round(illegal_area_m2, 2),
            "legal_area_m2": round(legal_area_m2, 2),
            "volume_m3": round(illegal_vol_m3, 2),
            "total_vol_m3": round(total_vol_m3, 2),
            "avg_depth_m": round(avg_depth_m, 2),
            "truckloads": int(illegal_vol_m3 / 15)
        },
        "artifacts": {
            "map_url": map_filename,
            "model_url": tin_filename if total_area_m2 > 0 else None,
            "report_url": pdf_filename
        }
    }
import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import quote_plus
import requests

# Konfigurasi Environment Variables dari GitHub Secrets / Vars
AMAZON_TAG = os.environ.get("AMAZON_TAG", "omniprime10-20").strip()
SITE_URL = os.environ.get("SITE_URL", "https://username.github.io/omniprime10-us").rstrip("/")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "user/omniprime10-us")

# Kunci verifikasi IndexNow deterministik untuk Bing, Yahoo, Yandex, DuckDuckGo
INDEXNOW_KEY = hashlib.md5(f"{REPO_NAME}_{AMAZON_TAG}_omniprime10".encode("utf-8")).hexdigest()

DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "omniprime_state.json")
IMAGE_CACHE_FILE = os.path.join(DATA_DIR, "stock_image_cache.json")
DOCS_DIR = "docs"
PRODUCTS_DIR = os.path.join(DOCS_DIR, "products")
REVIEWS_DIR = os.path.join(DOCS_DIR, "reviews")
CATEGORIES_DIR = os.path.join(DOCS_DIR, "categories")

HEADERS = {
    "User-Agent": "OmniPrime10StorefrontBot/2.0 (https://github.com; public-seo-engine@github.com)"
}

# 10 Kategori Terlaris Amazon US & 30 Subkategori
TAXONOMY = [
    {
        "category": "Smart Home & Security Tech",
        "cat_slug": "smart-home-security-tech",
        "icon": "🛡️",
        "img_keyword": "security camera smart home",
        "subcategories": [
            {
                "name": "4K Solar Security Cameras",
                "slug": "4k-solar-security-cameras",
                "img_q": "security camera outdoor",
                "brands": ["eufy Security", "Reolink", "Arlo", "Ring", "TP-Link Tapo"],
                "models": ["SoloCam S340 Dual-Lens Solar", "Argus PT Ultra 4K Solar", "Ultra 2 Spotlight 4K Kit", "Stick Up Cam Pro Solar", "C425 MagCam Solar 2K+"],
                "specs": {"Video Resolution": "4K UHD (3840x2160) Color Night Vision", "Power Source": "Integrated / Detachable Solar Panel + Rechargeable Battery", "Storage": "Local eMMC / MicroSD (No Monthly Fee Required)", "Weather Rating": "IP65/IP67 All-Season Weatherproof"},
                "buy_if": "You want 24/7 perimeter security and license-plate clarity without running coaxial cables or paying mandatory monthly cloud fees.",
                "skip_if": "Your mounting location sits under dense tree cover with zero direct sunlight."
            },
            {
                "name": "Biometric Smart Deadbolts",
                "slug": "biometric-smart-deadbolts",
                "img_q": "smart door lock",
                "brands": ["Schlage", "Yale", "Aqara", "eufy", "ULTRALOQ"],
                "models": ["Encode Plus Wi-Fi HomeKey", "Assure Lock 2 Touch Fingerprint", "Smart Lock U100 Apple HomeKey", "Video Smart Lock E330 3-in-1", "U-Bolt Pro Wi-Fi Biometric"],
                "specs": {"Unlock Methods": "3D Capacitive Fingerprint, Apple HomeKey, PIN, Physical Key", "Certification": "ANSI/BHMA Grade AAA Commercial Durability", "Connectivity": "Built-In Wi-Fi / Matter-Over-Thread", "Battery Life": "6 to 12 Months + USB-C Emergency Jump Port"},
                "buy_if": "You want keyless sub-0.3-second fingerprint entry and temporary guest PIN codes for family, dog walkers, or Airbnb guests.",
                "skip_if": "Your rental lease prohibits replacing exterior deadbolt cylinders."
            },
            {
                "name": "Wi-Fi 7 Mesh Routers",
                "slug": "wifi-7-mesh-routers",
                "img_q": "wireless router network",
                "brands": ["TP-Link Deco", "ASUS ZenWiFi", "Amazon eero", "NETGEAR Orbi", "Google Nest"],
                "models": ["BE65 Pro Tri-Band Wi-Fi 7 (3-Pack)", "BQ16 Pro Quad-Band Mesh", "Max 7 Tri-Band 10Gbps Mesh", "770 Series Tri-Band Wi-Fi 7", "Pro 6E / Wi-Fi 7 Whole-Home System"],
                "specs": {"Wireless Standard": "IEEE 802.11be (Wi-Fi 7) with Multi-Link Operation (MLO)", "Coverage": "Up to 7,500 – 9,000 Sq. Ft. Dead-Zone Elimination", "Ethernet Backhaul": "Dual 2.5Gbps / 10Gbps WAN/LAN Ports", "Device Capacity": "200+ Simultaneous Smart Home & 4K Streaming Devices"},
                "buy_if": "You have gigabit fiber internet and want rock-solid multi-floor coverage with zero dead zones in the garage or backyard.",
                "skip_if": "You live in a 500 sq. ft. studio apartment where a single router suffices."
            }
        ]
    },
    {
        "category": "Pet Care & Automated Tech",
        "cat_slug": "pet-care-automated-tech",
        "icon": "🐾",
        "img_keyword": "cat dog pet care",
        "subcategories": [
            {
                "name": "Self-Cleaning Cat Litter Boxes",
                "slug": "self-cleaning-cat-litter-boxes",
                "img_q": "cat indoor pet",
                "brands": ["Litter-Robot", "PETKIT", "Neakasa", "PetSafe", "MeoWant"],
                "models": ["4 Wi-Fi Open-Air Sifting Globe", "Purobot Ultra / PuraMax 2 Odor-Seal", "M1 Open-Top Automatic Litter Box", "ScoopFree Crystal Pro Self-Cleaning", "MW-SC01 Ultra-Quiet Auto Sifter"],
                "specs": {"Safety Sensors": "Infrared + Weight Scale Pinch-Prevention Array", "Odor Control": "Sealed Waste Drawer with Activated Carbon / UV Filter", "Multi-Cat Capacity": "Supports Up to 4 Cats (3.5 lbs to 25 lbs)", "App Telemetry": "Real-Time Cat Weight & Bathroom Frequency Tracking"},
                "buy_if": "You want to eliminate daily manual scooping and track your cat's urinary health via smartphone notifications.",
                "skip_if": "Your kitten weighs under 3 lbs (minimum weight required to trigger automatic safety sensors)."
            },
            {
                "name": "Smart Camera Pet Feeders",
                "slug": "smart-camera-pet-feeders",
                "img_q": "pet food bowl dog cat",
                "brands": ["PETLIBRO", "Petcube", "WOPET", "Whisker", "PetSafe"],
                "models": ["Granary Dual-Food 1080p Camera Feeder", "Bites 2 Lite Interactive Treat & Meal", "Heritage View 5L Wi-Fi Dispenser", "Feeder-Robot Automatic Portion Pro", "Smart Feed 2.0 Stainless Bowl"],
                "specs": {"Hopper Volume": "4.0L to 5.0L Desiccant-Sealed Dry Kibble Storage", "Camera System": "1080p HD 145° Wide-Angle + Two-Way Audio & Night Vision", "Bowl Material": "Food-Grade 304 Stainless Steel (Prevents Chin Acne)", "Backup Power": "Dual Power: USB-C Wall Adapter + Battery Blackout Backup"},
                "buy_if": "You work long shifts or travel on weekends and want scheduled portion control with live video verification.",
                "skip_if": "You feed a 100% raw wet-food diet that requires constant refrigeration."
            },
            {
                "name": "Orthopedic Dog Beds",
                "slug": "orthopedic-memory-foam-dog-beds",
                "img_q": "dog sleeping bed",
                "brands": ["Big Barker", "Furhaven", "Casper", "Bedsure", "PetFusion"],
                "models": ["7-Inch Pillow Top Orthopedic XL", "Plush & Suede Bolster Sofa Bed", "Memory Foam Engineered Dog Bed", "CertiPUR-US Egg-Crate Waterproof Sofa", "Ultimate Lounge Solid Memory Foam"],
                "specs": {"Foam Core": "Solid / Dual-Layer CertiPUR-US High-Density Orthopedic Foam", "Liner Protection": "100% Waterproof Internal Breathable Membrane", "Outer Cover": "Machine-Washable Tear-Resistant Microfiber Bolster", "Joint Support": "Calibrated for Senior Dogs, Hip Dysplasia & Arthritis"},
                "buy_if": "You have a large-breed or senior dog that needs pressure-point relief and a waterproof, washable cover.",
                "skip_if": "Your puppy is in an aggressive destructive chewing phase (use a chew-proof elevated cot first)."
            }
        ]
    },
    {
        "category": "Outdoor Gear & Camping",
        "cat_slug": "outdoor-gear-camping",
        "icon": "⛺",
        "img_keyword": "camping tent outdoor mountains",
        "subcategories": [
            {
                "name": "Ultralight Backpacking Tents",
                "slug": "ultralight-backpacking-tents",
                "img_q": "camping tent nature",
                "brands": ["Big Agnes", "MSR", "NEMO", "Kelty", "Naturehike"],
                "models": ["Copper Spur HV UL2 Bikepack/Trail", "Hubba Hubba NX 2-Person Freestanding", "Dagger OSMO Ultralight 2P/3P", "Late Start 2-Person Fast-Pitch", "Cloud Up 20D Silicone Ultralight"],
                "specs": {"Trail Weight": "2 lbs 10 oz to 3 lbs 12 oz Ultralight Pack Weight", "Poles": "DAC Featherlite Aluminum Pre-Bent Hub Architecture", "Waterproof Rating": "1500mm–3000mm Ripstop Sil-Nylon Rainfly & Bathtub Floor", "Ventilation": "Dual Doors +Dual Vestibules with No-See-Um Mesh"},
                "buy_if": "You hike multi-day backcountry trails or bikepack and need storm-worthy shelter under 3.5 lbs.",
                "skip_if": "You want a standing-height 8-person family cabin tent for drive-in car campgrounds."
            },
            {
                "name": "Rotomolded Hard Coolers",
                "slug": "rotomolded-hard-coolers",
                "img_q": "cooler box camping",
                "brands": ["YETI", "RTIC", "Coleman", "Igloo", " Pelican"],
                "models": ["Tundra 45 / Roadie 48 Wheeled", "52-Qt Ultra-Light Hard Cooler", "Pro Series 55-Qt Heavy-Duty", "BMX / Trailmate 52-Qt All-Terrain", "Elite 50-Qt Extreme Ice Retention"],
                "specs": {"Ice Retention": "5 to 8 Days Sub-Freezing Permafrost Polyurethane Insulation", "Shell Construction": "One-Piece Rotomolded UV-Resistant Armored Polyethylene", "Lid Seal": "Freezer-Grade Interlocking Silicone Gasket + Heavy Latches", "Drain System": "Leakproof Tethered Vortex Rapid Drain Plug"},
                "buy_if": "You camp off-grid, tailgate, or fish for multiple days and need guaranteed ice retention in 95°F summer heat.",
                "skip_if": "You only need a lightweight soft lunchbag for a 2-hour beach walk."
            },
            {
                "name": "Portable Water Filters",
                "slug": "portable-backcountry-water-filters",
                "img_q": "water bottle hiking",
                "brands": ["Sawyer", "Katadyn", "Grayl", "LifeStraw", "Platypus"],
                "models": ["Squeeze 0.1 Micron Hollow-Fiber System", "BeFree 1.0L Fast-Flow Collapsible", "GeoPress 24-Oz Purifier Bottle", "Peak Series Gravity 3L Bag System", "QuickDraw Microfilter 2L Kit"],
                "specs": {"Pore Size": "0.1 Micron Absolute Hollow-Fiber / Electroadsorptive Media", "Pathogen Removal": "99.99999% Bacteria (Salmonella, E. coli) & 99.9999% Protozoa", "Flow Rate": "Up to 2.0 Liters Per Minute Squeeze / Press", "Filter Lifespan": "1,000 to 100,000 Gallons Backflushable Capacity"},
                "buy_if": "You need instant, chemical-free safe drinking water from alpine lakes, streams, or international hotel taps.",
                "skip_if": "You only camp at RV parks with municipal potable water hookups."
            }
        ]
    },
    {
        "category": "Fitness & Recovery Equipment",
        "cat_slug": "fitness-recovery-equipment",
        "icon": "🏋️",
        "img_keyword": "dumbbells gym fitness workout",
        "subcategories": [
            {
                "name": "Adjustable Dumbbell Sets",
                "slug": "quick-lock-adjustable-dumbbells",
                "img_q": "dumbbells gym weights",
                "brands": ["Bowflex", "PowerBlock", "NÜOBELL", "NordicTrack", "Flybird"],
                "models": ["SelectTech 552 Dual Pair (5–52.5 lbs)", "Elite EXP Stage-1 Expandable (5–90 lbs)", "80-lb CNC Knurled Twist-Lock Pair", "iSelect Voice-Controlled 50-lb Pair", "55-lb Rapid-Dial Home Gym Pair"],
                "specs": {"Weight Range": "5 lbs to 52.5 / 80 lbs per Hand in 2.5–5 lb Increments", "Adjustment Mechanism": "1-Second Single-Handed Twist / Pin Selector Dial", "Space Saved": "Replaces 15 to 30 Individual Pairs of Free Weights", "Cradle Tray": "Heavy-Impact Molded Retention Storage Base"},
                "buy_if": "You want a full progressive-overload strength training rack in a compact bedroom or garage corner.",
                "skip_if": "You routinely drop heavy dumbbells from overhead onto concrete floors."
            },
            {
                "name": "Under-Desk Walking Pads",
                "slug": "under-desk-walking-pad-treadmills",
                "img_q": "treadmill running fitness",
                "brands": ["UREVO", "WalkingPad", "Sperax", "Sunny Health", "DeerRun"],
                "models": ["2-in-1 Folding Incline Walking Pad", "C2 / A1 Pro Foldable Smart Treadmill", "3-in-1 Under-Desk Vibration Pad", "Slim-Flat Brushless Office Treadmill", "Q1 Mini Whisper-Quiet 2.5HP Pad"],
                "specs": {"Motor Drive": "2.25 to 2.5 HP Whisper-Quiet Brushless Motor (<45 dB)", "Speed Range": "0.6 MPH to 4.0 / 7.5 MPH (LED Remote & App Control)", "Deck Cushioning": "5-Layer Non-Slip Belt + 8 Silicone Shock Absorbers", "Storage Profile": "5-Inch Slim Profile Slides Under Sofa or Standing Desk"},
                "buy_if": "You work remotely at a standing desk and want to hit 10,000 daily steps during Zoom calls regardless of weather.",
                "skip_if": "You are training for sub-6-minute marathon sprinting intervals."
            },
            {
                "name": "Deep-Tissue Massage Guns",
                "slug": "percussion-deep-tissue-massage-guns",
                "img_q": "massage therapy recovery",
                "brands": ["Therabody", "Bob and Brad", "Hyperice", "TOLOCO", "RENPHO"],
                "models": ["Theragun Prime / Relief Ergonomic", "Q2 Mini / C2 Pro Heated & Cold Head", "Hypervolt 2 QuietGlide Bluetooth", "EM26 Deep-Tissue 12mm Amplitude", "Active Thermacool Percussion Gun"],
                "specs": {"Stroke Amplitude": "10mm to 16mm True Deep-Muscle Percussion Depth", "Stall Force": "30 lbs to 60 lbs No-Stall Brushless High-Torque Motor", "Attachments": "5 to 8 Interchangeable Closed-Cell Foam & Heated Heads", "Battery Runtime": "180 to 300 Minutes USB-C Fast-Charge Lithium Pack"},
                "buy_if": "You experience post-workout DOMS soreness, tight hamstrings, or upper-trap stiffness from desk work.",
                "skip_if": "You have acute bone fractures or prefer gentle spa-style Swedish surface rubbing."
            }
        ]
    },
    {
        "category": "Automotive & Garage Tools",
        "cat_slug": "automotive-garage-tools",
        "icon": "🚗",
        "img_keyword": "car dashboard automotive tool",
        "subcategories": [
            {
                "name": "3-Channel 4K Dash Cams",
                "slug": "3-channel-4k-dash-cams",
                "img_q": "car windshield driving",
                "brands": ["VIOFO", "Vantrue", "Rove", "Redtiger", "Garmin"],
                "models": ["A229 Pro 3CH 4K Sony STARVIS 2", "N4 Pro 3-Channel 4K Front/Inside/Rear", "R2-4K PRO Dual STARVIS GPS", "F7NP 4K Front & Rear 5GHz Wi-Fi", "Dash Cam Live / Mini 3 Voice Control"],
                "specs": {"Image Sensor": "Sony STARVIS 2 IMX678 HDR Night-Plate Recognition", "Power Design": "Supercapacitor Extreme Heat Resistance (-4°F to 158°F)", "Connectivity": "5GHz Ultra-Fast Wi-Fi App Download + Built-In GPS Logger", "Parking Mode": "24/7 Buffered Low-Bitrate & Motion Collision Recording"},
                "buy_if": "You commute daily or drive rideshare and want irrefutable 4K license-plate evidence day or night.",
                "skip_if": "Your vehicle already includes built-in multi-angle factory dashcam recording."
            },
            {
                "name": "Lithium Jump Starters",
                "slug": "lithium-car-battery-jump-starters",
                "img_q": "car battery engine mechanic",
                "brands": ["NOCO", "GOOLOO", "AVAPOW", "HULKMAN", "DEWALT"],
                "models": ["Boost Plus GB40 / GB50 XL 1500A", "GP4000 SuperSafe 4000A Peak Pro", "A68 6000A Heavy-Duty 12V Pack", "Alpha 85S Pre-Heat Extreme Cold", "DXAEJ14 Digital Jump Starter + Compressor"],
                "specs": {"Peak Cranking Amps": "1,500A to 4,000A (Starts Up to 9.0L Gas & 7.0L Diesel)", "Safety Protection": "UltraSafe Spark-Proof + Reverse Polarity Protection", "Power Bank Function": "60W USB-C PD Fast Laptop/Phone Charging + 400-Lumen Strobe", "Standby Retention": "Holds Charge up to 12–24 Months in Glovebox"},
                "buy_if": "You want self-reliant 30-second dead-battery recovery in winter parking lots without waiting for roadside assistance.",
                "skip_if": "You drive a pure battery-electric vehicle without a 12V accessory system."
            },
            {
                "name": "Bi-Directional OBD2 Scanners",
                "slug": "bidirectional-obd2-diagnostic-scanners",
                "img_q": "car mechanic diagnostic tool",
                "brands": ["BlueDriver", "TOPDON", "Autel", "FOXWELL", "ANCEL"],
                "models": ["Bluetooth Pro OBDII Scan Tool", "TopScan Pro Bi-Directional Active Test", "MaxiCOM MK808S Full-System Tablet", "NT630 Plus ABS & SRS Bleed Tool", "BD310 / AD410 Enhanced Check-Engine"],
                "specs": {"System Coverage": "All-System Diagnostics (Engine, Transmission, ABS, Airbag, DPF)", "Active Control": "Bi-Directional Actuator Tests & 28+ Maintenance Resets", "Database": "Verified ASE Mechanic Repair Reports & Live PID Graphing", "Subscription": "Lifetime Free Software Updates (on Select Pro Models)"},
                "buy_if": "You want to read check-engine, ABS, and airbag codes yourself and avoid $150 dealership diagnostic fees.",
                "skip_if": "Your car was manufactured prior to the 1996 OBD-II standardization mandate."
            }
        ]
    },
    {
        "category": "Audio & Creator Studio Gear",
        "cat_slug": "audio-creator-studio-gear",
        "icon": "🎧",
        "img_keyword": "headphones microphone audio studio",
        "subcategories": [
            {
                "name": "ANC Over-Ear Headphones",
                "slug": "anc-wireless-over-ear-headphones",
                "img_q": "headphones audio music",
                "brands": ["Sony", "Bose", "Sennheiser", "Soundcore", "Apple"],
                "models": ["WH-1000XM5 / WH-CH720N Wireless ANC", "QuietComfort Ultra Spatial Audio", "MOMENTUM 4 Wireless 60-Hr Battery", "Space One Pro / Q45 LDAC Hi-Res", "Beats Studio Pro Lossless USB-C"],
                "specs": {"Noise Cancellation": "Multi-Microphone Adaptive Active Noise Cancellation (ANC)", "Battery Endurance": "30 to 60 Hours Continuous Playback (5-Min Quick Charge)", "Audio Codecs": "LDAC, aptX Adaptive, AAC & Wired USB-C DAC", "Multipoint": "Simultaneous Dual-Device Bluetooth 5.3 Pairing"},
                "buy_if": "You fly frequently, commute on noisy trains, or work in open offices and need total acoustic isolation.",
                "skip_if": "You only want waterproof in-ear buds for heavy-sweat running."
            },
            {
                "name": "XLR/USB Podcast Microphones",
                "slug": "xlr-usb-dynamic-podcast-microphones",
                "img_q": "studio microphone podcast",
                "brands": ["Shure", "Rode", "FIFINE", "Audio-Technica", "Elgato"],
                "models": ["MV7+ Hybrid XLR/USB-C Dynamic", "PodMic USB Broadcast Dynamic", "Tank3 / K688 Dynamic Studio Mic", "AT2040USB Hypercardioid Dynamic", "Wave DX + Wave XLR Broadcast Bundle"],
                "specs": {"Capsule Type": "Dynamic Cardioid (Rejects Untreated Room Echo & Keyboard Clicks)", "Outputs": "Dual Hybrid USB-C Digital DSP + Professional 3-Pin XLR", "Onboard DSP": "Real-Time Auto-Leveler, Digital Popper Stopper & Denoiser", "Bit Depth": "24-Bit / 48kHz Broadcast Studio Resolution"},
                "buy_if": "You record podcasts, YouTube voiceovers, or executive Zoom calls in an untreated bedroom or home office.",
                "skip_if": "You are recording an acoustic string quartet from 10 feet away."
            },
            {
                "name": "Dolby Atmos Soundbars",
                "slug": "dolby-atmos-home-theater-soundbars",
                "img_q": "home theater television speaker",
                "brands": ["Sonos", "Bose", "Samsung", "JBL", "VIZIO"],
                "models": ["Arc Ultra / Beam Gen 2 Dolby Atmos", "Smart Ultra Soundbar with AI Dialogue", "HW-Q990D / Q800D 11.1.4ch Wireless Sub", "Bar 1000 7.1.4 Detachable Surrounds", "Elevate SE 5.1.2 Rotating Atmos Speakers"],
                "specs": {"Channel Architecture": "Up-Firing True Dolby Atmos & DTS:X 3D Acoustic Dome", "Connectivity": "HDMI eARC Uncompressed Audio + Wi-Fi AirPlay 2", "Voice Enhancement": "AI Center-Channel Vocal Clarity Booster", "Subwoofer": "Wireless Deep-Bass Reflex Subwoofer Included/Compatible"},
                "buy_if": "You can barely hear whispered movie dialogue on flat-screen TV speakers and want cinema-grade 3D surround sound.",
                "skip_if": "You already have a wired 9.2-channel AVR receiver with in-ceiling speakers."
            }
        ]
    },
    {
        "category": "Baby & Nursery Essentials",
        "cat_slug": "baby-nursery-essentials",
        "icon": "🍼",
        "img_keyword": "baby nursery stroller crib",
        "subcategories": [
            {
                "name": "4K Split-Screen Baby Monitors",
                "slug": "split-screen-video-baby-monitors",
                "img_q": "baby sleeping crib",
                "brands": ["Infant Optics", "HelloBaby", "Nanit", "Momcozy", "eufy Care"],
                "models": ["DXR-8 PRO Active Noise Reduction", "HB6550 5-Inch Pan-Tilt-Zoom 2-Cam", "Pro Smart Breathing Wear Monitor", "BM01 5.5-Inch 1080p Non-WiFi Secure", "SpaceView Pro 720p Wide-Angle"],
                "specs": {"Security Protocol": "100% Hack-Proof FHSS Closed-Loop Local Radio / AES-256", "Display Screen": "5.0 to 5.5-Inch HD Split-Screen Parent Unit + Remote Pan/Tilt", "Audio Filtering": "Active White-Noise Background Suppression (Hears Cries Only)", "Range": "Up to 1,000 Feet Multi-Wall Home Penetration"},
                "buy_if": "You want instant, lag-free overnight video monitoring of one or two nursery rooms without relying on home Wi-Fi.",
                "skip_if": "You live in a tiny studio layout where the crib is 4 feet from your bed."
            },
            {
                "name": "All-in-One Convertible Car Seats",
                "slug": "all-in-one-convertible-car-seats",
                "img_q": "car seat safety child",
                "brands": ["Graco", "Britax", "Chicco", "Nuna", "Evenflo"],
                "models": ["4Ever DLX Grad 4-in-1 (10-Year Use)", "One4Life ClickTight All-in-One", "OneFit ClearTex All-in-One Slim", "REVV / RAVA Flame-Retardant-Free", "Revolve360 Extend Rotational Seat"],
                "specs": {"Growth Stages": "Rear-Facing (4–50 lbs), Forward-Facing (22–65 lbs) & Belt Booster (40–120 lbs)", "Installation System": "60-Second ClickTight / SnugLock Seatbelt Tensioner", "Safety Frame": "Steel-Reinforced Side-Impact Energy-Absorbing Shell", "Fabric": "GREENGUARD Gold Certified Machine-Washable Cover"},
                "buy_if": "You want one crash-tested car seat that adapts from newborn hospital discharge all the way to age 10.",
                "skip_if": "You specifically want a lightweight detachable infant carrier basket that clicks into a stroller."
            },
            {
                "name": "Compact Travel Strollers",
                "slug": "compact-overhead-bin-travel-strollers",
                "img_q": "baby stroller park",
                "brands": ["UPPAbaby", "Bugaboo", "Babyzen", "Ergobaby", "Mompush"],
                "models": ["Minu V2 One-Hand Fold Travel", "Butterfly 1-Second Ultra-Compact", "YOYO2 IATA Overhead-Bin Stroller", "Metro+ Deluxe Padded Compact", "Lithe V2 Lightweight Airplane Stroller"],
                "specs": {"Folded Dimensions": "IATA Airline Overhead-Bin Compliant One-Hand Fold", "Stroller Weight": "13.6 lbs to 16.9 lbs Aircraft Aluminum Frame", "Suspension": "4-Wheel All-Terrain Spring Suspension + Puncture-Proof Tires", "Canopy": "UPF 50+ Extendable Water-Repellent Sunshade"},
                "buy_if": "You fly with toddlers or navigate crowded city subways and want a stroller that folds into airplane overhead bins.",
                "skip_if": "You want an oversized pneumatic-tire jogging stroller for rocky mountain trails."
            }
        ]
    },
    {
        "category": "Lawn, Patio & Power Tools",
        "cat_slug": "lawn-patio-power-tools",
        "icon": "🛠️",
        "img_keyword": "power drill tools workshop",
        "subcategories": [
            {
                "name": "Brushless Cordless Drill Combos",
                "slug": "brushless-cordless-drill-combo-kits",
                "img_q": "cordless drill tool",
                "brands": ["DEWALT", "Milwaukee", "Makita", "BOSCH", "RYOBI"],
                "models": ["20V MAX XR Brushless Hammer Drill + Impact Kit", "M18 FUEL 2-Tool Brushless Combo", "18V LXT Lithium-Ion Sub-Compact Combo", "18V Freak 2-in-1 Bit/Socket Impact + Drill", "ONE+ HP 18V Brushless 2-Tool Kit"],
                "specs": {"Motor Technology": "Brushless Copper Motor (57% More Runtime vs Brushed)", "Chuck & Collet": "1/2-Inch All-Metal Ratcheting Chuck + 1/4-Inch Hex Impact", "Torque Output": "Up to 1,800 in-lbs Fastening Torque / 2,000 RPM", "Battery Pack": "Includes Two Lithium-Ion Packs, Fast Charger & Hard Case"},
                "buy_if": "You tackle home renovations, deck building, and furniture assembly and want pro-grade torque that lasts a decade.",
                "skip_if": "You only tighten a loose eyeglass screw once a year."
            },
            {
                "name": "Robotic Lawn Mowers",
                "slug": "wire-free-robotic-lawn-mowers",
                "img_q": "lawn mower grass garden",
                "brands": ["Mammotion", "Segway Navimow", " Greenworks", "EGO Power+", "WORX"],
                "models": ["LUBA 2 AWD RTK Wire-Free Mower", "i105N / H-Series GPS Boundary-Free", "60V Pro 21-Inch Self-Propelled Dual-Port", "Power+ LM2156SP Select Cut XP", "Landroid Vision AI Camera Mower"],
                "specs": {"Navigation / Drive": "RTK-GNSS + 3D Vision Wire-Free / High-Torque Brushless Self-Propelled", "Slope Climbing": "Handles Up to 45% – 80% (38°) Yard Incline Gradients", "Cutting Deck": "Multi-Blade Mulching Micro-Clipping System", "Weather Sensor": "Auto-Rain Dock Return + IPX6 Hose-Washable Deck"},
                "buy_if": "You want a manicured lawn every morning without pushing a loud, fume-heavy gas mower in summer humidity.",
                "skip_if": "Your yard consists entirely of gravel xeriscaping with no grass."
            },
            {
                "name": "Electric Pressure Washers",
                "slug": "electric-high-psi-pressure-washers",
                "img_q": "pressure washer cleaning",
                "brands": ["Westinghouse", "Sun Joe", "Giraffe Tools", "Greenworks", "Craftsman"],
                "models": ["ePX3100v 2300 PSI Anti-Tip Pro", "SPX3000 2030 PSI Dual Detergent Tank", "Grandfalls Wall-Mounted 100-Ft Retractable", "Pro 3000 PSI Brushless TruBrushless", "2100 MAX PSI Cold-Water Foam Cannon Kit"],
                "specs": {"Cleaning Power": "2,030 to 3,000 MAX PSI @ 1.76 – 2.0 GPM Water Flow", "Pump System": "Total Stop System (TSS) Auto-Trigger Pump Saver", "Nozzle Array": "Quick-Connect 0°, 15°, 25°, 40° Steel Tips + Foam Cannon", "Safety": "35-Foot GFCI Inline Weatherproof Power Cord"},
                "buy_if": "You want to strip driveway algae, wash foam onto cars, and blast patio mildew without carburetor maintenance.",
                "skip_if": "You have no outdoor garden hose spigot at your property."
            }
        ]
    },
    {
        "category": "Travel Luggage & Carry-Ons",
        "cat_slug": "travel-luggage-carry-ons",
        "icon": "🧳",
        "img_keyword": "suitcase luggage airport travel",
        "subcategories": [
            {
                "name": "Polycarbonate Hardshell Spinners",
                "slug": "polycarbonate-hardshell-spinner-luggage",
                "img_q": "suitcase luggage travel",
                "brands": ["Samsonite", "Travelpro", "Level8", "Delsey Paris", "Coolife"],
                "models": ["Freeform / Omni 2 Hardside Expandable", "Maxlite Air / Platinum Elite Spinner", "Luminous Textured 20-Inch Carry-On", "Chatelet Air 2.0 / Helium Aero", "3-Piece ABS+PC TSA Lock Spinner Set"],
                "specs": {"Shell Material": "100% Virgin Makrolon Polycarbonate Impact-Flex Shell", "Wheel System": "360° Hinomoto / Dual-Ball-Bearing Silent Spinner Wheels", "Security": "Recessed TSA-Accepted 3-Dial Combination Lock + YKK Zippers", "Expansion": "2-Inch Zippered Gusset Expansion + Cross-Strap Divider"},
                "buy_if": "You want a crack-resistant carry-on that glides effortlessly across carpeted airport terminals.",
                "skip_if": "You exclusively hike rough dirt paths where wheeled suitcases cannot roll."
            },
            {
                "name": "TSA Laptop Travel Backpacks",
                "slug": "tsa-laptop-travel-backpacks",
                "img_q": "backpack laptop travel",
                "brands": ["Peak Design", "Osprey", "Nomatic", "MATEIN", "SwissGear"],
                "models": ["Travel Backpack 45L Weatherproof", "Farpoint 40 / Daylite Expandable", "40L Travel Bag V2 Convertible", "Carry-On 40L Flight-Approved Weekender", "1900 ScanSmart 17-Inch TSA Backpack"],
                "specs": {"Capacity": "30L to 45L Clamshell Suitcase-Style Main Opening", "Laptop Protection": "Suspended Padded 16-Inch / 17.3-Inch TSA Lay-Flat Sleeve", "Fabric": "Water-Resistant 400D–900D Recycled Nylon + Luggage Pass-Through", "Ergonomics": "Breathable Air-Mesh Back Panel + Tuck-Away Hip Belt"},
                "buy_if": "You travel One-Bag style on budget or international airlines and want to avoid checked-bag fees and lost luggage.",
                "skip_if": "You pack 5 pairs of formal shoes and heavy winter coats for 3-week cruises."
            },
            {
                "name": "Compression Packing Cubes",
                "slug": "compression-travel-packing-cubes",
                "img_q": "travel bag organizer",
                "brands": ["Peak Design", "Eagle Creek", "BAGSMART", "Thule", "Gonex"],
                "models": ["Ultralight Tear-Away Compression Cubes", "Pack-It Isolate Compression Set", "6-Piece Double-Zipper Mesh Set", "Clean/Dirty Divided Water-Resistant Cube", " Ripstop Nylon 6-Set Organizer"],
                "specs": {"Compression Ratio": "Dual-Zipper Gusset Compresses Clothing Volume by 40%–50%", "Textile": "Ultralight 70D Self-Healing Ripstop Nylon / Breathable Mesh", "Organization": "Internal Clean/Dirty Laundered Compartment Divider", "Durability": "Reinforced Cord Pulls & Snag-Free Gusseted Seams"},
                "buy_if": "You want to fit 7 days of outfits into a single 20-inch carry-on while keeping clean and worn clothes separated.",
                "skip_if": "You travel with hanging garment bags only."
            }
        ]
    },
    {
        "category": "Coffee, Tea & Craft Beverage",
        "cat_slug": "coffee-tea-craft-beverage",
        "icon": "☕",
        "img_keyword": "coffee grinder espresso kettle",
        "subcategories": [
            {
                "name": "Conical Burr Coffee Grinders",
                "slug": "conical-flat-burr-coffee-grinders",
                "img_q": "coffee beans grinder",
                "brands": ["Fellow", "Baratza", "OXO", "Breville", "1Zpresso"],
                "models": ["Opus All-Purpose / Ode Brew Gen 2", "Encore ESP Espresso & Filter Burr", "Brew Stainless Steel Conical Burr", "Smart Grinder Pro 60-Setting LCD", "J-Ultra / K-Ultra Precision Hand Grinder"],
                "specs": {"Burr Geometry": "40mm–64mm Hardened Stainless Steel Conical / Flat Burrs", "Grind Settings": "31 to 60 Micro-Stepped Settings (Turkish/Espresso to Cold Brew)", "Anti-Static Tech": "Ionizer Plasma Anti-Static Chute (Zero Chaff Mess)", "Retention": "Low-Retention Single-Dose Hopper + Magnetic Catch Cup"},
                "buy_if": "You want uniform particle size distribution that unlocks sweet, balanced flavor notes in espresso and pour-over coffee.",
                "skip_if": "You only buy pre-ground supermarket tin coffee."
            },
            {
                "name": "Variable-Temp Gooseneck Kettles",
                "slug": "variable-temp-gooseneck-electric-kettles",
                "img_q": "kettle tea coffee pour over",
                "brands": ["Fellow", "Bonavita", "COSORI", "OXO", "Hario"],
                "models": ["Stagg EKG Pro Studio Electric Kettle", "1.0L Digital Variable Temperature", "Smart Gooseneck 5-Preset Bluetooth", "Brew Adjustable Temperature Pour-Over", "Buono V60 Temperature Control"],
                "specs": {"Temperature Precision": "104°F to 212°F Degree-by-Degree PID Hold (60-Min Keep Warm)", "Spout Profile": "Precision Counterbalanced Slow-Flow Gooseneck Spout", "Interior Body": "100% Food-Grade 304 18/8 Stainless Steel (Zero Plastic Contact)", "Heating Power": "1200W Quick-Boil Element + Boil-Dry Auto-Shutoff"},
                "buy_if": "You brew specialty V60/Chemex pour-over coffee or delicate green, oolong, and matcha teas requiring exact temperatures.",
                "skip_if": "You just need a wide-spout pot to boil 2 liters of pasta water."
            },
            {
                "name": "Cold Brew & Nitro Makers",
                "slug": "cold-brew-nitro-coffee-makers",
                "img_q": "iced coffee glass",
                "brands": ["OXO", "Takeya", "KitchenAid", "Vinci", "Toddy"],
                "models": ["Good Grips 32-Oz Compact Cold Brewer", "Patented Deluxe 2-Qt Airtight Pitcher", "38-Oz Stainless Tap Refrigerator Brewer", "Express Electric Cold Brew in 10 Mins", " Artisan Commercial Cold Brew System"],
                "specs": {"Filtration": "Ultra-Fine Reusable Stainless Steel Mesh + Paper Micro-Filter", "Extraction Method": "Rainmaker Perforated Water Dispersal / Rapid Vacuum Pulse", "Carafe Material": "Thermal Shock-Resistant Borosilicate Glass / Tritan", "Concentrate Yield": "Up to 14 Servings of Low-Acid Smooth Concentrate (2-Week Fridge Life)"},
                "buy_if": "You love smooth, 65% less-acidic iced coffee and want to stop spending $6.50 daily at coffee chains.",
                "skip_if": "You exclusively drink piping-hot espresso shots."
            }
        ]
    }
]

EDITIONS = [
    ("2026 Pro Edition", "updated 2026 top-seller configuration engineered for daily reliability"),
    ("Complete Starter Bundle", "all-in-one bundle packaged with essential accessories"),
    ("Signature Series", "flagship consumer choice backed by verified specifications"),
    ("Next-Gen Performance Spec", "precision-engineered hardware revision with improved efficiency")
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


def make_amazon_url(query: str) -> str:
    """
    Membuat tautan afiliasi Amazon US dengan Tracking ID otomatis,
    diurutkan berdasarkan Best-Sellers (exact-aware-popularity-rank) dan rating 4 bintang ke atas.
    """
    encoded = quote_plus(query)
    return (
        f"https://www.amazon.com/s?k={encoded}"
        f"&s=exact-aware-popularity-rank&rh=p_72%3A1248873011&tag={AMAZON_TAG}"
    )


def load_image_cache() -> dict:
    if os.path.exists(IMAGE_CACHE_FILE):
        try:
            with open(IMAGE_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_image_cache(cache: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IMAGE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def fetch_free_stock_image(query: str, variant_idx: int, cache: dict) -> dict:
    """
    Mengambil gambar gratis resolusi tinggi dari API publik tanpa API key:
    1. Openverse Public API (https://api.openverse.org/v1/images/)
    2. Wikimedia Commons Public API (https://commons.wikimedia.org/w/api.php)
    3. Fallback deterministik ke LoremFlickr Stock Photo CDN agar 100% bebas broken-image.
    """
    cache_key = f"{query}_{variant_idx % 5}"
    if cache_key in cache:
        return cache[cache_key]

    # 1. Coba Openverse Public API (Tanpa API Key)
    try:
        ov_url = f"https://api.openverse.org/v1/images/?q={quote_plus(query)}&page_size=6"
        r = requests.get(ov_url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                picked = results[variant_idx % len(results)]
                img_url = picked.get("thumbnail") or picked.get("url")
                if img_url and img_url.startswith("http"):
                    res_obj = {
                        "url": img_url,
                        "credit": f"Openverse CC ({picked.get('license', 'CC0').upper()})"
                    }
                    cache[cache_key] = res_obj
                    return res_obj
    except Exception:
        pass

    # 2. Coba Wikimedia Commons Public MediaWiki API (Tanpa API Key)
    try:
        wm_url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&generator=search&gsrsearch=filetype:bitmap+{quote_plus(query)}"
            "&gsrnamespace=6&gsrlimit=5&prop=imageinfo&iiprop=url&iiurlwidth=640&format=json"
        )
        r = requests.get(wm_url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            pages = list(r.json().get("query", {}).get("pages", {}).values())
            if pages:
                picked = pages[variant_idx % len(pages)]
                ii = picked.get("imageinfo", [{}])[0]
                img_url = ii.get("thumburl") or ii.get("url")
                if img_url and img_url.startswith("http"):
                    res_obj = {
                        "url": img_url,
                        "credit": "Wikimedia Commons Public Media"
                    }
                    cache[cache_key] = res_obj
                    return res_obj
    except Exception:
        pass

    # 3. Fallback deterministik ke CDN foto stok bebas lisensi
    clean_tag = re.sub(r"[^a-zA-Z0-9]", ",", query.split()[0])
    fallback_obj = {
        "url": f"https://loremflickr.com/640/440/{clean_tag}?lock={variant_idx + 100}",
        "credit": "Creative Commons Public Stock"
    }
    cache[cache_key] = fallback_obj
    return fallback_obj


def init_or_load_state() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                if state.get("products"):
                    return state
        except Exception:
            pass

    # Bangun antrean 600 produk di 10 kategori terlaris (30 subkategori)
    products = []
    idx = 1
    for ed_name, ed_desc in EDITIONS:
        for model_i in range(5):
            for cat in TAXONOMY:
                for sub in cat["subcategories"]:
                    brand = sub["brands"][model_i % len(sub["brands"])]
                    model = sub["models"][model_i % len(sub["models"])]
                    title = f"{brand} {model} ({ed_name})"
                    slug = f"{slugify(brand)}-{slugify(model)}-{slugify(ed_name)}-{idx}"
                    products.append({
                        "id": f"OP-{idx:04d}",
                        "idx": idx,
                        "slug": slug,
                        "name": title,
                        "brand": brand,
                        "category": cat["category"],
                        "cat_slug": cat["cat_slug"],
                        "cat_icon": cat["icon"],
                        "subcategory": sub["name"],
                        "sub_slug": sub["slug"],
                        "img_q": sub["img_q"],
                        "image_url": "",
                        "image_credit": "",
                        "search_query": f"{brand} {model} {sub['name']}",
                        "summary": f"The {title} is an Amazon top-ranked {sub['name'].lower()}—an {ed_desc}.",
                        "specs": sub["specs"],
                        "buy_if": sub["buy_if"],
                        "skip_if": sub["skip_if"],
                        "pros": [
                            f"Authentic {brand} build quality with verified performance metrics",
                            f"{list(sub['specs'].keys())[0]}: {list(sub['specs'].values())[0]}",
                            f"{list(sub['specs'].keys())[1]}: {list(sub['specs'].values())[1]}"
                        ],
                        "cons": [
                            "High consumer demand on Amazon can occasionally impact specific color/bundle stock",
                            "Verify exact dimensions and compatibility prior to checkout"
                        ],
                        "published": False,
                        "published_at": ""
                    })
                    idx += 1

    state = {"products": products, "reviews": [], "cycle_count": 0}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return state


def save_state(state: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_common_styles() -> str:
    return """
        :root {
            --bg: #ffffff;
            --surface: #f8fafc;
            --border: #e2e8f0;
            --navy: #0f172a;
            --slate: #475569;
            --indigo: #4f46e5;
            --indigo-dark: #3730a3;
            --indigo-light: #eef2ff;
            --amber: #d97706;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--navy); line-height: 1.65; }
        .compliance-bar { background: var(--navy); color: #f8fafc; font-size: 0.79rem; text-align: center; padding: 9px 16px; }
        .compliance-bar strong { color: #818cf8; }
        header { background: rgba(255,255,255,0.97); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; backdrop-filter: blur(8px); }
        .nav-wrap { max-width: 1260px; margin: 0 auto; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
        .brand { font-size: 1.45rem; font-weight: 900; color: var(--navy); text-decoration: none; letter-spacing: -0.5px; }
        .brand span { color: var(--indigo); }
        .nav-links { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
        .nav-link { color: var(--navy); text-decoration: none; font-size: 0.9rem; font-weight: 600; padding: 6px 10px; border-radius: 6px; }
        .nav-link:hover { background: var(--surface); color: var(--indigo); }
        .mega-dropdown { position: relative; display: inline-block; }
        .mega-menu { display: none; position: absolute; right: 0; top: 100%; width: 920px; max-width: 94vw; background: #fff; border: 1px solid var(--border); border-radius: 14px; box-shadow: 0 22px 40px rgba(15,23,42,0.16); padding: 22px; grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); gap: 16px; z-index: 200; }
        .mega-dropdown:hover .mega-menu { display: grid; }
        .mega-col h4 { font-size: 0.83rem; color: var(--indigo-dark); margin-bottom: 6px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
        .mega-col a { display: block; color: var(--slate); text-decoration: none; font-size: 0.78rem; padding: 3px 0; }
        .mega-col a:hover { color: var(--indigo); font-weight: 600; }
        .container { max-width: 1260px; margin: 36px auto; padding: 0 20px; }
        .btn-amz { display: inline-block; background: var(--indigo); color: #ffffff; font-weight: 700; text-decoration: none; padding: 11px 18px; border-radius: 8px; font-size: 0.86rem; text-align: center; transition: background 0.15s; }
        .btn-amz:hover { background: var(--indigo-dark); }
        .btn-outline { display: inline-block; background: #fff; color: var(--navy); border: 1px solid var(--border); font-weight: 600; text-decoration: none; padding: 10px 14px; border-radius: 8px; font-size: 0.84rem; text-align: center; }
        .btn-outline:hover { border-color: var(--indigo); color: var(--indigo); }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 22px; }
        .card { background: #fff; border: 1px solid var(--border); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.15s, box-shadow 0.15s; }
        .card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(15,23,42,0.07); border-color: #cbd5e1; }
        .card-img { width: 100%; height: 190px; object-fit: cover; background: #f1f5f9; border-bottom: 1px solid var(--border); }
        .card-body { padding: 20px; display: flex; flex-direction: column; flex: 1; justify-content: space-between; }
        .pill { display: inline-block; background: var(--indigo-light); color: var(--indigo-dark); font-size: 0.73rem; font-weight: 700; padding: 4px 10px; border-radius: 999px; margin-bottom: 8px; width: fit-content; }
        .micro-disclosure { font-size: 0.72rem; color: #64748b; margin: 10px 0 6px; }
        footer { background: var(--surface); border-top: 1px solid var(--border); margin-top: 70px; padding: 48px 20px; color: var(--slate); font-size: 0.84rem; }
        .footer-inner { max-width: 1260px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 28px; }
        .footer-inner h4 { color: var(--navy); margin-bottom: 10px; font-size: 0.94rem; }
        .footer-inner a { display: block; color: var(--slate); text-decoration: none; padding: 3px 0; }
        .footer-inner a:hover { color: var(--indigo); }
    """


def build_header_html() -> str:
    mega_cols = ""
    for cat in TAXONOMY:
        sub_links = "".join(
            f'<a href="{SITE_URL}/categories/{sub["slug"]}.html">&rsaquo; {sub["name"]}</a>'
            for sub in cat["subcategories"]
        )
        mega_cols += f"""
        <div class="mega-col">
            <h4><a href="{SITE_URL}/categories/{cat['cat_slug']}.html" style="color:var(--indigo-dark);font-size:0.84rem;">{cat['icon']} {cat['category']}</a></h4>
            {sub_links}
        </div>
        """

    return f"""
    <div class="compliance-bar">
        <strong>AFFILIATE DISCLOSURE:</strong> As an Amazon Associate I earn from qualifying purchases. Stock imagery provided via Openverse &amp; Wikimedia Commons Public APIs.
    </div>
    <header>
        <div class="nav-wrap">
            <a href="{SITE_URL}/" class="brand">🌐 Omni<span>Prime10</span> US</a>
            <nav class="nav-links">
                <a href="{SITE_URL}/" class="nav-link">Storefront</a>
                <div class="mega-dropdown">
                    <a href="#departments" class="nav-link">10 Best-Seller Categories &#9662;</a>
                    <div class="mega-menu">
                        {mega_cols}
                    </div>
                </div>
                <a href="{SITE_URL}/#featured" class="nav-link">Featured Picks</a>
                <a href="{SITE_URL}/#reviews" class="nav-link">12H Buying Guides</a>
                <a href="{SITE_URL}/legal.html" class="nav-link">Policies</a>
            </nav>
        </div>
    </header>
    """


def build_footer_html(today: str) -> str:
    cat_links_1 = "".join(
        f'<a href="{SITE_URL}/categories/{c["cat_slug"]}.html">{c["icon"]} {c["category"]}</a>'
        for c in TAXONOMY[:5]
    )
    cat_links_2 = "".join(
        f'<a href="{SITE_URL}/categories/{c["cat_slug"]}.html">{c["icon"]} {c["category"]}</a>'
        for c in TAXONOMY[5:]
    )
    return f"""
    <footer>
        <div class="footer-inner">
            <div>
                <h4>OmniPrime10 US Storefront</h4>
                <p>Independent US buying-guide and product discovery platform covering Amazon's 10 best-selling consumer departments. Updated automatically every 12 hours.</p>
                <p style="margin-top:10px;font-weight:700;color:var(--navy);">As an Amazon Associate I earn from qualifying purchases.</p>
            </div>
            <div>
                <h4>Departments (1–5)</h4>
                {cat_links_1}
            </div>
            <div>
                <h4>Departments (6–10)</h4>
                {cat_links_2}
            </div>
            <div>
                <h4>Compliance & Feeds</h4>
                <a href="{SITE_URL}/legal.html#disclosure">Amazon Affiliate Disclosure</a>
                <a href="{SITE_URL}/legal.html#privacy">Privacy Policy</a>
                <a href="{SITE_URL}/legal.html#terms">Terms of Use</a>
                <a href="{SITE_URL}/sitemap.xml">XML Sitemap</a>
                <a href="{SITE_URL}/feed.xml">RSS 2.0 WebSub Feed</a>
            </div>
        </div>
        <div style="max-width:1260px;margin:28px auto 0;padding-top:20px;border-top:1px solid var(--border);text-align:center;font-size:0.78rem;">
            &copy; {today[:4]} OmniPrime10 US. Not operated, endorsed, or sponsored by Amazon.com, Inc. Last 12-Hour Automated Build: {today}.
        </div>
    </footer>
    """


def render_product_page(prod: dict, related: list, today: str) -> str:
    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    page_url = f"{SITE_URL}/products/{prod['slug']}.html"
    amz_url = make_amazon_url(prod["search_query"])

    specs_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in prod["specs"].items())
    pros_html = "".join(f"<li style='margin-bottom:6px;color:#065f46;'>&#10004; {p}</li>" for p in prod["pros"])
    cons_html = "".join(f"<li style='margin-bottom:6px;color:#991b1b;'>&#9888; {c}</li>" for c in prod["cons"])

    rel_cards = ""
    for r in related[:3]:
        if r["slug"] == prod["slug"]:
            continue
        r_amz = make_amazon_url(r["search_query"])
        rel_cards += f"""
        <div class="card">
            <img src="{r['image_url']}" alt="{r['name']}" class="card-img" loading="lazy">
            <div class="card-body">
                <div>
                    <span class="pill">{r['subcategory']}</span>
                    <h3 style="font-size:1.05rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{r['slug']}.html" style="color:var(--navy);text-decoration:none;">{r['name']}</a></h3>
                    <p style="font-size:0.85rem;color:var(--slate);">{r['summary']}</p>
                </div>
                <div style="margin-top:14px;">
                    <a href="{r_amz}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="width:100%;">Check Price on Amazon &rarr;</a>
                </div>
            </div>
        </div>
        """

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Who should buy the {prod['name']}?",
                "acceptedAnswer": {"@type": "Answer", "text": prod["buy_if"]}
            },
            {
                "@type": "Question",
                "name": f"Who should skip the {prod['name']}?",
                "acceptedAnswer": {"@type": "Answer", "text": prod["skip_if"]}
            }
        ]
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prod['name']} Review, Specs & Buying Guide | OmniPrime10 US</title>
    <meta name="description" content="{prod['summary']} Compare verified specifications, pros, cons, and check live price on Amazon.">
    <link rel="canonical" href="{page_url}">
    <script type="application/ld+json">{json.dumps(faq_schema)}</script>
    <style>
        {get_common_styles()}
        .hero-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 32px; display: grid; grid-template-columns: 360px 1fr; gap: 28px; align-items: center; }}
        .hero-img {{ width: 100%; height: 260px; object-fit: cover; border-radius: 12px; border: 1px solid var(--border); }}
        .spec-table {{ width: 100%; border-collapse: collapse; margin: 20px 0 32px; }}
        .spec-table th, .spec-table td {{ border: 1px solid var(--border); padding: 12px 16px; text-align: left; font-size: 0.92rem; }}
        .spec-table th {{ background: var(--surface); width: 34%; }}
        .verdict-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 20px; margin: 24px 0; }}
        .v-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 22px; }}
        @media (max-width: 780px) {{ .hero-box {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <div style="font-size:0.84rem;color:var(--slate);margin-bottom:16px;">
            <a href="{SITE_URL}/" style="color:var(--indigo);text-decoration:none;font-weight:600;">Home</a> &rsaquo;
            <a href="{SITE_URL}/categories/{prod['cat_slug']}.html" style="color:var(--indigo);text-decoration:none;font-weight:600;">{prod['category']}</a> &rsaquo;
            <a href="{SITE_URL}/categories/{prod['sub_slug']}.html" style="color:var(--indigo);text-decoration:none;font-weight:600;">{prod['subcategory']}</a> &rsaquo;
            <span>{prod['name']}</span>
        </div>

        <section class="hero-box">
            <div>
                <img src="{prod['image_url']}" alt="{prod['name']}" class="hero-img">
                <div style="font-size:0.7rem;color:#64748b;margin-top:4px;text-align:center;">Illustrative Category Photo: {prod['image_credit']}</div>
            </div>
            <div>
                <span class="pill">{prod['cat_icon']} {prod['subcategory']} &bull; Amazon Best-Seller Pick</span>
                <h1 style="font-size:1.9rem;line-height:1.25;margin-bottom:10px;">{prod['name']}</h1>
                <p style="color:var(--slate);margin-bottom:14px;">{prod['summary']}</p>
                <div class="micro-disclosure">Affiliate Disclosure: As an Amazon Associate I earn from qualifying purchases.</div>
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;">
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz">Check Price on Amazon &rarr;</a>
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-outline">View on Amazon</a>
                </div>
            </div>
        </section>

        <div class="verdict-grid">
            <div class="v-box">
                <h3 style="color:#047857;margin-bottom:8px;">Who Should Buy This</h3>
                <p style="font-size:0.93rem;color:var(--slate);">{prod['buy_if']}</p>
            </div>
            <div class="v-box">
                <h3 style="color:#b91c1c;margin-bottom:8px;">Who Should Skip This</h3>
                <p style="font-size:0.93rem;color:var(--slate);">{prod['skip_if']}</p>
            </div>
        </div>

        <h2 style="font-size:1.4rem;margin-top:30px;">Verified Technical Specifications</h2>
        <table class="spec-table">
            <tbody>{specs_rows}</tbody>
        </table>

        <div class="verdict-grid">
            <div class="v-box">
                <h3 style="margin-bottom:10px;">Key Strengths (Pros)</h3>
                <ul style="list-style:none;">{pros_html}</ul>
            </div>
            <div class="v-box">
                <h3 style="margin-bottom:10px;">Considerations (Cons)</h3>
                <ul style="list-style:none;">{cons_html}</ul>
            </div>
        </div>

        <h2 style="font-size:1.4rem;margin:40px 0 18px;">Related Best-Selling Picks</h2>
        <div class="grid-3">{rel_cards}</div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""

    with open(os.path.join(PRODUCTS_DIR, f"{prod['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return page_url


def render_review_article(group: list, cycle_num: int, art_idx: int, today: str) -> dict:
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    sub = group[0]["subcategory"]
    cat = group[0]["category"]
    slug = f"best-{slugify(sub)}-review-comparison-c{cycle_num}-{art_idx}"
    title = f"Top 4 Best-Selling {sub} & Buying Guide ({today[:4]} Review)"
    page_url = f"{SITE_URL}/reviews/{slug}.html"
    cover_img = group[0]["image_url"]

    th_cols = "".join(f"<th>{p['name']}</th>" for p in group)
    spec_keys = list(group[0]["specs"].keys())
    matrix_rows = ""
    for k in spec_keys:
        tds = "".join(f"<td>{p['specs'].get(k, 'Verified')}</td>" for p in group)
        matrix_rows += f"<tr><th>{k}</th>{tds}</tr>"

    cta_tds = "".join(
        f'<td><a href="{make_amazon_url(p["search_query"])}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="padding:8px 12px;font-size:0.8rem;">Check Price on Amazon</a></td>'
        for p in group
    )

    sections_html = ""
    for rank, p in enumerate(group, 1):
        amz_url = make_amazon_url(p["search_query"])
        sections_html += f"""
        <section style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:24px;display:grid;grid-template-columns:220px 1fr;gap:22px;align-items:center;">
            <img src="{p['image_url']}" alt="{p['name']}" style="width:100%;height:160px;object-fit:cover;border-radius:10px;border:1px solid var(--border);" loading="lazy">
            <div>
                <span class="pill">Top Pick #{rank} &bull; {p['brand']}</span>
                <h2 style="font-size:1.3rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h2>
                <p style="color:var(--slate);margin-bottom:8px;font-size:0.92rem;">{p['summary']}</p>
                <p style="font-size:0.88rem;margin-bottom:6px;"><strong>Best For:</strong> {p['buy_if']}</p>
                <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz">Check Price on Amazon &rarr;</a>
                    <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Full Spec Sheet</a>
                </div>
            </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | OmniPrime10 US</title>
    <meta name="description" content="Side-by-side specification review and buyer's guide comparing {', '.join(p['name'] for p in group)}.">
    <link rel="canonical" href="{page_url}">
    <style>
        {get_common_styles()}
        .table-scroll {{ overflow-x: auto; margin: 26px 0 36px; }}
        table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
        th, td {{ border: 1px solid var(--border); padding: 12px 14px; text-align: left; font-size: 0.88rem; }}
        th {{ background: var(--surface); color: var(--navy); }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <span class="pill">{cat} &rsaquo; 12-Hour Editorial Review</span>
        <h1 style="font-size:2rem;margin-bottom:12px;">{title}</h1>
        <p style="color:var(--slate);max-width:860px;margin-bottom:22px;">Comparing top-selling {sub.lower()} requires looking closely at verified build materials, durability ratings, and real-world household suitability. Explore our side-by-side matrix and detailed model breakdowns below.</p>

        <div class="table-scroll">
            <table>
                <thead>
                    <tr><th>Specification</th>{th_cols}</tr>
                </thead>
                <tbody>
                    {matrix_rows}
                    <tr><th>Amazon Availability</th>{cta_tds}</tr>
                </tbody>
            </table>
        </div>

        {sections_html}
    </main>
    {build_footer_html(today)}
</body>
</html>"""

    with open(os.path.join(REVIEWS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "slug": slug,
        "title": title,
        "category": cat,
        "subcategory": sub,
        "image_url": cover_img,
        "excerpt": f"Side-by-side comparison of {group[0]['name']}, {group[1]['name']}, and 2 more best-selling picks.",
        "published_at": today,
        "url": page_url
    }


def render_category_and_subcategory_pages(published_prods: list, today: str) -> list:
    os.makedirs(CATEGORIES_DIR, exist_ok=True)
    cat_urls = []

    def write_listing(slug: str, heading: str, desc: str, items: list):
        cards = ""
        for p in items[:36]:
            amz_url = make_amazon_url(p["search_query"])
            cards += f"""
            <article class="card">
                <img src="{p['image_url']}" alt="{p['name']}" class="card-img" loading="lazy">
                <div class="card-body">
                    <div>
                        <span class="pill">{p['cat_icon']} {p['subcategory']}</span>
                        <h3 style="font-size:1.06rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h3>
                        <p style="font-size:0.86rem;color:var(--slate);margin-bottom:10px;">{p['summary']}</p>
                    </div>
                    <div>
                        <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
                        <div style="display:flex;gap:8px;">
                            <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="flex:1;">Check Price on Amazon</a>
                            <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Review</a>
                        </div>
                    </div>
                </div>
            </article>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{heading} — Best-Selling Buying Guides | OmniPrime10 US</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{SITE_URL}/categories/{slug}.html">
    <style>{get_common_styles()}</style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <h1 style="font-size:2rem;margin-bottom:8px;">{heading}</h1>
        <p style="color:var(--slate);margin-bottom:28px;">{desc}</p>
        <div class="grid-3">{cards or '<p>Products in this subcategory will populate in the next 12-hour automated cycle.</p>'}</div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""
        with open(os.path.join(CATEGORIES_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        cat_urls.append(f"{SITE_URL}/categories/{slug}.html")

    for cat in TAXONOMY:
        c_items = [p for p in published_prods if p["cat_slug"] == cat["cat_slug"]]
        write_listing(
            cat["cat_slug"],
            f"{cat['icon']} {cat['category']}",
            f"Compare verified specifications and Amazon best-seller links across {', '.join(s['name'] for s in cat['subcategories'])}.",
            c_items
        )
        for sub in cat["subcategories"]:
            s_items = [p for p in published_prods if p["sub_slug"] == sub["slug"]]
            write_listing(
                sub["slug"],
                f"{sub['name']} ({cat['category']})",
                f"Top-rated {sub['name'].lower()} compared side-by-side for US buyers.",
                s_items
            )

    return cat_urls


def render_legal_page(today: str):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Affiliate Disclosure, Privacy Policy & Terms | OmniPrime10 US</title>
    <link rel="canonical" href="{SITE_URL}/legal.html">
    <style>
        {get_common_styles()}
        .legal-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 26px; margin-bottom: 22px; }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <div class="legal-box" id="disclosure">
            <h2>Amazon Associates Program Disclosure</h2>
            <p style="margin-top:8px;"><strong>As an Amazon Associate I earn from qualifying purchases.</strong></p>
            <p style="margin-top:8px;color:var(--slate);">OmniPrime10 US is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. Category photography is sourced from public Creative Commons APIs (Openverse &amp; Wikimedia Commons) for illustrative editorial purposes.</p>
        </div>
        <div class="legal-box" id="privacy">
            <h2>Privacy Policy</h2>
            <p style="margin-top:8px;color:var(--slate);">We do not collect personal payment details or process direct checkouts. Clicking "Check Price on Amazon" redirects you securely to Amazon.com.</p>
        </div>
        <div class="legal-box" id="terms">
            <h2>Terms of Use</h2>
            <p style="margin-top:8px;color:var(--slate);">All product specifications are compiled for comparative buying guidance. Always confirm current pricing, stock availability, and manufacturer warranty terms directly on Amazon.com.</p>
        </div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""
    with open(os.path.join(DOCS_DIR, "legal.html"), "w", encoding="utf-8") as f:
        f.write(html)


def render_storefront_homepage(published_prods: list, reviews: list, today: str):
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    latest_prods = list(reversed(published_prods))[:48]
    latest_revs = list(reversed(reviews))[:12]

    cat_tiles = ""
    for c in TAXONOMY:
        subs = " &bull; ".join(s["name"] for s in c["subcategories"])
        cat_tiles += f"""
        <a href="{SITE_URL}/categories/{c['cat_slug']}.html" class="card" style="text-decoration:none;color:inherit;">
            <div class="card-body">
                <div>
                    <div style="font-size:2rem;margin-bottom:8px;">{c['icon']}</div>
                    <h3 style="font-size:1.08rem;color:var(--navy);margin-bottom:6px;">{c['category']}</h3>
                    <p style="font-size:0.82rem;color:var(--slate);">{subs}</p>
                </div>
                <span style="margin-top:14px;font-size:0.84rem;font-weight:700;color:var(--indigo);">Shop Department &rarr;</span>
            </div>
        </a>
        """

    prod_cards = ""
    for p in latest_prods:
        amz_url = make_amazon_url(p["search_query"])
        prod_cards += f"""
        <article class="card prod-card" data-cat="{p['cat_slug']}">
            <img src="{p['image_url']}" alt="{p['name']}" class="card-img" loading="lazy">
            <div class="card-body">
                <div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <span class="pill" style="margin:0;">{p['cat_icon']} {p['subcategory']}</span>
                        <span style="font-size:0.74rem;font-weight:700;color:var(--amber);">★ Top Pick</span>
                    </div>
                    <h3 style="font-size:1.06rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h3>
                    <p style="font-size:0.85rem;color:var(--slate);margin-bottom:10px;">{p['summary']}</p>
                </div>
                <div>
                    <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
                    <div style="display:flex;gap:8px;">
                        <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="flex:1;">Check Price on Amazon</a>
                        <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Specs</a>
                    </div>
                </div>
            </div>
        </article>
        """

    rev_cards = ""
    for r in latest_revs:
        rev_cards += f"""
        <article class="card">
            <img src="{r['image_url']}" alt="{r['title']}" class="card-img" loading="lazy">
            <div class="card-body">
                <div>
                    <span class="pill">{r['category']}</span>
                    <h3 style="font-size:1.08rem;margin-bottom:8px;"><a href="{SITE_URL}/reviews/{r['slug']}.html" style="color:var(--navy);text-decoration:none;">{r['title']}</a></h3>
                    <p style="font-size:0.85rem;color:var(--slate);">{r['excerpt']}</p>
                </div>
                <div style="margin-top:14px;">
                    <a href="{SITE_URL}/reviews/{r['slug']}.html" class="btn-outline" style="width:100%;">Read 4-Product Review &rarr;</a>
                </div>
            </div>
        </article>
        """

    filter_btns = '<button class="f-btn active" onclick="filterDept(\'all\', this)">All 10 Departments</button>'
    for c in TAXONOMY:
        filter_btns += f'<button class="f-btn" onclick="filterDept(\'{c["cat_slug"]}\', this)">{c["icon"]} {c["category"]}</button>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmniPrime10 US — Top 10 Amazon Best-Seller Departments & Buying Guides</title>
    <meta name="description" content="Explore verified product reviews and side-by-side buying guides across Amazon's 10 best-selling categories: Smart Home, Pet Tech, Outdoor Gear, Fitness, Auto Tools, Audio, Baby, Power Tools, Luggage & Coffee.">
    <link rel="canonical" href="{SITE_URL}/">
    <style>
        {get_common_styles()}
        .hero-banner {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: #ffffff; padding: 56px 20px; }}
        .hero-inner {{ max-width: 1260px; margin: 0 auto; display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 32px; align-items: center; }}
        .hero-badge {{ display: inline-block; background: rgba(129,140,248,0.2); border: 1px solid #818cf8; color: #c7d2fe; font-size: 0.78rem; font-weight: 700; padding: 5px 12px; border-radius: 999px; margin-bottom: 14px; }}
        .hero-banner h1 {{ font-size: 2.35rem; line-height: 1.2; margin-bottom: 14px; }}
        .search-bar {{ display: flex; gap: 10px; margin-top: 22px; max-width: 620px; }}
        .search-bar input {{ flex: 1; padding: 14px 18px; border-radius: 10px; border: none; font-size: 1rem; outline: none; }}
        .filter-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 22px 0; }}
        .f-btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--navy); padding: 7px 13px; border-radius: 999px; font-size: 0.82rem; font-weight: 600; cursor: pointer; }}
        .f-btn.active, .f-btn:hover {{ background: var(--indigo); color: #fff; border-color: var(--indigo); }}
        .sec-head {{ display: flex; justify-content: space-between; align-items: baseline; margin: 46px 0 20px; border-bottom: 2px solid var(--border); padding-bottom: 10px; flex-wrap: wrap; gap: 10px; }}
        @media (max-width: 820px) {{ .hero-inner {{ grid-template-columns: 1fr; }} .hero-banner h1 {{ font-size: 1.85rem; }} }}
    </style>
</head>
<body>
    {build_header_html()}
    <section class="hero-banner">
        <div class="hero-inner">
            <div>
                <span class="hero-badge">10 BEST-SELLING DEPARTMENTS &bull; AUTO-UPDATED EVERY 12 HOURS</span>
                <h1>The Complete US Buying-Guide Storefront Across 10 Top-Selling Categories</h1>
                <p style="color:#e0e7ff;font-size:1.04rem;">Compare verified specifications across Smart Home Security, Automated Pet Care, Backcountry Camping, Home Gym Fitness, Automotive Diagnostics, Creator Audio, Baby Essentials, Power Tools, Travel Luggage & Specialty Coffee.</p>
                <div class="search-bar">
                    <input type="text" id="liveSearch" placeholder="Search across all 10 departments (e.g. eufy, Litter-Robot, YETI, Bowflex, Shure, Samsonite)..." onkeyup="runSearch()">
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.2);border-radius:16px;padding:24px;">
                <div style="font-size:0.78rem;color:#c7d2fe;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Storefront Inventory</div>
                <div style="font-size:1.6rem;font-weight:900;margin-bottom:4px;">{len(published_prods)} Active Products</div>
                <div style="font-size:0.9rem;color:#e0e7ff;margin-bottom:14px;">{len(reviews)} Comparative Review Guides</div>
                <a href="#featured" class="btn-amz" style="width:100%;background:#6366f1;">Explore Featured Best-Sellers &darr;</a>
            </div>
        </div>
    </section>

    <main class="container">
        <div class="sec-head" id="departments">
            <h2>Browse All 10 Best-Selling Amazon Departments</h2>
            <span style="font-size:0.85rem;color:var(--slate);">10 Flagship Categories &bull; 30 Specialized Subcategories</span>
        </div>
        <div class="grid-3">{cat_tiles}</div>

        <div class="sec-head" id="featured">
            <h2>Featured Best-Selling Products</h2>
            <span style="font-size:0.85rem;color:var(--slate);">+20 New Products Published Every 12 Hours</span>
        </div>
        <div class="filter-row">{filter_btns}</div>
        <div class="grid-3" id="productsContainer">{prod_cards}</div>

        <div class="sec-head" id="reviews">
            <h2>Latest 12-Hour Comparative Review Articles</h2>
            <span style="font-size:0.85rem;color:var(--slate);">+5 New 4-Model Buying Guides Every 12 Hours</span>
        </div>
        <div class="grid-3">{rev_cards}</div>
    </main>

    {build_footer_html(today)}
    <script>
        function runSearch() {{
            const q = document.getElementById('liveSearch').value.toLowerCase();
            document.querySelectorAll('.prod-card').forEach(card => {{
                card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
            }});
        }}
        function filterDept(catSlug, btn) {{
            document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.prod-card').forEach(card => {{
                if (catSlug === 'all' || card.getAttribute('data-cat') === catSlug) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def build_seo_feeds_and_ping_all_engines(published_prods: list, reviews: list, cat_urls: list, new_urls: list, today: str):
    # 1. Sitemap XML
    urls_xml = f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>\n"
    urls_xml += f"  <url><loc>{SITE_URL}/legal.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>\n"

    for c_url in cat_urls:
        urls_xml += f"  <url><loc>{c_url}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n"
    for r in reviews:
        urls_xml += f"  <url><loc>{r['url']}</loc><lastmod>{r['published_at']}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>\n"
    for p in published_prods:
        urls_xml += f"  <url><loc>{SITE_URL}/products/{p['slug']}.html</loc><lastmod>{p.get('published_at', today)}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"

    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>'
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # 2. RSS 2.0 Feed dengan Google PubSubHubbub / WebSub Hub
    rss_items = ""
    for r in list(reversed(reviews))[:15]:
        rss_items += f"""    <item>
      <title>{r['title']}</title>
      <link>{r['url']}</link>
      <guid>{r['url']}</guid>
      <description>{r['excerpt']}</description>
    </item>\n"""
    for p in list(reversed(published_prods))[:25]:
        p_url = f"{SITE_URL}/products/{p['slug']}.html"
        rss_items += f"""    <item>
      <title>{p['name']}</title>
      <link>{p_url}</link>
      <guid>{p_url}</guid>
      <description>{p['summary']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>OmniPrime10 US — 10-Department Amazon Best-Seller Storefront</title>
    <link>{SITE_URL}/</link>
    <description>Automated 12-Hour Product Reviews &amp; Buying Guides Across 10 Top Categories</description>
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{rss_items}  </channel>
</rss>"""
    with open(os.path.join(DOCS_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    # 3. robots.txt & file verifikasi IndexNow
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

    if "username.github.io" in SITE_URL or not new_urls:
        return

    # 4. Ping IndexNow API (Otomatis mendaftarkan URL ke Bing, Yahoo, DuckDuckGo, Yandex, Naver, Seznam)
    host = SITE_URL.replace("https://", "").replace("http://", "").split("/")[0]
    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls[:100]
    }
    for endpoint in ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow", "https://yandex.com/indexnow"]:
        try:
            r = requests.post(endpoint, json=payload, timeout=12)
            print(f"[SEO] IndexNow Ping ({endpoint}) Status: {r.status_code}")
        except Exception as e:
            print(f"[WARN] IndexNow Ping gagal ({endpoint}): {e}")

    # 5. Ping Google WebSub / PubSubHubbub Hub
    try:
        r_google = requests.post(
            "https://pubsubhubbub.appspot.com/",
            data={"hub.mode": "publish", "hub.url": f"{SITE_URL}/feed.xml"},
            timeout=12
        )
        print(f"[SEO] Google WebSub Ping Status: {r_google.status_code}")
    except Exception as e:
        print(f"[WARN] Google WebSub Ping gagal: {e}")


def main():
    state = init_or_load_state()
    img_cache = load_image_cache()
    products = state["products"]
    reviews = state["reviews"]
    cycle = state.get("cycle_count", 0) + 1
    state["cycle_count"] = cycle
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    unpublished = [p for p in products if not p.get("published")]
    if len(unpublished) < 20:
        for p in products:
            p["published"] = False
        unpublished = products

    batch_20 = unpublished[:20]
    new_urls = [f"{SITE_URL}/"]

    # Ambil gambar stok gratis via API publik (Openverse / Wikimedia Commons) untuk 20 produk baru
    for p in batch_20:
        if not p.get("image_url"):
            img_info = fetch_free_stock_image(p["img_q"], p["idx"], img_cache)
            p["image_url"] = img_info["url"]
            p["image_credit"] = img_info["credit"]
            time.sleep(0.2)
        p["published"] = True
        p["published_at"] = today

    save_image_cache(img_cache)
    published_prods = [p for p in products if p.get("published")]

    # Pastikan semua produk terpublikasi memiliki gambar valid
    for p in published_prods:
        if not p.get("image_url"):
            img_info = fetch_free_stock_image(p["img_q"], p["idx"], img_cache)
            p["image_url"] = img_info["url"]
            p["image_credit"] = img_info["credit"]

    for p in published_prods:
        same_cat = [x for x in published_prods if x["cat_slug"] == p["cat_slug"]]
        url = render_product_page(p, same_cat, today)
        if p in batch_20:
            new_urls.append(url)

    # Buat 5 artikel review komparatif baru setiap 12 jam (masing-masing membandingkan 4 produk)
    for i in range(0, len(batch_20), 4):
        group = batch_20[i:i + 4]
        if len(group) == 4:
            rev_meta = render_review_article(group, cycle, (i // 4) + 1, today)
            reviews.append(rev_meta)
            new_urls.append(rev_meta["url"])

    cat_urls = render_category_and_subcategory_pages(published_prods, today)
    render_legal_page(today)
    render_storefront_homepage(published_prods, reviews, today)

    save_state(state)
    build_seo_feeds_and_ping_all_engines(published_prods, reviews, cat_urls, new_urls, today)

    print(f"[DONE] Siklus #{cycle}: +20 Produk (10 Kategori) & +5 Artikel Review berhasil dipublikasikan beserta gambar stok API publik dan didaftarkan ke IndexNow & Google WebSub.")


if __name__ == "__main__":
    main()

import logging
import uuid
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.crop import Crop
from app.models.crop_stage import CropCultivationStage
from app.models.enums import CropCategoryEnum

logger = logging.getLogger("agri_smart.seeds.crop_stages")

ONION_STAGES: List[Dict[str, Any]] = [
    {
        "stage_order": 1,
        "stage_name": "Land Preparation & Deep Tillage / நில உழவு & சால் பிடித்தல்",
        "stage_name_local": "நில உழவு & சால் பிடித்தல்",
        "description": "Deep disc ploughing (2 times), rotavator fine tilth leveling, ridge & furrow bed formation, and farmyard manure (FYM) basal mixing.",
        "duration_days": 10,
        "visual_asset_type": "TILLAGE",
        "visual_theme_color": "#854d0e",
        "recommended_activities": [
            "Primary disc ploughing & clod crushing",
            "Rotavator fine tilth pulverization",
            "Ridge & furrow formation (45cm width)",
            "Farmyard Manure (FYM 10-15 tonnes/acre) & Neem cake incorporation"
        ],
        "recommended_inputs": ["Farmyard Manure (FYM)", "Neem Cake", "Trichoderma viride"],
        "is_active": True
    },
    {
        "stage_order": 2,
        "stage_name": "Seed Selection & Sowing / விதை வெங்காய நடவு",
        "stage_name_local": "விதை வெங்காய நடவு",
        "description": "Certified medium-sized seed bulbs selection (e.g. CO 4 / Bellary / Small Onion). Seed slurry treatment with bio-fungicide and manual line planting.",
        "duration_days": 8,
        "visual_asset_type": "SEED",
        "visual_theme_color": "#10b981",
        "recommended_activities": [
            "Germination and seed quality check",
            "Seed bulb dipping in Trichoderma slurry",
            "Line planting at 15cm x 10cm spacing on ridges",
            "Immediate life irrigation on the same day"
        ],
        "recommended_inputs": ["Certified Onion Seed Bulbs", "Trichoderma viride", "Pseudomonas"],
        "is_active": True
    },
    {
        "stage_order": 3,
        "stage_name": "Weeding & Soil Aeration / பில்லு புடுங்குறது (களை எடுத்தல்)",
        "stage_name_local": "பில்லு புடுங்குறது (களை எடுத்தல்)",
        "description": "First and second manual hand weeding, light soil loosening around roots, and irrigation scheduling to prevent weed competition.",
        "duration_days": 25,
        "visual_asset_type": "WEEDING",
        "visual_theme_color": "#16a34a",
        "recommended_activities": [
            "First manual hand weeding at 20-25 days after planting",
            "Light hoeing around plant root zone for aeration",
            "Removal of stray grass and broadleaf weeds"
        ],
        "recommended_inputs": ["Hand Weeding Tools"],
        "is_active": True
    },
    {
        "stage_order": 4,
        "stage_name": "Fertilization & Spraying / உரம் & மருந்து தெளித்தல்",
        "stage_name_local": "உரம் & மருந்து தெளித்தல்",
        "description": "Split Nitrogen & Potassium top dressing, foliar micronutrient spray (Zinc + Boron), and prophylactic spray for purple blotch and thrips.",
        "duration_days": 30,
        "visual_asset_type": "VEGETATIVE",
        "visual_theme_color": "#3b82f6",
        "recommended_activities": [
            "Split application of Urea and Potash (MOP)",
            "Foliar micronutrient spray (Zinc + Boron mixture)",
            "Neem oil / bio-pesticide spray for thrips prevention",
            "Installation of yellow & blue sticky traps"
        ],
        "recommended_inputs": ["Urea", "MOP (Potash)", "Micronutrient Mixture", "Neem Oil 10000ppm"],
        "is_active": True
    },
    {
        "stage_order": 5,
        "stage_name": "Bulb Formation & Earthing Up / வெங்காய குமிழ் உருவாக்கம்",
        "stage_name_local": "வெங்காய குமிழ் உருவாக்கம்",
        "description": "Energy translocation to bulb swelling. Potassium fertigation (0:0:50) for bulb density and careful furrow irrigation management.",
        "duration_days": 25,
        "visual_asset_type": "BULB_FORMATION",
        "visual_theme_color": "#e11d48",
        "recommended_activities": [
            "Potassium sulfate (0:0:50) fertigation for solid bulb formation",
            "Controlled furrow irrigation at 5-6 day intervals",
            "Soil earthing up to keep bulbs covered"
        ],
        "recommended_inputs": ["Sulfate of Potash (0:0:50)", "Hexaconazole / Mancozeb"],
        "is_active": True
    },
    {
        "stage_order": 6,
        "stage_name": "Maturity & Neck-Fall / முதிர்ச்சி நிலை & கழுத்து மடிவு",
        "stage_name_local": "முதிர்ச்சி நிலை & கழுத்து மடிவு",
        "description": "Natural neck fall (50-70%) indicating bulb maturity. Complete stoppage of irrigation 10-12 days prior to harvest for firm skin curing.",
        "duration_days": 12,
        "visual_asset_type": "MATURITY",
        "visual_theme_color": "#d97706",
        "recommended_activities": [
            "Completely stop irrigation 12 days before harvest",
            "Neck fall percentage inspection (>60%)",
            "Outer scale firmness check"
        ],
        "recommended_inputs": [],
        "is_active": True
    },
    {
        "stage_order": 7,
        "stage_name": "Harvesting & Windrow Curing / பிடுங்குதல் & தாள் அடித்தல்",
        "stage_name_local": "பிடுங்குதல் & தாள் அடித்தல்",
        "description": "Manual bulb pulling in dry weather, windrow curing in shade for 3-4 days, and foliage detopping (தாள் அடித்தல்).",
        "duration_days": 7,
        "visual_asset_type": "HARVEST",
        "visual_theme_color": "#ca8a04",
        "recommended_activities": [
            "Manual pulling of bulbs in early morning hours",
            "Windrow shade curing for 3-4 days",
            "Neck foliage detopping leaving 2.5 cm collar"
        ],
        "recommended_inputs": [],
        "is_active": True
    },
    {
        "stage_order": 8,
        "stage_name": "Grading & Bagging / மூட்டை பிடித்தல் & விற்பனை",
        "stage_name_local": "மூட்டை பிடித்தல் & விற்பனை",
        "description": "Size grading into Grade A, Grade B, and seed quality. Packing into 50kg aerated mesh bags for marketplace trade or cold storage.",
        "duration_days": 5,
        "visual_asset_type": "YIELD_STORAGE",
        "visual_theme_color": "#0d9488",
        "recommended_activities": [
            "Cleaning loose papery scales and thick-necked bulbs",
            "Size grading into Grade A (>45mm) and Grade B",
            "Weighment & bagging into 50kg breathable red mesh bags",
            "Listing on Marketplace or Mandi dispatch"
        ],
        "recommended_inputs": ["Aerated Mesh Bags (50kg)", "Batch Barcode Tags"],
        "is_active": True
    },
]

GROUNDNUT_STAGES: List[Dict[str, Any]] = [
    {
        "stage_order": 1,
        "stage_name": "Land Preparation & Basal Manuring / நிலத் தயாரிப்பு & எரு இடுதல்",
        "stage_name_local": "நிலத் தயாரிப்பு & எரு இடுதல்",
        "description": "Deep ploughing (2-3 times) for loose, friable red soil tilth. Application of well-decomposed FYM (5-7 tonnes/acre) and gypsum basal application.",
        "duration_days": 10,
        "visual_asset_type": "TILLAGE",
        "visual_theme_color": "#854d0e",
        "recommended_activities": [
            "Primary mouldboard ploughing & secondary cultivator tilling",
            "Incorporation of FYM (5-7 tonnes/acre)",
            "Basal gypsum application (200 kg/acre) for pod calcium",
            "Leveling and forming broad bed furrows (BBF)"
        ],
        "recommended_inputs": ["Farmyard Manure (FYM)", "Agricultural Gypsum", "Trichoderma viride"],
        "is_active": True
    },
    {
        "stage_order": 2,
        "stage_name": "Seed Treatment & Sowing / விதை நேர்த்தி & விதைப்பு",
        "stage_name_local": "விதை நேர்த்தி & விதைப்பு",
        "description": "Certified high-yielding seeds (TMV 7 / VRI 2 / Kadiri 6). Seed treatment with Rhizobium and Trichoderma. Sowing at 30cm x 10cm spacing.",
        "duration_days": 8,
        "visual_asset_type": "SEED",
        "visual_theme_color": "#10b981",
        "recommended_activities": [
            "Seed treatment with Rhizobium culture & Trichoderma slurry",
            "Sowing at 30cm x 10cm spacing using seed drill or bullock plough",
            "Life irrigation on day 3 for uniform emergence"
        ],
        "recommended_inputs": ["Certified Groundnut Seeds (TMV/VRI)", "Rhizobium Bio-fertilizer", "Phosphobacteria"],
        "is_active": True
    },
    {
        "stage_order": 3,
        "stage_name": "Weeding & Earthing Up / களை எடுத்தல் & மண் அணைத்தல்",
        "stage_name_local": "களை எடுத்தல் & மண் அணைத்தல்",
        "description": "Manual hand weeding at 20 DAS followed by gypsum top dressing and earthing up (மண் அணைத்தல்) at 40-45 DAS before peg entry.",
        "duration_days": 30,
        "visual_asset_type": "WEEDING",
        "visual_theme_color": "#16a34a",
        "recommended_activities": [
            "First hand weeding at 20 days after sowing",
            "Gypsum top dressing (200 kg/acre) at 40-45 DAS",
            "Earthing up (மண் அணைத்தல்) to facilitate easy peg penetration into loose soil",
            "Strictly avoid disturbing soil after 45 DAS"
        ],
        "recommended_inputs": ["Agricultural Gypsum", "Hand Weeding Equipment"],
        "is_active": True
    },
    {
        "stage_order": 4,
        "stage_name": "Pegging & Pod Development / விழுது இறங்குதல் & காய் பிடித்தல்",
        "stage_name_local": "விழுது இறங்குதல் & காய் பிடித்தல்",
        "description": "Pegs penetrate soil and start forming pods. Critical irrigation period: adequate soil moisture needed without waterlogging.",
        "duration_days": 35,
        "visual_asset_type": "VEGETATIVE",
        "visual_theme_color": "#3b82f6",
        "recommended_activities": [
            "Maintain optimum soil moisture through sprinkler/furrow irrigation",
            "Foliar spray of DAP (2%) + Micronutrients for pod filling",
            "Monitoring for leaf spot (Tikka) and rust disease"
        ],
        "recommended_inputs": ["DAP Fertilizer", "Carbendazim / Mancozeb", "Micronutrient Mixture"],
        "is_active": True
    },
    {
        "stage_order": 5,
        "stage_name": "Maturity & Pod Check / முதிர்ச்சி நிலை & காய் முதிர்வு ஆய்வு",
        "stage_name_local": "முதிர்ச்சி நிலை & காய் முதிர்வு ஆய்வு",
        "description": "Inner pod shell turns dark brown/black. Leaves turn yellowish and start shedding, confirming harvest maturity.",
        "duration_days": 15,
        "visual_asset_type": "MATURITY",
        "visual_theme_color": "#d97706",
        "recommended_activities": [
            "Sample pod pull test: inner shell should show dark brownish-black netting",
            "Withhold irrigation 5-7 days before harvest",
            "Preparation of harvest labor and mechanical pod pullers"
        ],
        "recommended_inputs": [],
        "is_active": True
    },
    {
        "stage_order": 6,
        "stage_name": "Harvesting, Pod Stripping & Bagging / அறுவடை & காய் பறித்தல்",
        "stage_name_local": "அறுவடை & காய் பறித்தல்",
        "description": "Manual plant pulling in moist soil, pod stripping (காய் பறித்தல்) using mechanical thresher or hand stripping, sun drying pods to <9% moisture, and gunny bagging.",
        "duration_days": 10,
        "visual_asset_type": "HARVEST",
        "visual_theme_color": "#ca8a04",
        "recommended_activities": [
            "Manual plant pulling or tractor groundnut digger operation",
            "Pod stripping (காய் பறித்தல்) and separation of haulms (fodder)",
            "Sun drying pods for 4-5 days to 8-9% safe storage moisture",
            "Packing in 40kg gunny bags for oil extraction or seed sale"
        ],
        "recommended_inputs": ["Jute Gunny Bags (40kg)", "Moisture Meter", "Pod Stripper Machine"],
        "is_active": True
    },
]

TOMATO_STAGES: List[Dict[str, Any]] = [
    {
        "stage_order": 1,
        "stage_name": "Seed Priming & Pro-Tray Nursery / விதை நேர்த்தி & நாற்றுப் பண்ணை",
        "stage_name_local": "விதை நேர்த்தி & நாற்றுப் பண்ணை",
        "description": "High-germination hybrid seeds sown in 98-cell pro-trays with sterilized coco-peat and bio-fungicides under shade net shelter.",
        "duration_days": 25,
        "visual_asset_type": "NURSERY",
        "visual_theme_color": "#059669",
        "recommended_activities": [
            "Pro-tray filling with sterilized coco-peat and vermicompost",
            "Single seed sowing per cavity and micro-sprinkler misting",
            "Prophylactic bio-fungicide spray for damping-off"
        ],
        "recommended_inputs": ["Hybrid Tomato Seeds (Shivam/Abhinav)", "Coco-peat", "Trichoderma viride"],
        "is_active": True
    },
    {
        "stage_order": 2,
        "stage_name": "Main Field Prep & Ridge Bed Formation / நில உழவு & பாத்தி அமைத்தல்",
        "stage_name_local": "நில உழவு & பாத்தி அமைத்தல்",
        "description": "Disc ploughing, rotavator leveling, application of FYM (10 tonnes/acre), and forming raised beds with silver-black mulch sheet.",
        "duration_days": 10,
        "visual_asset_type": "TILLAGE",
        "visual_theme_color": "#854d0e",
        "recommended_activities": [
            "Deep tillage and FYM + neem cake incorporation",
            "Forming raised beds (90cm width) and drip lateral laying",
            "Mulch film laying and hole punching at 60cm spacing"
        ],
        "recommended_inputs": ["Farmyard Manure", "Neem Cake", "Mulching Film 25 Micron"],
        "is_active": True
    },
    {
        "stage_order": 3,
        "stage_name": "Transplanting & Root Dip / நாற்று நடுதல் & வேர் நனைத்தல்",
        "stage_name_local": "நாற்று நடுதல் & வேர் நனைத்தல்",
        "description": "Transplanting 25-day old sturdy seedlings. Seedling root dip in bio-fertilizers and immediate drip fertigation.",
        "duration_days": 7,
        "visual_asset_type": "TRANSPLANT",
        "visual_theme_color": "#3b82f6",
        "recommended_activities": [
            "Seedling root dip in Pseudomonas & Azospirillum solution",
            "Transplanting in evening hours at 60cm spacing",
            "Starter dose fertigation (19:19:19)"
        ],
        "recommended_inputs": ["Azospirillum", "Phosphobacteria", "Soluble 19:19:19"],
        "is_active": True
    },
    {
        "stage_order": 4,
        "stage_name": "Staking & Trellising / முட்டுக் கொடுத்தல் & கொடி கட்டுதல்",
        "stage_name_local": "முட்டுக் கொடுத்தல் & கொடி கட்டுதல்",
        "description": "Bamboo stake installation and GI wire trellising to support vigorous upright growth and keep tomato fruits off damp soil.",
        "duration_days": 20,
        "visual_asset_type": "VEGETATIVE",
        "visual_theme_color": "#16a34a",
        "recommended_activities": [
            "Erection of sturdy bamboo stakes every 10 feet",
            "Tying plants with plastic twine / jute string to GI wires",
            "Side shoot pruning (nipping suckers) for main stem vigor"
        ],
        "recommended_inputs": ["Bamboo Poles", "GI Wire 16 Gauge", "Tying Twine"],
        "is_active": True
    },
    {
        "stage_order": 5,
        "stage_name": "Flowering & Fruit Set / பூ பூத்தல் & பிஞ்சு பிடித்தல்",
        "stage_name_local": "பூ பூத்தல் & பிஞ்சு பிடித்தல்",
        "description": "Profuse flowering and early fruit development. Fertigation with 12:61:0 (MAP) and Boron foliar spray for flower drop prevention.",
        "duration_days": 25,
        "visual_asset_type": "FLOWERING",
        "visual_theme_color": "#eab308",
        "recommended_activities": [
            "Foliar spray of Boron (1g/L) + Calcium nitrate (2g/L) to prevent blossom end rot",
            "Installation of pheromone traps for Helicoverpa fruit borer",
            "Regular fertigation schedule (0:52:34 + Calcium Nitrate)"
        ],
        "recommended_inputs": ["Calcium Nitrate", "Boron 20%", "Fruit Borer Pheromone Traps"],
        "is_active": True
    },
    {
        "stage_order": 6,
        "stage_name": "Fruit Growth & Breaker Stage / காய் வளர்ச்சி & நிறம் மாறுதல்",
        "stage_name_local": "காய் வளர்ச்சி & நிறம் மாறுதல்",
        "description": "Fruit expansion to full size. Breaker / turning stage with slight pink-red blush at the blossom end. High Potassium requirement (0:0:50).",
        "duration_days": 18,
        "visual_asset_type": "MATURITY",
        "visual_theme_color": "#f97316",
        "recommended_activities": [
            "Potassium-rich fertigation (0:0:50) for uniform red color and fruit firmness",
            "Monitoring fruit fly and leaf miner incidence",
            "Checking fruit firmness and breaker stage color"
        ],
        "recommended_inputs": ["Sulfate of Potash (0:0:50)", "Neem Oil"],
        "is_active": True
    },
    {
        "stage_order": 7,
        "stage_name": "Harvesting (Multiple Pickings) / தக்காளி பறித்தல்",
        "stage_name_local": "தக்காளி பறித்தல்",
        "description": "Manual picking of firm breaker/turning stage tomatoes in cool morning hours every 3-4 days into plastic crates.",
        "duration_days": 25,
        "visual_asset_type": "HARVEST",
        "visual_theme_color": "#e11d48",
        "recommended_activities": [
            "Hand picking fruit with calyx attached in morning hours",
            "Gentle placement into 25kg plastic ventilated crates",
            "Grading on farm into table-fresh vs local processing"
        ],
        "recommended_inputs": ["Plastic Harvesting Crates (25kg)", "Cotton Gloves"],
        "is_active": True
    },
    {
        "stage_order": 8,
        "stage_name": "Grading, Packing & Market Dispatch / தரம் பிரித்தல் & விற்பனை",
        "stage_name_local": "தரம் பிரித்தல் & விற்பனை",
        "description": "Sorting by size and color into Grade-A (table/retail) and Grade-B. Weighing crates and dispatching to marketplace or mandi.",
        "duration_days": 5,
        "visual_asset_type": "YIELD_STORAGE",
        "visual_theme_color": "#0d9488",
        "recommended_activities": [
            "Grading by size, firmness, and absence of sun scald/blemishes",
            "Standard 25kg crate packing and weighment tagging",
            "Fast dispatch via logistics transport to buyers"
        ],
        "recommended_inputs": ["Ventilated Plastic Crates (25kg)", "Weighment Scale", "Batch Barcode Labels"],
        "is_active": True
    },
]

PADDY_STAGES: List[Dict[str, Any]] = [
    {
        "stage_order": 1,
        "stage_name": "Nursery Bed Preparation & Sowing / நாற்றங்கால் தயாரிப்பு & விதைப்பு",
        "stage_name_local": "நாற்றங்கால் தயாரிப்பு & விதைப்பு",
        "description": "Wet nursery bed preparation (20 cents per acre), certified seed soaking (e.g. CO 51 / CR 1009 / BPT 5204), and sprouted seed broadcasting with bio-fertilizers.",
        "duration_days": 22,
        "visual_asset_type": "NURSERY",
        "visual_theme_color": "#059669",
        "recommended_activities": [
            "Puddle nursery land (2-3 times) and level with wooden plank",
            "Seed treatment with Azospirillum and Trichoderma viride",
            "Broadcasting sprouted seeds uniformly with thin water film maintenance"
        ],
        "recommended_inputs": ["Certified Paddy Seeds (CO 51 / BPT)", "Azospirillum", "Pseudomonas fluorescens"],
        "is_active": True
    },
    {
        "stage_order": 2,
        "stage_name": "Main Field Puddling & Transplanting / சேற்று உழவு & நடவு பணி",
        "stage_name_local": "சேற்று உழவு & நடவு பணி",
        "description": "Main field tractor puddling, leveling, basal fertilizer application (DAP + Zinc + FYM), and manual or transplanter machine planting at 20cm x 10cm spacing.",
        "duration_days": 10,
        "visual_asset_type": "TRANSPLANT",
        "visual_theme_color": "#3b82f6",
        "recommended_activities": [
            "Tractor cage wheel puddling and leveling",
            "Basal application of DAP (50kg/acre), Potash, and Zinc Sulphate (10kg/acre)",
            "Transplanting 2-3 seedlings per hill at 20cm x 10cm spacing"
        ],
        "recommended_inputs": ["DAP Fertilizer", "MOP Potash", "Zinc Sulphate", "Farmyard Manure"],
        "is_active": True
    },
    {
        "stage_order": 3,
        "stage_name": "Active Tillering & Cono Weeding / தூர் கட்டுதல் & களை எடுத்தல்",
        "stage_name_local": "தூர் கட்டுதல் & களை எடுத்தல்",
        "description": "Maximum tillering stage (25-45 DAT). Cono-weeder operation between lines for root aeration and split Urea + Potash top dressing.",
        "duration_days": 30,
        "visual_asset_type": "WEEDING",
        "visual_theme_color": "#16a34a",
        "recommended_activities": [
            "Cono-weeder operation at 15 and 30 DAT to incorporate weeds as green manure",
            "First top dressing of Urea (30kg) and Potash (15kg)",
            "Monitoring for stem borer and leaf folder caterpillars"
        ],
        "recommended_inputs": ["Urea", "Potash (MOP)", "Neem Cake", "Cono Weeder Tool"],
        "is_active": True
    },
    {
        "stage_order": 4,
        "stage_name": "Panicle Initiation & Flowering / கதிர் உருவாக்கம் & பூக்கும் நிலை",
        "stage_name_local": "கதிர் உருவாக்கம் & பூக்கும் நிலை",
        "description": "Panicle emergence and uniform flowering. Continuous shallow water submergence (5cm) and prophylactic spray for blast and sheath blight.",
        "duration_days": 25,
        "visual_asset_type": "FLOWERING",
        "visual_theme_color": "#eab308",
        "recommended_activities": [
            "Maintain 5cm standing water in the field",
            "Final top dressing of Potash for grain weight",
            "Prophylactic foliar spray of Pseudomonas for blast disease prevention"
        ],
        "recommended_inputs": ["Potash (MOP)", "Pseudomonas fluorescens", "Hexaconazole"],
        "is_active": True
    },
    {
        "stage_order": 5,
        "stage_name": "Grain Filling & Dough Stage / பால் பிடிக்கும் நிலை & முதிர்வு",
        "stage_name_local": "பால் பிடிக்கும் நிலை & முதிர்வு",
        "description": "Milky stage transits to hard golden dough stage. 85-90% panicles turn golden yellow. Drain field water 10-12 days before harvest.",
        "duration_days": 20,
        "visual_asset_type": "MATURITY",
        "visual_theme_color": "#d97706",
        "recommended_activities": [
            "Drain water completely from the field 10-12 days prior to harvest",
            "Observe golden grain color across 85% of panicles",
            "Prevent bird damage and lodging"
        ],
        "recommended_inputs": [],
        "is_active": True
    },
    {
        "stage_order": 6,
        "stage_name": "Combine Harvesting & Bagging / நெல் அறுவடை & மூட்டை பிடித்தல்",
        "stage_name_local": "நெல் அறுவடை & மூட்டை பிடித்தல்",
        "description": "Combine harvester operation or manual harvesting + mechanical threshing. Grain cleaning, sun drying to 13% moisture, and 75kg gunny bagging.",
        "duration_days": 8,
        "visual_asset_type": "HARVEST",
        "visual_theme_color": "#ca8a04",
        "recommended_activities": [
            "Combine harvester operation for simultaneous reaping, threshing, and cleaning",
            "Sun drying cleaned paddy on threshing floor to 13% safe storage moisture",
            "Packing in standard 75kg or 100kg jute bags for Mandi auction or warehouse"
        ],
        "recommended_inputs": ["Paddy Jute Bags (75kg)", "Moisture Meter", "Combine Harvester Rental"],
        "is_active": True
    },
]

CROPS_DATA = [
    {
        "crop_name": "Onion / வெங்காயம்",
        "crop_code": "CRP-001",
        "scientific_name": "Allium cepa",
        "crop_category": CropCategoryEnum.VEGETABLE.value,
        "image_url": "/images/crops/onion.jpg",
        "local_names": {
            "en": "Onion",
            "ta": "வெங்காயம்",
            "hi": "प्याज",
            "kn": "ಈರುಳ್ಳಿ",
            "te": "ఉల్లిపాయ"
        },
        "description": "High-value seasonal bulb crop cultivated across Tamil Nadu with 8-stage precision agronomic cycle.",
        "stages": ONION_STAGES,
    },
    {
        "crop_name": "Groundnut / நிலக்கடலை",
        "crop_code": "CRP-002",
        "scientific_name": "Arachis hypogaea",
        "crop_category": CropCategoryEnum.OILSEED.value,
        "image_url": "/images/crops/groundnut.jpg",
        "local_names": {
            "en": "Groundnut",
            "ta": "நிலக்கடலை",
            "hi": "मूंगफली",
            "kn": "ಕಡಲೆಕಾಯಿ",
            "te": "వేరుశెనగ"
        },
        "description": "Major Kharif & Rabi oilseed and cash crop with 6-stage agronomic cycle.",
        "stages": GROUNDNUT_STAGES,
    },
    {
        "crop_name": "Tomato / தக்காளி",
        "crop_code": "CRP-003",
        "scientific_name": "Solanum lycopersicum",
        "crop_category": CropCategoryEnum.VEGETABLE.value,
        "image_url": "/images/crops/tomato.jpg",
        "local_names": {
            "en": "Tomato",
            "ta": "தக்காளி",
            "hi": "टमाटर",
            "kn": "ಟೊಮೆಟೊ",
            "te": "టమోటా"
        },
        "description": "High-yield commercial vegetable with 8-stage precision staking, fertigation, and multi-picking lifecycle.",
        "stages": TOMATO_STAGES,
    },
    {
        "crop_name": "Paddy (Rice) / நெல்",
        "crop_code": "CRP-004",
        "scientific_name": "Oryza sativa",
        "crop_category": CropCategoryEnum.CEREAL.value,
        "image_url": "/images/crops/paddy.jpg",
        "local_names": {
            "en": "Paddy (Rice)",
            "ta": "நெல்",
            "hi": "धान",
            "kn": "ಭತ್ತ",
            "te": "వరి"
        },
        "description": "Staple wetland cereal crop with 6-stage puddling, transplanting, and combine harvest lifecycle.",
        "stages": PADDY_STAGES,
    },
    {
        "crop_name": "Turmeric / மஞ்சள்",
        "crop_code": "CRP-005",
        "scientific_name": "Curcuma longa",
        "crop_category": CropCategoryEnum.SPICE.value,
        "image_url": "/images/crops/turmeric.jpg",
        "local_names": {
            "en": "Turmeric",
            "ta": "மஞ்சள்",
            "hi": "हल्दी",
            "kn": "ಅರಿಶಿನ",
            "te": "పసుపు"
        },
        "description": "High-value spice rhizome crop with 6-stage planting, earthing up, and boiling/curing lifecycle.",
        "stages": [
            {
                "stage_order": 1,
                "stage_name": "Land Preparation & Ridge Formation / நில உழவு & பார் அமைத்தல்",
                "stage_name_local": "நில உழவு & பார் அமைத்தல்",
                "description": "Deep tilling with FYM and forming 45cm ridges and furrows for rhizome aeration.",
                "duration_days": 15,
                "visual_asset_type": "TILLAGE",
                "visual_theme_color": "#854d0e",
                "recommended_activities": ["Deep ploughing", "FYM application 10t/acre", "Ridge formation"],
                "recommended_inputs": ["Farmyard Manure", "Neem Cake"],
                "is_active": True
            },
            {
                "stage_order": 2,
                "stage_name": "Mother Rhizome Planting / தாய் கிழங்கு நடவு",
                "stage_name_local": "தாய் கிழங்கு நடவு",
                "description": "Selected healthy mother rhizomes treated with Trichoderma and planted at 15cm spacing.",
                "duration_days": 10,
                "visual_asset_type": "SEED",
                "visual_theme_color": "#10b981",
                "recommended_activities": ["Seed rhizome treatment", "Ridge planting", "Mulching with green leaves"],
                "recommended_inputs": ["Trichoderma viride", "Pseudomonas"],
                "is_active": True
            },
            {
                "stage_order": 3,
                "stage_name": "Weeding & Earthing Up / களை எடுத்தல் & மண் அணைத்தல்",
                "stage_name_local": "களை எடுத்தல் & மண் அணைத்தல்",
                "description": "Manual weeding and earthing up around growing rhizome clusters at 60 and 90 DAS.",
                "duration_days": 60,
                "visual_asset_type": "WEEDING",
                "visual_theme_color": "#16a34a",
                "recommended_activities": ["De-weeding", "Top soil loosening", "Earthing up soil"],
                "recommended_inputs": ["Hand weeding hoes"],
                "is_active": True
            },
            {
                "stage_order": 4,
                "stage_name": "Fertigation & Micronutrient Spray / உரம் & நுண்ணூட்டச் சத்து",
                "stage_name_local": "உரம் & நுண்ணூட்டச் சத்து",
                "description": "Foliar spray of Turmeric Special micronutrients and potash fertigation for rhizome weight.",
                "duration_days": 75,
                "visual_asset_type": "VEGETATIVE",
                "visual_theme_color": "#3b82f6",
                "recommended_activities": ["Turmeric Special foliar spray", "Potash fertigation", "Shoot borer monitoring"],
                "recommended_inputs": ["Turmeric Special Micronutrient", "Sulfate of Potash (0:0:50)"],
                "is_active": True
            },
            {
                "stage_order": 5,
                "stage_name": "Maturity & Leaf Drying / இலை காய்வு & முதிர்ச்சி நிலை",
                "stage_name_local": "இலை காய்வு & முதிர்ச்சி நிலை",
                "description": "Leaves turn yellowish brown and dry completely, indicating peak curcumin synthesis.",
                "duration_days": 30,
                "visual_asset_type": "MATURITY",
                "visual_theme_color": "#d97706",
                "recommended_activities": ["Stop irrigation 15 days before harvest", "Maturity check"],
                "recommended_inputs": [],
                "is_active": True
            },
            {
                "stage_order": 6,
                "stage_name": "Harvesting, Boiling & Curing / அறுவடை & வேகவைத்தல்",
                "stage_name_local": "அறுவடை & வேகவைத்தல்",
                "description": "Tractor digger harvesting, rhizome cleaning, boiling in turmeric boilers, and sun drying.",
                "duration_days": 20,
                "visual_asset_type": "HARVEST",
                "visual_theme_color": "#ca8a04",
                "recommended_activities": ["Digging out fingers and bulbs", "Boiling in steam drum", "Sun drying on clean floor for 10-15 days"],
                "recommended_inputs": ["Jute Bags", "Turmeric Boiler Unit Rental"],
                "is_active": True
            }
        ]
    }
]


def seed_crop_stages(db: Session) -> Dict[str, Any]:
    """Seeds master crops and their dynamic cultivation process stage templates."""
    total_crops_created = 0
    total_stages_created = 0
    total_stages_updated = 0

    for crop_info in CROPS_DATA:
        stmt = select(Crop).where(
            (Crop.crop_code == crop_info["crop_code"]) | (Crop.crop_name.ilike(f"%{crop_info['crop_name'].split('/')[0].strip()}%"))
        ).limit(1)
        crop = db.execute(stmt).scalar_one_or_none()

        if not crop:
            crop = Crop(
                id=uuid.uuid4(),
                crop_name=crop_info["crop_name"],
                crop_code=crop_info["crop_code"],
                scientific_name=crop_info["scientific_name"],
                crop_category=crop_info["crop_category"],
                image_url=crop_info.get("image_url"),
                local_names=crop_info.get("local_names", {}),
                description=crop_info["description"],
                is_active=True
            )
            db.add(crop)
            db.commit()
            db.refresh(crop)
            total_crops_created += 1
            logger.info("Created crop master record: %s (%s)", crop.crop_name, crop.id)
        else:
            # Ensure crop_code, image_url, local_names and category are up to date
            crop.crop_name = crop_info["crop_name"]
            crop.scientific_name = crop_info["scientific_name"]
            crop.crop_category = crop_info["crop_category"]
            crop.image_url = crop_info.get("image_url", crop.image_url)
            crop.local_names = crop_info.get("local_names", crop.local_names)
            crop.description = crop_info["description"]
            db.commit()

        # Seed/update stages for this crop
        for stage_data in crop_info["stages"]:
            stage_stmt = (
                select(CropCultivationStage)
                .where(
                    CropCultivationStage.crop_id == crop.id,
                    CropCultivationStage.stage_order == stage_data["stage_order"],
                    CropCultivationStage.is_deleted.is_(False)
                )
            )
            existing_stage = db.execute(stage_stmt).scalar_one_or_none()

            if existing_stage:
                existing_stage.stage_name = stage_data["stage_name"]
                existing_stage.stage_name_local = stage_data["stage_name_local"]
                existing_stage.description = stage_data["description"]
                existing_stage.duration_days = stage_data["duration_days"]
                existing_stage.visual_asset_type = stage_data["visual_asset_type"]
                existing_stage.visual_theme_color = stage_data["visual_theme_color"]
                existing_stage.recommended_activities = stage_data["recommended_activities"]
                existing_stage.recommended_inputs = stage_data["recommended_inputs"]
                existing_stage.is_active = stage_data["is_active"]
                total_stages_updated += 1
            else:
                new_stage = CropCultivationStage(
                    id=uuid.uuid4(),
                    crop_id=crop.id,
                    stage_order=stage_data["stage_order"],
                    stage_name=stage_data["stage_name"],
                    stage_name_local=stage_data["stage_name_local"],
                    description=stage_data["description"],
                    duration_days=stage_data["duration_days"],
                    visual_asset_type=stage_data["visual_asset_type"],
                    visual_theme_color=stage_data["visual_theme_color"],
                    recommended_activities=stage_data["recommended_activities"],
                    recommended_inputs=stage_data["recommended_inputs"],
                    is_active=stage_data["is_active"]
                )
                db.add(new_stage)
                total_stages_created += 1

        db.commit()

    # Retrieve Onion crop for backward compatibility with test fixtures
    onion_crop = db.query(Crop).filter(Crop.crop_name.ilike("%Onion%")).first()
    first_crop_id = str(onion_crop.id) if onion_crop else None

    logger.info(
        "Crop Stages Seeding Finished: %d crops created, %d stages created, %d stages updated",
        total_crops_created,
        total_stages_created,
        total_stages_updated,
    )
    return {
        "crop_id": first_crop_id,
        "crop_name": onion_crop.crop_name if onion_crop else "Onion",
        "crops_created": total_crops_created,
        "stages_created": total_stages_created,
        "stages_updated": total_stages_updated,
    }


def run_seed() -> None:
    db = SessionLocal()
    try:
        result = seed_crop_stages(db)
        logger.info("Crop Stages Seeder Result: %s", result)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.livestock import LivestockCategory, LivestockBreed

logger = logging.getLogger("agri_smart.seeds.livestock")

LIVESTOCK_TAXONOMY = [
    {
        "code": "CHICKEN",
        "name": "Chicken",
        "name_ta": "கோழி",
        "description": "Poultry chickens including native free-range, dual-purpose, egg layers, and meat birds.",
        "icon_slug": "chicken",
        "display_order": 1,
        "breeds": [
            {"code": "COUNTRY_CHICKEN", "name": "Country Chicken", "name_ta": "நாட்டுக்கோழி", "characteristics": "Traditional hardy free-range organic chicken.", "display_order": 1},
            {"code": "KADAKNATH", "name": "Kadaknath", "name_ta": "கருங்கோழி", "characteristics": "High protein black-meat heritage breed known for medicinal value.", "display_order": 2},
            {"code": "ASEEL", "name": "Aseel", "name_ta": "அசல் சண்டை சேவல் / பெருவிடை", "characteristics": "Majestic, muscular heritage gamefowl breed.", "display_order": 3},
            {"code": "GIRIRAJA", "name": "Giriraja", "name_ta": "கிரிராஜா", "characteristics": "Fast growing dual purpose backyard poultry.", "display_order": 4},
            {"code": "KAVERI", "name": "Kaveri", "name_ta": "காவேரி", "characteristics": "Dual purpose high disease resistance poultry.", "display_order": 5},
            {"code": "BROILER", "name": "Commercial Broiler", "name_ta": "பிராய்லர்", "characteristics": "Fast-growing meat chicken.", "display_order": 6},
            {"code": "LAYER", "name": "Commercial Layer", "name_ta": "லேயர் முட்டைக்கோழி", "characteristics": "High-yield commercial egg producing hens.", "display_order": 7},
            {"code": "OTHER_CHICKEN", "name": "Other Chicken Breed", "name_ta": "மற்ற கோழி ரகங்கள்", "characteristics": "Cross-bred or regional native chickens.", "display_order": 8},
        ]
    },
    {
        "code": "GOAT",
        "name": "Goat",
        "name_ta": "ஆடு",
        "description": "Meat and dairy goats adapted to tropical and intensive farming systems.",
        "icon_slug": "goat",
        "display_order": 2,
        "breeds": [
            {"code": "KANNI_ADU", "name": "Kanni Adu", "name_ta": "கன்னி ஆடு", "characteristics": "Tamil Nadu native meat breed, drought-tolerant with black-and-brown coat.", "display_order": 1},
            {"code": "SALEM_BLACK", "name": "Salem Black", "name_ta": "சேலம் கருப்பு", "characteristics": "Completely black meat goat renowned for superior mutton quality.", "display_order": 2},
            {"code": "BOER", "name": "Boer", "name_ta": "போயர் ஆடு", "characteristics": "World-leading fast-growth meat goat breed.", "display_order": 3},
            {"code": "JAMUNAPARI", "name": "Jamunapari", "name_ta": "ஜமுனாபாரி", "characteristics": "Tall, dual-purpose milk and meat goat with roman nose.", "display_order": 4},
            {"code": "TELLICHERRY", "name": "Tellicherry / Malabari", "name_ta": "தலச்சேரி ஆடு", "characteristics": "Prolific breeder with high twinning and triplet rates.", "display_order": 5},
            {"code": "SIROHI", "name": "Sirohi", "name_ta": "சிரோகி", "characteristics": "Hardy semi-arid goat breed suitable for stall feeding.", "display_order": 6},
            {"code": "OSMANABADI", "name": "Osmanabadi", "name_ta": "உஸ்மனாபாதி", "characteristics": "Disease-resistant and adaptable meat breed.", "display_order": 7},
            {"code": "OTHER_GOAT", "name": "Other Goat Breed", "name_ta": "மற்ற ஆட்டு ரகங்கள்", "characteristics": "Regional native or cross-bred goats.", "display_order": 8},
        ]
    },
    {
        "code": "COW",
        "name": "Cow",
        "name_ta": "மாடு",
        "description": "Indigenous desi cattle and high-yielding dairy cows.",
        "icon_slug": "cow",
        "display_order": 3,
        "breeds": [
            {"code": "KANGAYAM", "name": "Kangayam", "name_ta": "காங்கேயம் காளை / பசு", "characteristics": "World-renowned draught breed from Tamil Nadu, extremely resilient.", "display_order": 1},
            {"code": "GIR", "name": "Gir", "name_ta": "கிர் பசு (A2 பால்)", "characteristics": "Famous A2 milk indigenous dairy cattle from Gujarat.", "display_order": 2},
            {"code": "SAHIWAL", "name": "Sahiwal", "name_ta": "சாஹிவால்", "characteristics": "Top indigenous milch breed producing rich A2 milk.", "display_order": 3},
            {"code": "UMBLACHERY", "name": "Umblachery", "name_ta": "உம்பளச்சேரி", "characteristics": "Native delta breed ideal for wetland plowing and compact milking.", "display_order": 4},
            {"code": "RED_SINDHI", "name": "Red Sindhi", "name_ta": "சிவப்பு சிந்தி", "characteristics": "Heat and tick-resistant indigenous dairy cow.", "display_order": 5},
            {"code": "JERSEY_CROSS", "name": "Jersey Cross", "name_ta": "ஜெர்சி கலப்பின மாடு", "characteristics": "High butterfat commercial dairy cow.", "display_order": 6},
            {"code": "HF_CROSS", "name": "Holstein Friesian (HF) Cross", "name_ta": "ஹெச்.எஃப் கலப்பின மாடு", "characteristics": "Very high milk production volume dairy cow.", "display_order": 7},
            {"code": "OTHER_COW", "name": "Other Cattle Breed", "name_ta": "மற்ற நாட்டு மாடுகள்", "characteristics": "Other indigenous or mixed dairy cows.", "display_order": 8},
        ]
    },
    {
        "code": "CALF",
        "name": "Calf",
        "name_ta": "கன்றுக்குட்டி",
        "description": "Young male and female cattle calves raised for rearing and future dairy/draught.",
        "icon_slug": "calf",
        "display_order": 4,
        "breeds": [
            {"code": "KANGAYAM_CALF", "name": "Kangayam Calf", "name_ta": "காங்கேயம் கன்று", "characteristics": "Purebred Kangayam heifer or bull calf.", "display_order": 1},
            {"code": "GIR_CALF", "name": "Gir Heifer / Bull Calf", "name_ta": "கிர் கன்று", "characteristics": "A2 pure Gir genetics calf.", "display_order": 2},
            {"code": "DAIRY_CROSS_CALF", "name": "Dairy Cross Heifer Calf", "name_ta": "கலப்பின கிடாரி கன்று", "characteristics": "Prospective high-yielding dairy heifer.", "display_order": 3},
            {"code": "OTHER_CALF", "name": "Other Calf Breed", "name_ta": "மற்ற கன்றுகள்", "characteristics": "Native or cross-bred farm calves.", "display_order": 4},
        ]
    },
    {
        "code": "BUFFALO",
        "name": "Buffalo",
        "name_ta": "எருமை",
        "description": "High-fat dairy buffaloes and working farm buffaloes.",
        "icon_slug": "buffalo",
        "display_order": 5,
        "breeds": [
            {"code": "MURRAH", "name": "Murrah", "name_ta": "முர்ரா எருமை", "characteristics": "Premier dairy buffalo breed known for rich 7-8% fat milk.", "display_order": 1},
            {"code": "TODA", "name": "Toda Buffalo", "name_ta": "தோடா எருமை", "characteristics": "Nilgiris indigenous high-altitude semi-wild buffalo.", "display_order": 2},
            {"code": "SURTI", "name": "Surti", "name_ta": "சுர்தி எருமை", "characteristics": "Medium-sized economical dairy buffalo.", "display_order": 3},
            {"code": "MEHSANA", "name": "Mehsana", "name_ta": "மெஹ்சானா", "characteristics": "Docile buffalo with consistent high lactation.", "display_order": 4},
            {"code": "OTHER_BUFFALO", "name": "Other Buffalo Breed", "name_ta": "நாட்டு எருமை", "characteristics": "Native country buffaloes.", "display_order": 5},
        ]
    },
    {
        "code": "SHEEP",
        "name": "Sheep",
        "name_ta": "செம்மறியாடு",
        "description": "Wool, meat, and dual-purpose sheep breeds.",
        "icon_slug": "sheep",
        "display_order": 6,
        "breeds": [
            {"code": "MECHERI", "name": "Mecheri", "name_ta": "மேச்சேரி செம்மறி", "characteristics": "Famous drought-hardy mutton breed with tender meat.", "display_order": 1},
            {"code": "MADRAS_RED", "name": "Madras Red", "name_ta": "சென்னை சிவப்பு செம்மறி", "characteristics": "Hardy red-coated meat sheep adapted to semi-arid regions.", "display_order": 2},
            {"code": "RAMNAD_WHITE", "name": "Ramnad White", "name_ta": "ராமநாதபுரம் வெள்ளை", "characteristics": "Native meat sheep with white coat and black muzzle.", "display_order": 3},
            {"code": "VEMBUR", "name": "Vembur", "name_ta": "வேம்பூர் செம்மறி", "characteristics": "Tall, white with red spots meat sheep from Thoothukudi.", "display_order": 4},
            {"code": "KILAKARSAL", "name": "Kilakarsal", "name_ta": "கீழக்கரிசல் செம்மறி", "characteristics": "Native meat breed with dark tan coat.", "display_order": 5},
            {"code": "OTHER_SHEEP", "name": "Other Sheep Breed", "name_ta": "மற்ற செம்மறி ரகங்கள்", "characteristics": "Other local sheep breeds.", "display_order": 6},
        ]
    },
    {
        "code": "DUCK",
        "name": "Duck",
        "name_ta": "வாத்து",
        "description": "Pond and free-range ducks raised for eggs and meat.",
        "icon_slug": "duck",
        "display_order": 7,
        "breeds": [
            {"code": "INDIAN_RUNNER", "name": "Indian Runner / Country Duck", "name_ta": "நாட்டு வாத்து", "characteristics": "Prolific egg layer, active forager in paddy fields.", "display_order": 1},
            {"code": "WHITE_PEKIN", "name": "White Pekin", "name_ta": "பெக்கின் வாத்து", "characteristics": "Fast-growing white meat duck.", "display_order": 2},
            {"code": "KHAKI_CAMPBELL", "name": "Khaki Campbell", "name_ta": "காக்கி கேம்ப்பல்", "characteristics": "World-class egg laying duck (up to 300 eggs/year).", "display_order": 3},
            {"code": "MUSCOVY", "name": "Muscovy", "name_ta": "மஸ்கோவி வாத்து", "characteristics": "Quiet, lean-meat duck with caruncled red face.", "display_order": 4},
            {"code": "OTHER_DUCK", "name": "Other Duck Breed", "name_ta": "மற்ற வாத்து ரகங்கள்", "characteristics": "Regional native ducks.", "display_order": 5},
        ]
    },
    {
        "code": "TURKEY",
        "name": "Turkey",
        "name_ta": "வான்கோழி",
        "description": "Meat turkeys suited for extensive farm rearing.",
        "icon_slug": "turkey",
        "display_order": 8,
        "breeds": [
            {"code": "BROAD_BREASTED_BRONZE", "name": "Broad Breasted Bronze", "name_ta": "பிரான்ஸ் வான்கோழி", "characteristics": "Heavy meat bird with striking metallic bronze feathers.", "display_order": 1},
            {"code": "BELTSVILLE_WHITE", "name": "Beltsville Small White", "name_ta": "வெள்ளை வான்கோழி", "characteristics": "Compact size, good egg production and meat quality.", "display_order": 2},
            {"code": "NANDANAM_TURKEY", "name": "Nandanam Turkey", "name_ta": "நந்தனம் வான்கோழி", "characteristics": "TANUVAS-developed disease-resistant backyard turkey.", "display_order": 3},
            {"code": "OTHER_TURKEY", "name": "Other Turkey Breed", "name_ta": "மற்ற வான்கோழி ரகங்கள்", "characteristics": "Local farm turkeys.", "display_order": 4},
        ]
    },
    {
        "code": "RABBIT",
        "name": "Rabbit",
        "name_ta": "முயல்",
        "description": "Meat and pet rabbit breeds.",
        "icon_slug": "rabbit",
        "display_order": 9,
        "breeds": [
            {"code": "NEW_ZEALAND_WHITE", "name": "New Zealand White", "name_ta": "நியூசிலாந்து வெள்ளை முயல்", "characteristics": "Leading commercial meat rabbit breed.", "display_order": 1},
            {"code": "SOVIET_CHINCHILLA", "name": "Soviet Chinchilla", "name_ta": "சோவியத் சின்சில்லா", "characteristics": "Hardy, dense grey-coated meat rabbit.", "display_order": 2},
            {"code": "GREY_GIANT", "name": "Grey Giant", "name_ta": "கிரே ஜெயன்ட்", "characteristics": "Large frame fast-growing rabbit.", "display_order": 3},
            {"code": "FLEMISH_GIANT", "name": "Flemish Giant", "name_ta": "பிளெமிஷ் ஜெயன்ட்", "characteristics": "Very large heritage rabbit breed.", "display_order": 4},
            {"code": "OTHER_RABBIT", "name": "Other Rabbit Breed", "name_ta": "நாட்டு முயல்", "characteristics": "Local farm or pet rabbits.", "display_order": 5},
        ]
    },
    {
        "code": "OTHER",
        "name": "Other Farm Animals",
        "name_ta": "இதர பண்ணை விலங்குகள்",
        "description": "Other agricultural livestock such as Quail, Guinea Fowl, and Horses.",
        "icon_slug": "other",
        "display_order": 10,
        "breeds": [
            {"code": "JAPANESE_QUAIL", "name": "Japanese Quail (Kaada)", "name_ta": "காடை", "characteristics": "Fast-cycling meat and egg quail.", "display_order": 1},
            {"code": "GUINEA_FOWL", "name": "Guinea Fowl (Gini Kozhi)", "name_ta": "கினிக்கோழி", "characteristics": "Hardy foraging gamebird.", "display_order": 2},
            {"code": "FARM_HORSE", "name": "Farm / Draught Horse", "name_ta": "குதிரை", "characteristics": "Marwari, Kathiawari, or country horses.", "display_order": 3},
            {"code": "MIXED_FARM", "name": "Mixed Farm Animal", "name_ta": "பண்ணை விலங்கு", "characteristics": "Other domestic farm livestock.", "display_order": 4},
        ]
    }
]


def seed_livestock_master(db: Session) -> dict:
    """
    Idempotently seeds livestock categories and breeds with Tamil & English taxonomy.
    """
    logger.info("Starting livestock master taxonomy seeding...")
    categories_created = 0
    breeds_created = 0

    for cat_data in LIVESTOCK_TAXONOMY:
        category = db.scalar(
            select(LivestockCategory).where(LivestockCategory.code == cat_data["code"])
        )
        if not category:
            category = LivestockCategory(
                id=uuid.uuid4(),
                code=cat_data["code"],
                name=cat_data["name"],
                name_ta=cat_data["name_ta"],
                description=cat_data["description"],
                icon_slug=cat_data["icon_slug"],
                display_order=cat_data["display_order"],
                is_active=True
            )
            db.add(category)
            db.flush()
            categories_created += 1
            logger.info("Created livestock category: %s (%s)", category.name, category.code)

        for breed_data in cat_data["breeds"]:
            breed = db.scalar(
                select(LivestockBreed).where(
                    LivestockBreed.category_id == category.id,
                    LivestockBreed.name == breed_data["name"]
                )
            )
            if not breed:
                breed = LivestockBreed(
                    id=uuid.uuid4(),
                    category_id=category.id,
                    code=breed_data["code"],
                    name=breed_data["name"],
                    name_ta=breed_data["name_ta"],
                    description=breed_data.get("description"),
                    characteristics=breed_data.get("characteristics"),
                    display_order=breed_data["display_order"],
                    is_active=True
                )
                db.add(breed)
                breeds_created += 1

    db.commit()
    logger.info(
        "Livestock master seeding complete. Categories created: %d, Breeds created: %d",
        categories_created,
        breeds_created
    )
    return {
        "categories_created": categories_created,
        "breeds_created": breeds_created
    }

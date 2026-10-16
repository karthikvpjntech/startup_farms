import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.input_master import InputMaster
from app.models.supplier import Supplier
from app.repositories.input_master_repository import InputMasterRepository
from app.repositories.supplier_repository import SupplierRepository

logger = logging.getLogger("agri_smart.seeds.inputs_suppliers")

INPUT_CATALOG_DATA = [
    {
        "input_code": "INP-000001",
        "input_name": "Onion Seed Co-5 / வெங்காயம் விதை Co-5",
        "category": "SEED",
        "unit": "KG",
        "technical_name": "Allium cepa var. aggregatum",
        "brand_name": "TNAU Certified Seeds",
        "description": "High-yielding small onion (shallot) seed variety with high disease resistance and uniform bulb formation.",
    },
    {
        "input_code": "INP-000002",
        "input_name": "Trichoderma Viride 1.0% WP / டிரைக்கோடெர்மா விரிடி",
        "category": "BIO_INPUT",
        "unit": "KG",
        "technical_name": "Trichoderma viride 1.0% WP bio-fungicide",
        "brand_name": "Bio-Rakshak Organic",
        "description": "Biological fungicide effective for bulb treatment and root-rot prevention in nursery and transplant beds.",
    },
    {
        "input_code": "INP-000003",
        "input_name": "Pseudomonas Fluorescens / சூடோமோனாஸ்",
        "category": "BIO_INPUT",
        "unit": "LITRE",
        "technical_name": "Pseudomonas fluorescens 1.5% LF",
        "brand_name": "BioShield Agri",
        "description": "Plant-growth promoting rhizobacteria providing systemic resistance against damping-off and foliar blight.",
    },
    {
        "input_code": "INP-000004",
        "input_name": "Cold-Pressed Neem Cake / வேப்பம் பிண்ணாக்கு",
        "category": "BIO_INPUT",
        "unit": "BAG",
        "technical_name": "Azadirachta indica 100% De-oiled Cake",
        "brand_name": "GreenGold Organics",
        "description": "Enriched organic soil conditioner protecting against nematodes and underground grubs while providing nitrogen.",
    },
    {
        "input_code": "INP-000005",
        "input_name": "Decomposed Farmyard Manure (FYM) / தொழு உரம்",
        "category": "FERTILIZER",
        "unit": "TONNE",
        "technical_name": "Organic Cattle Compost (0.5% N, 0.2% P, 0.5% K)",
        "brand_name": "Rural Agri Hub",
        "description": "Fully cured basal farmyard compost for improving soil microbial activity, aeration, and water retention.",
    },
    {
        "input_code": "INP-000006",
        "input_name": "Urea (46% Nitrogen) / யூரியா",
        "category": "FERTILIZER",
        "unit": "BAG",
        "technical_name": "Carbamide 46% N",
        "brand_name": "SPIC Agro",
        "description": "Standard high-nitrogen fertilizer for vegetative crop growth and canopy development (50kg bag).",
    },
    {
        "input_code": "INP-000007",
        "input_name": "DAP (Diammonium Phosphate 18-46-0) / டி.ஏ.பி",
        "category": "FERTILIZER",
        "unit": "BAG",
        "technical_name": "Diammonium Phosphate 18:46:0",
        "brand_name": "IFFCO",
        "description": "Essential basal source of nitrogen and phosphorus promoting rapid root architecture development.",
    },
    {
        "input_code": "INP-000008",
        "input_name": "MOP (Muriate of Potash 60%) / பொட்டாஷ்",
        "category": "FERTILIZER",
        "unit": "BAG",
        "technical_name": "Potassium Chloride 60% K2O",
        "brand_name": "Indian Potash Limited",
        "description": "Potassium fertilizer vital for bulb expansion, skin firmness, and shelf-life enhancement.",
    },
    {
        "input_code": "INP-000009",
        "input_name": "Chelated Micronutrient Formulation (Zn, B, Fe) / நுண்ணூட்ட சத்து கலவை",
        "category": "FERTILIZER",
        "unit": "KG",
        "technical_name": "Chelated Zinc, Boron & Iron Complex",
        "brand_name": "AgriZinc Plus",
        "description": "Foliar spray mixture preventing leaf chlorosis and ensuring optimal nutrient absorption in onion crops.",
    },
    {
        "input_code": "INP-000010",
        "input_name": "Mancozeb 75% WP / மேங்கோசெப் பூஞ்சாணக்கொல்லி",
        "category": "PESTICIDE",
        "unit": "KG",
        "technical_name": "Mancozeb 75% Wettable Powder",
        "brand_name": "Indofil M-45",
        "description": "Broad-spectrum contact fungicide controlling purple blotch, leaf blight, and downy mildew.",
    },
    {
        "input_code": "INP-000011",
        "input_name": "16mm UV-Stabilized Drip Lateral Pipe / சொட்டு நீர் குழாய்",
        "category": "IRRIGATION_SUPPLY",
        "unit": "PIECE",
        "technical_name": "16mm Inline Emitter Lateral (400m bundle)",
        "brand_name": "Jain Irrigation",
        "description": "Heavy-duty UV stabilized drip lateral bundle designed for high precision water and fertigation delivery.",
    },
]

SUPPLIERS_DATA = [
    {
        "supplier_code": "SUP-000001",
        "supplier_name": "Salem Farmers Agri-Input Cooperative Society",
        "contact_person": "M. Shanmugam",
        "phone_number": "9842011223",
        "email": "salemcoop@agrismart.local",
        "address_line1": "45 Market Road, Near Uzhavar Sandhai",
        "address_line2": "Attur Main Road",
        "village_city": "Attur",
        "district": "Salem",
        "state": "Tamil Nadu",
        "pincode": "636102",
        "gstin": "33AAACS1234F1Z1",
        "supplier_type": "COOPERATIVE",
    },
    {
        "supplier_code": "SUP-000002",
        "supplier_name": "Annai Agro Seeds & Chemical Distributors",
        "contact_person": "K. Balasubramanian",
        "phone_number": "9876543210",
        "email": "annaiagro@agrismart.local",
        "address_line1": "12 Bye-Pass Road",
        "address_line2": "Opposite Agricultural College",
        "village_city": "Namakkal",
        "district": "Namakkal",
        "state": "Tamil Nadu",
        "pincode": "637001",
        "gstin": "33AABCA9876G1Z2",
        "supplier_type": "DISTRIBUTOR",
    },
    {
        "supplier_code": "SUP-000003",
        "supplier_name": "SPIC & IFFCO Authorized Kisan Seva Kendra",
        "contact_person": "R. Prakash",
        "phone_number": "9443209871",
        "email": "kisansevakendra@agrismart.local",
        "address_line1": "88 Bhavani Main Road",
        "address_line2": "Agri Market Complex",
        "village_city": "Perundurai",
        "district": "Erode",
        "state": "Tamil Nadu",
        "pincode": "638052",
        "gstin": "33AACSP5544H1Z3",
        "supplier_type": "DISTRIBUTOR",
    },
    {
        "supplier_code": "SUP-000004",
        "supplier_name": "Kaveri Bio-Organics & Seed Tech",
        "contact_person": "Dr. S. Vasanth",
        "phone_number": "9443156789",
        "email": "kaveribio@agrismart.local",
        "address_line1": "7 Industrial Estate, Pollachi Road",
        "address_line2": "SIDCO Industrial Area",
        "village_city": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "pincode": "641021",
        "gstin": "33AABCK3322K1Z4",
        "supplier_type": "MANUFACTURER",
    },
    {
        "supplier_code": "SUP-000005",
        "supplier_name": "Cauvery Delta Agro Retailer & Farm Clinic",
        "contact_person": "G. Manickam",
        "phone_number": "9894012345",
        "email": "cauverydelta@agrismart.local",
        "address_line1": "23 Thanjavur Main Road",
        "address_line2": "Kattur Junction",
        "village_city": "Tiruchirappalli",
        "district": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "pincode": "620019",
        "gstin": "33AABCD1122L1Z5",
        "supplier_type": "RETAILER",
    },
]


def seed_inputs_and_suppliers(db: Session) -> Dict[str, Any]:
    """
    Seeds essential agricultural inputs and verified suppliers into the database.
    """
    created_inputs = []
    updated_inputs = []
    for item in INPUT_CATALOG_DATA:
        existing = InputMasterRepository.get_by_code(db, item["input_code"])
        if not existing:
            existing_by_name = InputMasterRepository.get_active_by_name(db, item["input_name"])
            if existing_by_name:
                existing = existing_by_name

        if existing:
            for k, v in item.items():
                setattr(existing, k, v)
            existing.is_active = True
            existing.is_deleted = False
            updated_inputs.append(existing.input_code)
        else:
            new_input = InputMaster(
                input_code=item["input_code"],
                input_name=item["input_name"],
                category=item["category"],
                unit=item["unit"],
                technical_name=item.get("technical_name"),
                brand_name=item.get("brand_name"),
                description=item.get("description"),
                is_active=True,
                is_deleted=False,
            )
            db.add(new_input)
            created_inputs.append(item["input_code"])

    db.commit()

    created_suppliers = []
    updated_suppliers = []
    for s_item in SUPPLIERS_DATA:
        existing = SupplierRepository.get_by_code(db, s_item["supplier_code"])
        if not existing:
            existing_by_phone = SupplierRepository.get_active_by_name_or_phone(
                db, s_item["supplier_name"], s_item["phone_number"]
            )
            if existing_by_phone:
                existing = existing_by_phone

        if existing:
            for k, v in s_item.items():
                setattr(existing, k, v)
            existing.is_active = True
            existing.is_deleted = False
            updated_suppliers.append(existing.supplier_code)
        else:
            new_sup = Supplier(
                supplier_code=s_item["supplier_code"],
                supplier_name=s_item["supplier_name"],
                contact_person=s_item.get("contact_person"),
                phone_number=s_item["phone_number"],
                email=s_item.get("email"),
                address_line1=s_item["address_line1"],
                address_line2=s_item.get("address_line2"),
                village_city=s_item["village_city"],
                district=s_item["district"],
                state=s_item["state"],
                pincode=s_item["pincode"],
                gstin=s_item.get("gstin"),
                supplier_type=s_item.get("supplier_type", "DISTRIBUTOR"),
                is_active=True,
                is_deleted=False,
            )
            db.add(new_sup)
            created_suppliers.append(s_item["supplier_code"])

    db.commit()

    logger.info(
        "Inputs seeded: %d created, %d updated; Suppliers seeded: %d created, %d updated",
        len(created_inputs),
        len(updated_inputs),
        len(created_suppliers),
        len(updated_suppliers),
    )
    return {
        "inputs_created": len(created_inputs),
        "inputs_updated": len(updated_inputs),
        "suppliers_created": len(created_suppliers),
        "suppliers_updated": len(updated_suppliers),
    }

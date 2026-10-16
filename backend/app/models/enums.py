from enum import Enum


class RoleEnum(str, Enum):
    """System-defined roles in the Agri-Smart Ecosystem."""
    SUPER_ADMIN = "SUPER_ADMIN"
    FARMER = "FARMER"
    TRADER = "TRADER"
    DRIVER = "DRIVER"
    WORKER = "WORKER"
    CUSTOMER = "CUSTOMER"


ROLE_DESCRIPTIONS = {
    RoleEnum.SUPER_ADMIN: "Complete system administration",
    RoleEnum.FARMER: "Cultivation and farm management",
    RoleEnum.TRADER: "Inventory and mandi trading",
    RoleEnum.DRIVER: "Transport and trip management",
    RoleEnum.WORKER: "Labor and wage management",
    RoleEnum.CUSTOMER: "Livestock & agri-product marketplace consumer",
}


class OwnershipTypeEnum(str, Enum):
    """Farm ownership types supported in the Agri-Smart Ecosystem."""
    OWNED = "OWNED"
    LEASED = "LEASED"
    SHARED = "SHARED"
    MANAGED = "MANAGED"


class LandAreaUnitEnum(str, Enum):
    """Land area measurement units."""
    ACRE = "ACRE"
    HECTARE = "HECTARE"
    SQUARE_METER = "SQUARE_METER"


class CropCategory(str, Enum):
    """Agricultural crop classification categories."""
    CEREAL = "CEREAL"
    PULSE = "PULSE"
    OILSEED = "OILSEED"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    FIBER = "FIBER"
    SPICE = "SPICE"
    PLANTATION = "PLANTATION"
    OTHER = "OTHER"


class CropSeason(str, Enum):
    """Agricultural cultivation seasons."""
    KHARIF = "KHARIF"
    RABI = "RABI"
    ZAID = "ZAID"
    YEAR_ROUND = "YEAR_ROUND"
    OTHER = "OTHER"


class StageStatus(str, Enum):
    """Cultivation stage progression statuses."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class ExpenseCategory(str, Enum):
    """Itemized stage expense categories."""
    LABOR = "LABOR"
    INPUT_MATERIAL = "INPUT_MATERIAL"
    MACHINERY = "MACHINERY"


class PaymentMode(str, Enum):
    """Payment settlement modes."""
    CASH = "CASH"
    UPI = "UPI"
    CREDIT_PENDING = "CREDIT_PENDING"


class MachineryOwnership(str, Enum):
    """Machinery usage classifications."""
    OWNED = "OWNED"
    RENTAL = "RENTAL"


class InputCategory(str, Enum):
    """Agricultural input categories."""
    SEED = "SEED"
    FERTILIZER = "FERTILIZER"
    PESTICIDE = "PESTICIDE"
    BIO_INPUT = "BIO_INPUT"
    EQUIPMENT_TOOL = "EQUIPMENT_TOOL"
    IRRIGATION_SUPPLY = "IRRIGATION_SUPPLY"
    OTHER = "OTHER"


class InputUnit(str, Enum):
    """Measurement units for agricultural inputs."""
    KG = "KG"
    GRAM = "GRAM"
    LITRE = "LITRE"
    ML = "ML"
    BAG = "BAG"
    PACKET = "PACKET"
    BOTTLE = "BOTTLE"
    PIECE = "PIECE"
    TONNE = "TONNE"


class ProcurementStatus(str, Enum):
    """Procurement request workflow statuses."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class SupplierType(str, Enum):
    """Agricultural supplier business types."""
    DISTRIBUTOR = "DISTRIBUTOR"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"
    COOPERATIVE = "COOPERATIVE"
    OTHER = "OTHER"


class FarmingMethod(str, Enum):
    """Farming methodology classification."""
    CONVENTIONAL = "CONVENTIONAL"  # ரசாயனம் / வழக்கமானது
    ORGANIC = "ORGANIC"            # இயற்கை விவசாயம்
    NATURAL = "NATURAL"            # ஜீரோ பட்ஜெட் இயற்கை விவசாயம்
    HYBRID = "HYBRID"              # ஒருங்கிணைந்த முறை


class WorkerPaymentStatus(str, Enum):
    """Wage payment settlement status."""
    PAID = "PAID"                  # கொடுத்தாச்சு
    PENDING = "PENDING"            # பாக்கி
    PARTIALLY_PAID = "PARTIALLY_PAID"


class WorkerGender(str, Enum):
    """Worker gender classification."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class WorkerSkill(str, Enum):
    """Worker skill specialization."""
    LAND_PREPARATION = "LAND_PREPARATION"
    SEEDING = "SEEDING"
    WEEDING = "WEEDING"
    IRRIGATION = "IRRIGATION"
    FERTILIZATION = "FERTILIZATION"
    PEST_MANAGEMENT = "PEST_MANAGEMENT"
    HARVESTING = "HARVESTING"
    GENERAL_LABOR = "GENERAL_LABOR"
    MACHINE_OPERATOR = "MACHINE_OPERATOR"
    OTHER = "OTHER"


class MachineType(str, Enum):
    """Agricultural machine categories."""
    TRACTOR = "TRACTOR"
    HARVESTER = "HARVESTER"
    POWER_TILLER = "POWER_TILLER"
    WATER_PUMP = "WATER_PUMP"
    SPRAYER = "SPRAYER"
    SEEDER = "SEEDER"
    THRESHER = "THRESHER"
    ROTAVATOR = "ROTAVATOR"
    OTHER = "OTHER"


class BillType(str, Enum):
    """Billing classification types."""
    STAGE_CONSOLIDATED = "STAGE_CONSOLIDATED"
    WORKER_PAYMENT = "WORKER_PAYMENT"
    MACHINE_COST = "MACHINE_COST"
    MATERIAL_PURCHASE = "MATERIAL_PURCHASE"
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"
    LOGISTICS_COST = "LOGISTICS_COST"
    OTHER_EXPENSE = "OTHER_EXPENSE"


class BillStatus(str, Enum):
    """Bill payment statuses."""
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    """Supported payment settlement methods."""
    UPI = "UPI"
    NET_BANKING = "NET_BANKING"
    CASH = "CASH"


class PaymentStatus(str, Enum):
    """Payment transaction statuses."""
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class LogisticsStatus(str, Enum):
    """Logistics dispatch tracking statuses."""
    PLANNED = "PLANNED"
    PICKUP_SCHEDULED = "PICKUP_SCHEDULED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class NotificationStatus(str, Enum):
    """Notification transmission statuses."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationType(str, Enum):
    """Notification trigger event types."""
    WORK_COMPLETED_PAYMENT = "WORK_COMPLETED_PAYMENT"
    BILL_ISSUED = "BILL_ISSUED"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"
    STAGE_ALERT = "STAGE_ALERT"
    YIELD_HARVEST_ALERT = "YIELD_HARVEST_ALERT"
    SEASONAL_SEED_USAGE_REMINDER = "SEASONAL_SEED_USAGE_REMINDER"


class LivestockSellingModel(str, Enum):
    """Selling models supported for livestock."""
    INDIVIDUAL = "INDIVIDUAL"   # Single tagged animal (Goat, Cow, etc.)
    QUANTITY = "QUANTITY"       # Batch/flock of animals (Chickens, Ducks, etc.)
    BATCH = "BATCH"             # Synonym for QUANTITY / Batch


class LivestockGender(str, Enum):
    """Gender classification for livestock."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"
    MIXED_HERD = "MIXED_HERD"
    MIXED = "MIXED"
    UNSPECIFIED = "UNSPECIFIED"


class LivestockStatus(str, Enum):
    """Livestock publication & inventory status."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"
    ARCHIVED = "ARCHIVED"


class LivestockHealthStatus(str, Enum):
    """Livestock health condition."""
    HEALTHY = "HEALTHY"
    UNDER_TREATMENT = "UNDER_TREATMENT"
    VACCINATED = "VACCINATED"
    QUARANTINED = "QUARANTINED"


class LivestockVaccinationStatus(str, Enum):
    """Vaccination compliance status."""
    UP_TO_DATE = "UP_TO_DATE"
    PARTIAL = "PARTIAL"
    NOT_VACCINATED = "NOT_VACCINATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LivestockPriceType(str, Enum):
    """Pricing calculation models."""
    PER_UNIT = "PER_UNIT"
    PER_KG = "PER_KG"
    FIXED_TOTAL = "FIXED_TOTAL"


class LivestockAgeUnit(str, Enum):
    """Age measurement units."""
    DAYS = "DAYS"
    WEEKS = "WEEKS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"


class LivestockWeightUnit(str, Enum):
    """Weight measurement units."""
    KG = "KG"
    GRAM = "GRAM"
    TONNE = "TONNE"


class LivestockImageType(str, Enum):
    """Livestock image angle & document classifications."""
    MAIN = "MAIN"
    FRONT = "FRONT"
    SIDE = "SIDE"
    BACK = "BACK"
    FACE = "FACE"
    ENVIRONMENT = "ENVIRONMENT"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class MarketplaceOrderStatus(str, Enum):
    """Marketplace customer order fulfillment lifecycle."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FARMER_ACCEPTED = "FARMER_ACCEPTED"
    FARMER_REJECTED = "FARMER_REJECTED"
    PROCESSING = "PROCESSING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"


class MarketplacePaymentStatus(str, Enum):
    """Payment transaction states."""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class MarketplacePaymentMethod(str, Enum):
    """Supported payment settlement methods for marketplace orders."""
    UPI = "UPI"
    NET_BANKING = "NET_BANKING"
    CARD = "CARD"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"


class MarketplaceDeliveryType(str, Enum):
    """Fulfillment delivery mechanisms."""
    FARM_PICKUP = "FARM_PICKUP"
    FARMER_DELIVERY = "FARMER_DELIVERY"
    LOGISTICS_PARTNER = "LOGISTICS_PARTNER"


class MarketplaceDeliveryStatus(str, Enum):
    """Marketplace delivery dispatch progression."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"



class ToolInterestType(str, Enum):
    """Agricultural demand and supply requirement types."""
    FERTILIZER = "FERTILIZER"           # Urea, DAP, NPK, Potash, Micronutrients, Bio-fertilizers
    SEEDS = "SEEDS"                     # Certified Paddy, Maize, Wheat, Vegetable seeds & saplings
    PESTICIDE = "PESTICIDE"             # Insecticides, Fungicides, Weedicides, Neem oil
    AGRI_INPUTS = "AGRI_INPUTS"         # General Agro-inputs & farm consumables
    RENTAL = "RENTAL"                   # Machinery & Tractor Custom Hire / Rental
    PURCHASE = "PURCHASE"               # Direct Dealership / Purchase
    IRRIGATION_HARDWARE = "IRRIGATION_HARDWARE"  # Drip kits, Sprinklers, Pumps, PVC pipes
    LIVESTOCK_FEED = "LIVESTOCK_FEED"   # Cattle feed, Poultry feed, Silage, Minerals
    TRADER_COMMODITY = "TRADER_COMMODITY" # APMC Mandi, Grain traders, Wholesale stockists
    SERVICE_REPAIR = "SERVICE_REPAIR"   # Machinery repair, tractor service & spares
    OPERATOR_HIRE = "OPERATOR_HIRE"     # Machinery with skilled operator
    OTHER = "OTHER"


class ToolInterestStatus(str, Enum):
    """Lifecycle status of a farmer's tool interest and discovery."""
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


# Backward compatibility aliases
CropCategoryEnum = CropCategory
CropSeasonEnum = CropSeason
StageStatusEnum = StageStatus
ExpenseCategoryEnum = ExpenseCategory
PaymentModeEnum = PaymentMode
MachineryOwnershipEnum = MachineryOwnership
InputCategoryEnum = InputCategory
InputUnitEnum = InputUnit
ProcurementStatusEnum = ProcurementStatus
SupplierTypeEnum = SupplierType
FarmingMethodEnum = FarmingMethod
WorkerPaymentStatusEnum = WorkerPaymentStatus
WorkerGenderEnum = WorkerGender
WorkerSkillEnum = WorkerSkill
MachineTypeEnum = MachineType
BillTypeEnum = BillType
BillStatusEnum = BillStatus
PaymentMethodEnum = PaymentMethod
PaymentStatusEnum = PaymentStatus
LogisticsStatusEnum = LogisticsStatus
NotificationStatusEnum = NotificationStatus
NotificationTypeEnum = NotificationType
LivestockSellingModelEnum = LivestockSellingModel
LivestockGenderEnum = LivestockGender
LivestockStatusEnum = LivestockStatus
LivestockHealthStatusEnum = LivestockHealthStatus
LivestockVaccinationStatusEnum = LivestockVaccinationStatus
LivestockPriceTypeEnum = LivestockPriceType
LivestockAgeUnitEnum = LivestockAgeUnit
LivestockWeightUnitEnum = LivestockWeightUnit
LivestockImageTypeEnum = LivestockImageType
MarketplaceOrderStatusEnum = MarketplaceOrderStatus
MarketplacePaymentStatusEnum = MarketplacePaymentStatus
MarketplacePaymentMethodEnum = MarketplacePaymentMethod
MarketplaceDeliveryTypeEnum = MarketplaceDeliveryType
MarketplaceDeliveryStatusEnum = MarketplaceDeliveryStatus
ToolInterestTypeEnum = ToolInterestType
ToolInterestStatusEnum = ToolInterestStatus

class ShipmentStatus(str, Enum):
    """Fulfillment & logistics shipment statuses."""
    CREATED = "CREATED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKUP_ASSIGNED = "PICKUP_ASSIGNED"
    PICKED_UP = "PICKED_UP"
    AT_ORIGIN_HUB = "AT_ORIGIN_HUB"
    IN_TRANSIT = "IN_TRANSIT"
    AT_DESTINATION_HUB = "AT_DESTINATION_HUB"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    RETURN_INITIATED = "RETURN_INITIATED"
    RETURN_IN_TRANSIT = "RETURN_IN_TRANSIT"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class SpecialHandlingType(str, Enum):
    """Special handling requirements for agricultural produce and livestock."""
    GENERAL = "GENERAL"
    KEEP_COOL = "KEEP_COOL"
    KEEP_DRY = "KEEP_DRY"
    FRAGILE = "FRAGILE"
    PERISHABLE = "PERISHABLE"
    LIVE_PLANT = "LIVE_PLANT"
    DIRECT_FARM = "DIRECT_FARM"


class PackageType(str, Enum):
    """Packaging container types."""
    JUTE_BAG = "JUTE_BAG"
    PLASTIC_CRATE = "PLASTIC_CRATE"
    WOODEN_BOX = "WOODEN_BOX"
    CORRUGATED_CARTON = "CORRUGATED_CARTON"
    SACK = "SACK"
    CAN = "CAN"
    BUNDLE = "BUNDLE"
    OTHER = "OTHER"


class PickupRequestStatus(str, Enum):
    """Transport pickup request status."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PickupTimeWindow(str, Enum):
    """Scheduled pickup time windows."""
    MORNING_7_11 = "MORNING_7_11"
    AFTERNOON_12_4 = "AFTERNOON_12_4"
    EVENING_4_8 = "EVENING_4_8"
    ANYTIME = "ANYTIME"


class DeliveryAttemptStatus(str, Enum):
    """Delivery attempt outcomes."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RESCHEDULED = "RESCHEDULED"


class DeliveryFailureReason(str, Enum):
    """Delivery failure reasons."""
    CUSTOMER_UNAVAILABLE = "CUSTOMER_UNAVAILABLE"
    INCORRECT_ADDRESS = "INCORRECT_ADDRESS"
    CUSTOMER_REJECTED = "CUSTOMER_REJECTED"
    PACKAGE_DAMAGED = "PACKAGE_DAMAGED"
    TRANSPORT_ISSUE = "TRANSPORT_ISSUE"
    WEATHER_DELAY = "WEATHER_DELAY"
    OTHER = "OTHER"


# Backward compatibility aliases
ShipmentStatusEnum = ShipmentStatus
SpecialHandlingTypeEnum = SpecialHandlingType
PackageTypeEnum = PackageType
PickupRequestStatusEnum = PickupRequestStatus
PickupTimeWindowEnum = PickupTimeWindow
DeliveryAttemptStatusEnum = DeliveryAttemptStatus
DeliveryFailureReasonEnum = DeliveryFailureReason

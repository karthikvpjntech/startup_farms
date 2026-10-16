import logging
from sqlalchemy import inspect, text
from app.core.database import engine, Base

logger = logging.getLogger("agri_smart.schema_sync")


def sync_database_schema() -> None:
    """
    Safely creates all database tables and ensures newly added model columns
    are altered into existing tables (vital for SQLite & dev databases).
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Base.metadata.create_all note: %s", e)

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        with engine.begin() as conn:
            # 1. users table
            if "users" in tables:
                cols = [c["name"] for c in inspector.get_columns("users")]
                if "is_two_factor_enabled" not in cols:
                    logger.info("Adding is_two_factor_enabled to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_two_factor_enabled BOOLEAN DEFAULT 0 NOT NULL"))
                if "two_factor_method" not in cols:
                    logger.info("Adding two_factor_method to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_method VARCHAR(20) DEFAULT 'EMAIL' NOT NULL"))

            # 2. farmer_profiles table
            if "farmer_profiles" in tables:
                cols = [c["name"] for c in inspector.get_columns("farmer_profiles")]
                if "latitude" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN latitude NUMERIC(10, 7)"))
                if "longitude" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN longitude NUMERIC(10, 7)"))
                if "location_address" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN location_address VARCHAR(255)"))
                if "district" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN district VARCHAR(100)"))
                if "state" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN state VARCHAR(100)"))
                if "pincode" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN pincode VARCHAR(10)"))
                if "google_maps_url" not in cols:
                    conn.execute(text("ALTER TABLE farmer_profiles ADD COLUMN google_maps_url VARCHAR(500)"))

            # 3. farm_crop_plans table
            if "farm_crop_plans" in tables:
                cols = [c["name"] for c in inspector.get_columns("farm_crop_plans")]
                if "seed_variety" not in cols:
                    conn.execute(text("ALTER TABLE farm_crop_plans ADD COLUMN seed_variety VARCHAR(150)"))
                if "seed_rate" not in cols:
                    conn.execute(text("ALTER TABLE farm_crop_plans ADD COLUMN seed_rate NUMERIC(10, 2)"))
                if "seed_rate_unit" not in cols:
                    conn.execute(text("ALTER TABLE farm_crop_plans ADD COLUMN seed_rate_unit VARCHAR(50)"))

            # 4. produce_procurements table
            if "produce_procurements" in tables:
                cols = [c["name"] for c in inspector.get_columns("produce_procurements")]
                if "pickup_location" not in cols:
                    conn.execute(text("ALTER TABLE produce_procurements ADD COLUMN pickup_location VARCHAR(255)"))
                if "google_maps_url" not in cols:
                    conn.execute(text("ALTER TABLE produce_procurements ADD COLUMN google_maps_url VARCHAR(500)"))
                if "pickup_instructions" not in cols:
                    conn.execute(text("ALTER TABLE produce_procurements ADD COLUMN pickup_instructions TEXT"))
                if "whatsapp_url" not in cols:
                    conn.execute(text("ALTER TABLE produce_procurements ADD COLUMN whatsapp_url VARCHAR(500)"))

            # 5. marketplace_order_items table
            if "marketplace_order_items" in tables:
                cols = [c["name"] for c in inspector.get_columns("marketplace_order_items")]
                if "farm_product_id" not in cols:
                    conn.execute(text("ALTER TABLE marketplace_order_items ADD COLUMN farm_product_id CHAR(32)"))
                if "product_type" not in cols:
                    conn.execute(text("ALTER TABLE marketplace_order_items ADD COLUMN product_type VARCHAR(30) DEFAULT 'LIVESTOCK' NOT NULL"))
                if "variety_name" not in cols:
                    conn.execute(text("ALTER TABLE marketplace_order_items ADD COLUMN variety_name VARCHAR(150)"))
                if "unit" not in cols:
                    conn.execute(text("ALTER TABLE marketplace_order_items ADD COLUMN unit VARCHAR(50)"))

            # 6. cart_items table
            if "cart_items" in tables:
                cols = [c["name"] for c in inspector.get_columns("cart_items")]
                if "farm_product_id" not in cols:
                    conn.execute(text("ALTER TABLE cart_items ADD COLUMN farm_product_id CHAR(32)"))
                if "product_type" not in cols:
                    conn.execute(text("ALTER TABLE cart_items ADD COLUMN product_type VARCHAR(30) DEFAULT 'LIVESTOCK' NOT NULL"))

            # 7. crops table
            if "crops" in tables:
                cols = [c["name"] for c in inspector.get_columns("crops")]
                if "crop_name_local" not in cols:
                    conn.execute(text("ALTER TABLE crops ADD COLUMN crop_name_local VARCHAR(200)"))
                if "local_names" not in cols:
                    conn.execute(text("ALTER TABLE crops ADD COLUMN local_names JSON DEFAULT '{}'"))
                if "image_url" not in cols:
                    conn.execute(text("ALTER TABLE crops ADD COLUMN image_url VARCHAR(500)"))

            # 8. cultivation_stages table
            if "cultivation_stages" in tables:
                cols = [c["name"] for c in inspector.get_columns("cultivation_stages")]
                if "image_url" not in cols:
                    conn.execute(text("ALTER TABLE cultivation_stages ADD COLUMN image_url VARCHAR(500)"))

            # 9. farms table (survey number & survey record portal links)
            if "farms" in tables:
                cols = [c["name"] for c in inspector.get_columns("farms")]
                if "survey_number" not in cols:
                    logger.info("Adding survey_number column to farms table")
                    conn.execute(text("ALTER TABLE farms ADD COLUMN survey_number VARCHAR(100)"))
                if "survey_link" not in cols:
                    logger.info("Adding survey_link column to farms table")
                    conn.execute(text("ALTER TABLE farms ADD COLUMN survey_link VARCHAR(500)"))

        logger.info("Database schema synchronized successfully.")
    except Exception as e:
        logger.error("Error during schema synchronization: %s", e)

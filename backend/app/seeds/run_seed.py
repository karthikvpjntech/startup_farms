import logging
import sys
from app.core.database import SessionLocal, Base, engine
from sqlalchemy import text, inspect
from app.seeds.roles_seed import seed_roles
from app.seeds.super_admin_seed import seed_super_admin
from app.seeds.crop_stages_seed import seed_crop_stages
from app.seeds.inputs_suppliers_seed import seed_inputs_and_suppliers
from app.seeds.livestock_seed import seed_livestock_master

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("agri_smart.seeds")


def _ensure_schema(db) -> None:
    """Ensures tables and any newly added model columns exist across engines."""
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        if "crops" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("crops")]
            if "crop_name_local" not in columns:
                db.execute(text("ALTER TABLE crops ADD COLUMN crop_name_local VARCHAR(200)"))
                db.commit()
            if "local_names" not in columns:
                db.execute(text("ALTER TABLE crops ADD COLUMN local_names JSON DEFAULT '{}'"))
                db.commit()
            if "image_url" not in columns:
                db.execute(text("ALTER TABLE crops ADD COLUMN image_url VARCHAR(500)"))
                db.commit()
        if "cultivation_stages" in inspector.get_table_names():
            stage_columns = [c["name"] for c in inspector.get_columns("cultivation_stages")]
            if "image_url" not in stage_columns:
                db.execute(text("ALTER TABLE cultivation_stages ADD COLUMN image_url VARCHAR(500)"))
                db.commit()
    except Exception as e:
        logger.warning("Schema inspection note: %s", e)
        db.rollback()


def run_all_seeds() -> None:
    """
    Executes all database seeders in sequence:
    1. Default System Roles (SUPER_ADMIN, FARMER, TRADER, DRIVER, WORKER, CUSTOMER)
    2. Initial Root SUPER_ADMIN User
    3. Crop Master & Dynamic Cultivation Process Stages
    4. Agricultural Inputs Catalog & Verified Suppliers
    5. Livestock Master Categories & Breeds Taxonomy
    """
    logger.info("=== Starting Agri-Smart Database Seed Process ===")
    db = SessionLocal()
    try:
        _ensure_schema(db)

        # Step 1: Seed default roles
        roles_result = seed_roles(db)
        logger.info(
            "Roles summary: %d created, %d existing",
            len(roles_result["created"]),
            len(roles_result["existing"])
        )

        # Step 2: Seed Super Admin user
        admin_result = seed_super_admin(db)
        logger.info("Super Admin status: %s", admin_result["message"])

        # Step 3: Seed Onion Master & Cultivation Process Stages
        stages_result = seed_crop_stages(db)
        total_stg = stages_result.get("total_stages", stages_result.get("stages_created", 0) + stages_result.get("stages_updated", 0))
        logger.info("Crop Stages status: %s (Total %d stages)", stages_result.get("crop_name", "Crops"), total_stg)

        # Step 4: Seed Agricultural Inputs & Suppliers
        inputs_suppliers_result = seed_inputs_and_suppliers(db)
        logger.info(
            "Inputs & Suppliers status: %d inputs (%d new), %d suppliers (%d new)",
            inputs_suppliers_result["inputs_created"] + inputs_suppliers_result["inputs_updated"],
            inputs_suppliers_result["inputs_created"],
            inputs_suppliers_result["suppliers_created"] + inputs_suppliers_result["suppliers_updated"],
            inputs_suppliers_result["suppliers_created"]
        )

        # Step 5: Seed Livestock Master Taxonomy
        livestock_result = seed_livestock_master(db)
        logger.info(
            "Livestock Master status: %d categories created, %d breeds created",
            livestock_result["categories_created"],
            livestock_result["breeds_created"]
        )

        logger.info("=== Database Seed Completed Successfully ===")
    except ValueError as val_err:
        logger.error("Configuration error during seeding: %s", val_err)
        sys.exit(1)
    except Exception as exc:
        logger.error("Unexpected error during seeding: %s", exc, exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeds()

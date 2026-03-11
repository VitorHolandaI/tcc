#!/usr/bin/env python3
"""
Migration script: Update submissoes table to use TEXT type for code fields
This preserves newlines, tabs, and indentation in student code submissions.

Run this script after updating the model to apply the migration.
"""
import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://testmaker:testmaker123@localhost:5432/testmaker"
)

def apply_migration():
    """Apply migration to update column types"""
    print(" Applying migration: submissoes table -> TEXT columns")
    print(f" Database: {DATABASE_URL}")
    print()

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            trans = conn.begin()

            try:
                print(" → Updating codigo_submetido to TEXT type...")
                conn.execute(text(
                    "ALTER TABLE submissoes ALTER COLUMN codigo_submetido TYPE TEXT"
                ))

                print(" → Updating resultado_execucao to TEXT type...")
                conn.execute(text(
                    "ALTER TABLE submissoes ALTER COLUMN resultado_execucao TYPE TEXT"
                ))

                trans.commit()
                print()
                print(" Migration applied successfully!")
                print()

                print(" Verifying column types:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = 'submissoes'
                    AND column_name IN ('codigo_submetido', 'resultado_execucao')
                    ORDER BY column_name
                """))

                for row in result:
                    col_name, data_type, max_length = row
                    length_info = f"({max_length})" if max_length else "(unlimited)"
                    print(f" {col_name}: {data_type} {length_info}")

            except Exception as e:
                trans.rollback()
                raise e

    except Exception as e:
        print(f"\n Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()

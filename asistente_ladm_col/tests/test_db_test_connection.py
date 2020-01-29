import nose2

from qgis.testing import (start_app,
                          unittest)

start_app() # need to start before asistente_ladm_col.tests.utils

from asistente_ladm_col.config.enums import (EnumTestConnectionMsg,
                                             EnumTestLevel)
from asistente_ladm_col.tests.utils import (get_gpkg_conn,
                                            get_pg_conn,
                                            restore_schema,
                                            get_gpkg_conn_from_path)


class TestDBTestConnection(unittest.TestCase):

    def test_pg_test_connection_interlis_ladm_col_models(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (Interlis, no LADM-COL models)...")

        restore_schema('test_ladm_all_models')
        db_pg = get_pg_conn('test_ladm_all_models')
        res, code, msg = db_pg.test_connection()
        self.assertTrue(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.SCHEMA_WITH_VALID_LADM_COL_STRUCTURE)
        db_pg.conn.close()


    def test_pg_test_connection_interlis_no_ladm_col_models(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (Interlis, no LADM-COL models)...")

        restore_schema('interlis_no_ladm')
        db_pg = get_pg_conn('interlis_no_ladm')
        res, code, msg = db_pg.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.NO_LADM_MODELS_FOUND)
        db_pg.conn.close()

    def test_pg_test_connection_no_interlis_no_ladm_col_models(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (no Interlis, no LADM-COL models)...")

        restore_schema('empty_no_interlis_no_ladm')
        db_pg = get_pg_conn('empty_no_interlis_no_ladm')
        res, code, msg = db_pg.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.INTERLIS_META_ATTRIBUTES_NOT_FOUND)
        db_pg.conn.close()

    def test_pg_test_connection_interlis_with_ili2pg3_ladm_col_221_models(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (Interlis with ili2pg 3, LADM-COL 2.2.1 models)...")

        restore_schema('interlis_ili2db3_ladm')
        db_pg = get_pg_conn('interlis_ili2db3_ladm')
        res, code, msg = db_pg.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(EnumTestConnectionMsg.INVALID_ILI2DB_VERSION, code)
        db_pg.conn.close()

    def test_pg_test_connection_bad_interlis_ladm_col_models(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (Bad Interlis, LADM-COL models)...")
        print("\nINFO: All records for t_ili2db_attrname table where removed...")

        restore_schema('bad_interlis_ladm')
        db_pg = get_pg_conn('bad_interlis_ladm')
        res, code, msg = db_pg.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.INTERLIS_META_ATTRIBUTES_NOT_FOUND)
        db_pg.conn.close()

    def test_pg_test_connection_interlis_ladm_col_models_upper_version(self):
        print("\nINFO: Validate test_connection() for PostgreSQL (Interlis, LADM-COL with higher models version)...")

        restore_schema('ladm_col_210')
        db_pg = get_pg_conn('ladm_col_210')
        res, code, msg = db_pg.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.NO_LADM_MODELS_FOUND)
        db_pg.conn.close()

    def test_gpkg_test_connection(self):
        print("\nINFO: Validate test_connection() for GeoPackage (model operation: OK!)...")
        db = get_gpkg_conn('test_ladm_operation_model_gpkg')
        res, code, msg = db.test_connection()
        self.assertTrue(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.DB_WITH_VALID_LADM_COL_STRUCTURE)

    def test_gpkg_test_connection_file_not_found(self):
        print("\nINFO: Validate test_connection() for GeoPackage (file not found)...")

        db = get_gpkg_conn_from_path('/tmp/a.gpkg')
        res, code, msg = db.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.GPKG_FILE_NOT_FOUND)

    def test_gpkg_test_connection_existing_file_no_interlis(self):
        print("\nINFO: Validate test_connection() for GeoPackage (existing file, no Interlis)...")

        db = get_gpkg_conn('no_interlis_gpkg')
        res, code, msg = db.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.INTERLIS_META_ATTRIBUTES_NOT_FOUND)

    def test_gpkg_test_connection_existing_file_schema_import(self):
        print("\nINFO: Validate test_connection() for GeoPackage (existing file, Schema Import)...")

        db = get_gpkg_conn('no_interlis_gpkg')
        res, code, msg = db.test_connection(EnumTestLevel.SCHEMA_IMPORT)
        self.assertTrue(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.CONNECTION_TO_DB_SUCCESSFUL_NO_LADM_COL)

    def test_gpkg_test_connection_interlis_no_ladm_col_models(self):
        print("\nINFO: Validate test_connection() for GeoPackage (Interlis, no LADM-COL models)...")

        db = get_gpkg_conn('interlis_no_ladm_col_models_gpkg')
        res, code, msg = db.test_connection()
        self.assertFalse(res, msg)
        self.assertEqual(code, EnumTestConnectionMsg.NO_LADM_MODELS_FOUND)

if __name__ == '__main__':
    nose2.main()
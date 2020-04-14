from asistente_ladm_col.config.mapping_config import QueryNames
from asistente_ladm_col.logic.ladm_col.qgis_ladm_query import QGISLADMQuery
from asistente_ladm_col.logic.ladm_col.config.queries.pg import (basic_query,
                                                                 economic_query,
                                                                 physical_query,
                                                                 legal_query,
                                                                 property_record_card_query)


class PGLADMQuery(QGISLADMQuery):
    def __init__(self):
        super(PGLADMQuery, self).__init__()

    @staticmethod
    def get_igac_basic_info(db, **kwargs):
        """
        Query by component: Basic info
        :param kwargs: dict with one of the following key-value param
               plot_t_ids
               parcel_fmi
               parcel_number
               previous_parcel_number
        :return:
        """
        params = QGISLADMQuery._get_parameters(kwargs)
        query = basic_query.get_igac_basic_query(schema=db.schema,
                                                 plot_t_ids=params[QueryNames.SEARCH_KEY_PLOT_T_IDS],
                                                 parcel_fmi=params[QueryNames.SEARCH_KEY_PARCEL_FMI],
                                                 parcel_number=params[QueryNames.SEARCH_KEY_PARCEL_NUMBER],
                                                 previous_parcel_number=params[QueryNames.SEARCH_KEY_PREVIOUS_PARCEL_NUMBER])
        return PGLADMQuery._get_query_results(db, query)

    @staticmethod
    def get_igac_legal_info(db, **kwargs):
        """
        Query by component: Legal info
        :param kwargs: dict with one of the following key-value param
               plot_t_ids
               parcel_fmi
               parcel_number
               previous_parcel_number
        :return:
        """
        params = QGISLADMQuery._get_parameters(kwargs)
        query = legal_query.get_igac_legal_query(schema=db.schema,
                                                 plot_t_ids=params[QueryNames.SEARCH_KEY_PLOT_T_IDS],
                                                 parcel_fmi=params[QueryNames.SEARCH_KEY_PARCEL_FMI],
                                                 parcel_number=params[QueryNames.SEARCH_KEY_PARCEL_NUMBER],
                                                 previous_parcel_number=params[QueryNames.SEARCH_KEY_PREVIOUS_PARCEL_NUMBER])
        return PGLADMQuery._get_query_results(db, query)

    @staticmethod
    def get_igac_property_record_card_info(db, **kwargs):
        """
        Query by component: Legal info
        :param kwargs: dict with one of the following key-value param
               plot_t_ids
               parcel_fmi
               parcel_number
               previous_parcel_number
        :return:
        """
        params = QGISLADMQuery._get_parameters(kwargs)
        query = property_record_card_query.get_igac_property_record_card_query(schema=db.schema,
                                                                               plot_t_ids=params[QueryNames.SEARCH_KEY_PLOT_T_IDS],
                                                                               parcel_fmi=params[QueryNames.SEARCH_KEY_PARCEL_FMI],
                                                                               parcel_number=params[QueryNames.SEARCH_KEY_PARCEL_NUMBER],
                                                                               previous_parcel_number=params[QueryNames.SEARCH_KEY_PREVIOUS_PARCEL_NUMBER])
        return PGLADMQuery._get_query_results(db, query)

    @staticmethod
    def get_igac_physical_info(db, **kwargs):
        """
        Query by component: Physical info
        :param kwargs: dict with one of the following key-value param
               plot_t_ids
               parcel_fmi
               parcel_number
               previous_parcel_number
        :return:
        """
        params = QGISLADMQuery._get_parameters(kwargs)
        query = physical_query.get_igac_physical_query(schema=db.schema,
                                                       plot_t_ids=params[QueryNames.SEARCH_KEY_PLOT_T_IDS],
                                                       parcel_fmi=params[QueryNames.SEARCH_KEY_PARCEL_FMI],
                                                       parcel_number=params[QueryNames.SEARCH_KEY_PARCEL_NUMBER],
                                                       previous_parcel_number=params[QueryNames.SEARCH_KEY_PREVIOUS_PARCEL_NUMBER])
        return PGLADMQuery._get_query_results(db, query)

    @staticmethod
    def get_igac_economic_info(db, **kwargs):
        """
        Query by component: Economic info
        :param kwargs: dict with one of the following key-value param
               plot_t_ids
               parcel_fmi
               parcel_number
               previous_parcel_number
        :return:
        """
        params = QGISLADMQuery._get_parameters(kwargs)
        query = economic_query.get_igac_economic_query(schema=db.schema,
                                                       plot_t_ids=params[QueryNames.SEARCH_KEY_PLOT_T_IDS],
                                                       parcel_fmi=params[QueryNames.SEARCH_KEY_PARCEL_FMI],
                                                       parcel_number=params[QueryNames.SEARCH_KEY_PARCEL_NUMBER],
                                                       previous_parcel_number=params[QueryNames.SEARCH_KEY_PREVIOUS_PARCEL_NUMBER])
        return PGLADMQuery._get_query_results(db, query)

    @staticmethod
    def _get_query_results(db, query):
        res, msg = db.check_and_fix_connection()
        if not res:
            return None
        cur = db.conn.cursor()
        cur.execute(query)
        query_result = cur.fetchone()[0]

        # self.logger.debug(__name__, "QUERY:".format(query))
        return query_result
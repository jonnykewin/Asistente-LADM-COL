# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2019-12-20
        git sha              : :%H$
        copyright            : (C) 2019 by Leo Cardona (BSF Swissphoto)
        email                : leo.cardona.p@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import QgsProject
from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QMessageBox,
                                 QPushButton,
                                 QSizePolicy)
from qgis.gui import QgsMessageBar

from asistente_ladm_col.config.general_config import (SUPPLIES_DB_SOURCE,
                                                      COLLECTED_DB_SOURCE,
                                                      SETTINGS_CONNECTION_TAB_INDEX)
from asistente_ladm_col.config.mapping_config import LADMNames
from asistente_ladm_col.gui.dialogs.dlg_settings import SettingsDialog
from asistente_ladm_col.lib.logger import Logger
from asistente_ladm_col.utils import get_ui_class
from asistente_ladm_col.config.help_strings import HelpStrings

DIALOG_UI = get_ui_class('change_detection/dlg_change_detection_settings.ui')


class ChangeDetectionSettingsDialog(QDialog, DIALOG_UI):
    CHANGE_DETECTIONS_MODE_SUPPLIES_MODEL = "CHANGE_DETECTIONS_MODE_SUPPLIES_MODEL"
    CHANGE_DETECTIONS_MODES = {CHANGE_DETECTIONS_MODE_SUPPLIES_MODEL: QCoreApplication.translate("ChangeDetectionSettingsDialog", "Change detection supplies model")}

    def __init__(self, parent=None, qgis_utils=None, conn_manager=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.logger = Logger()
        self.help_strings = HelpStrings()
        self.txt_help_page.setHtml(self.help_strings.CHANGE_DETECTION_SETTING_DIALOG_HELP)

        self.conn_manager = conn_manager
        self.qgis_utils = qgis_utils

        # we will use a unique instance of setting dialog
        self.settings_dialog = SettingsDialog(qgis_utils=self.qgis_utils, conn_manager=self.conn_manager)
        # The database configuration is saved if it becomes necessary
        # to restore the configuration when the user rejects the dialog
        self._init_db_collected_active_mode = None
        self._init_db_supplies_active_mode = None
        self._init_db_collected_dict_config = dict()
        self._init_db_supplies_dict_config = dict()
        self.set_init_db_config()  # Always call after the settings_dialog variable is set

        self._db_collected = self.conn_manager.get_db_connector_from_source()
        self._db_supplies = self.conn_manager.get_db_connector_from_source(SUPPLIES_DB_SOURCE)

        # There may be 1 case where we need to emit a db_connection_changed from the change detection settings dialog:
        #   1) Connection Settings was opened and the DB conn was changed.
        self._db_collected_was_changed = False  # To postpone calling refresh gui until we close this dialog instead of settings
        self._db_supplies_was_changed = False

        # Similarly, we could call a refresh on layers and relations cache in 1 case:
        #   1) If the change detection settings dialog was called for the COLLECTED source: opening Connection Settings
        #      and changing the DB connection.
        self._schedule_layers_and_relations_refresh = False

        for mode, label_mode in self.CHANGE_DETECTIONS_MODES.items():
            self.cbo_change_detection_modes.addItem(label_mode, mode)

        self.radio_button_other_db.setChecked(True)  # Default option
        self.radio_button_same_db.setEnabled(True)
        if not self._db_collected.supplies_model_exists():
            self.radio_button_same_db.setEnabled(False)

        self.radio_button_same_db.toggled.connect(self.update_supplies_db_options)
        self.update_supplies_db_options()

        self.btn_collected_db.clicked.connect(self.show_settings_collected_db)
        self.btn_supplies_db.clicked.connect(self.show_settings_supplies_db)

        # Default color error labels
        self.lbl_msg_collected.setStyleSheet('color: orange')
        self.lbl_msg_supplies.setStyleSheet('color: orange')

        # Set connections
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.helpRequested.connect(self.show_help)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.update_connection_info(COLLECTED_DB_SOURCE)
        self.update_connection_info(SUPPLIES_DB_SOURCE)

    def set_init_db_config(self):
        """
         A copy of the initial connections to the database is made,
         User can change the initial connections and then cancel the changes.
         Initial connections need to be re-established
        """
        # get init db for collected db source
        self.settings_dialog.set_db_source(COLLECTED_DB_SOURCE)
        self._init_db_collected_active_mode = self.settings_dialog.cbo_db_engine.itemData(self.settings_dialog.cbo_db_engine.currentIndex())

        for id_db, db_factory in self.settings_dialog._lst_db.items():
            dict_conn = db_factory.get_parameters_conn(COLLECTED_DB_SOURCE)
            self._init_db_collected_dict_config[id_db] = dict_conn

        # get init db for supplies db source
        self.settings_dialog.set_db_source(SUPPLIES_DB_SOURCE)
        self._init_db_supplies_active_mode = self.settings_dialog.cbo_db_engine.itemData(self.settings_dialog.cbo_db_engine.currentIndex())

        for id_db, db_factory in self.settings_dialog._lst_db.items():
            dict_conn = db_factory.get_parameters_conn(SUPPLIES_DB_SOURCE)
            self._init_db_supplies_dict_config[id_db] = dict_conn

    def update_supplies_db_options(self):
        if self.radio_button_same_db.isChecked():
            self.btn_supplies_db.setEnabled(False)
        else:
            self.btn_supplies_db.setEnabled(True)
        self.update_connection_info(SUPPLIES_DB_SOURCE)

    def show_settings_collected_db(self):
        self.settings_dialog.set_db_source(COLLECTED_DB_SOURCE)
        self.settings_dialog.set_tab_pages_list([SETTINGS_CONNECTION_TAB_INDEX])
        self.settings_dialog.set_required_models([LADMNames.OPERATION_MODEL_PREFIX])
        self.settings_dialog.db_connection_changed.connect(self.db_connection_changed)

        if self.settings_dialog.exec_():
            self._db_collected = self.settings_dialog.get_db_connection()
            self.update_connection_info(COLLECTED_DB_SOURCE)
        self.settings_dialog.db_connection_changed.disconnect(self.db_connection_changed)

    def show_settings_supplies_db(self):
        self.settings_dialog.set_db_source(SUPPLIES_DB_SOURCE)
        self.settings_dialog.set_tab_pages_list([SETTINGS_CONNECTION_TAB_INDEX])
        self.settings_dialog.set_required_models([LADMNames.SUPPLIES_MODEL_PREFIX])
        self.settings_dialog.db_connection_changed.connect(self.db_connection_changed)

        if self.settings_dialog.exec_():
            self._db_supplies = self.settings_dialog.get_db_connection()
            self.update_connection_info(SUPPLIES_DB_SOURCE)
        self.settings_dialog.db_connection_changed.disconnect(self.db_connection_changed)

    def db_connection_changed(self, db, ladm_col_db, db_source):
        # We dismiss parameters here, after all, we already have the db, and the ladm_col_db
        # may change from this moment until we close the import schema dialog
        if db_source == COLLECTED_DB_SOURCE:
            self._db_collected_was_changed = True
            self._schedule_layers_and_relations_refresh = True
        else:
            self._db_supplies_was_changed = True

    def close_dialog(self):
        """
        We use this method to be safe when emitting the db_connection_changed, otherwise we could trigger slots that
        unload the plugin, destroying dialogs and thus, leading to crashes.
        """
        if self._schedule_layers_and_relations_refresh:
            self.conn_manager.db_connection_changed.connect(self.qgis_utils.cache_layers_and_relations)

        if self._db_collected_was_changed:
            self.conn_manager.db_connection_changed.emit(self._db_collected, self._db_collected.test_connection()[0], COLLECTED_DB_SOURCE)

        if self._db_supplies_was_changed:
            self.conn_manager.db_connection_changed.emit(self._db_supplies, self._db_supplies.test_connection()[0], SUPPLIES_DB_SOURCE)

        if self._schedule_layers_and_relations_refresh:
            self.conn_manager.db_connection_changed.disconnect(self.qgis_utils.cache_layers_and_relations)

        self.logger.info(__name__, "Dialog closed.")
        self.show_message_change_detection_settings()  # Show information message indicating whether setting is OK
        self.done(QDialog.Accepted)

    def update_connection_info(self, db_source):
        # Validate db connections
        self.lbl_msg_collected.setText("")
        self.lbl_msg_supplies.setText("")
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        if self._db_collected.test_connection()[0] and self.radio_button_same_db.isChecked():
            if not self._db_collected.operation_model_exists():
                self.lbl_msg_collected.setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Warning: DB connection is not valid"))
                self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            else:
                self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        if self._db_collected.test_connection()[0] and self._db_supplies.test_connection()[0]:
            if not self._db_supplies.supplies_model_exists() or not self._db_collected.operation_model_exists():
                if not self._db_collected.operation_model_exists():
                    self.lbl_msg_collected.setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Warning: DB connection is not valid"))
                    self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

                if not self._db_supplies.supplies_model_exists():
                    self.lbl_msg_supplies.setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Warning: DB connection is not valid"))
                    self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            else:
                self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

        # validate selected db
        if self._db_collected.supplies_model_exists():
            self.radio_button_same_db.setEnabled(True)
            if self.radio_button_same_db.isChecked():
                self.db_supplies_connect_label.setText(self.db_collected_connect_label.text())
        else:
            self.radio_button_same_db.setEnabled(False)
            if self.radio_button_same_db.isChecked():
                self.radio_button_same_db.setChecked(False) # signal update the label

        if db_source == COLLECTED_DB_SOURCE:
            db_description = self._db_collected.get_description_conn_string()
            if db_description:
                self.db_collected_connect_label.setText(db_description)
                self.db_collected_connect_label.setToolTip(self._db_collected.get_display_conn_string())
            else:
                self.db_collected_connect_label.setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "The database is not defined!"))
                self.db_collected_connect_label.setToolTip('')
        elif db_source == SUPPLIES_DB_SOURCE:
            if self.radio_button_same_db.isChecked():
                self.db_supplies_connect_label.setText(self.db_collected_connect_label.text())
            else:
                db_description = self._db_supplies.get_description_conn_string()
                if db_description:
                    self.db_supplies_connect_label.setText(db_description)
                    self.db_supplies_connect_label.setToolTip(self._db_supplies.get_display_conn_string())
                else:
                    self.db_supplies_connect_label.setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "The database is not defined!"))
                    self.db_supplies_connect_label.setToolTip('')

    def accepted(self):
        """
        Confirm changes in db connections.
        If user select collected db as supplies db we update supplies db connection with collected db connection

        If there are layers load in canvas from a previous connection that changed, we ask to user
        if he want clean the canvas or preserving layers.

        if neither of the connections changed, the dialog is closed and a info message is displayed
        """
        if self.radio_button_same_db.isChecked():
            # Get collected db dict config
            self.settings_dialog.set_db_source(COLLECTED_DB_SOURCE)
            db_collected_active_mode = self.settings_dialog.cbo_db_engine.itemData(self.settings_dialog.cbo_db_engine.currentIndex())
            db_collected_dict_conn = dict()

            for id_db, db_factory in self.settings_dialog._lst_db.items():
                if id_db == db_collected_active_mode:
                    dict_conn = db_factory.get_parameters_conn(COLLECTED_DB_SOURCE)
                    db_collected_dict_conn[id_db] = dict_conn

            self.settings_dialog.set_db_source(SUPPLIES_DB_SOURCE)
            self.settings_dialog.set_db_connection(db_collected_active_mode, db_collected_dict_conn[db_collected_active_mode])

            self._db_supplies = self.settings_dialog.get_db_connection()
            self.conn_manager.db_connection_changed.emit(self._db_supplies, self._db_supplies.test_connection()[0], SUPPLIES_DB_SOURCE)

        if self._db_collected_was_changed or self._db_supplies_was_changed:
            if list(QgsProject.instance().mapLayers().values()):
                message = ""
                if self._db_collected_was_changed and self._db_supplies_was_changed:
                    message = "The connection of the collected and supplies databases has changed,"
                elif self._db_collected_was_changed:
                    message = "The collected database connection has changed,"
                elif self._db_supplies_was_changed:
                    message = "The supplies database connection has changed,"

                message += " do you want to remove the layers that are currently loaded in QGIS?"
                self.show_message_clean_layers_panel(message)
                self.show_message_change_detection_settings()  # Show information message indicating whether setting is OK
            else:
                self.close_dialog()
        else:
            # Connections have not changed
            self.close_dialog()

    def show_message_change_detection_settings(self):
        if not self._db_collected.operation_model_exists() and not self._db_supplies.supplies_model_exists():
            message = QCoreApplication.translate("ChangeDetectionSettingsDialog", "You don't have configured both Collected and Supplies database connections, you must first configure them before proceeding to detect changes.")
            self.logger.warning_msg(__name__, message)
        elif not self._db_collected.operation_model_exists() or not self._db_supplies.supplies_model_exists():

            if not self._db_collected.operation_model_exists():
                message = QCoreApplication.translate("ChangeDetectionSettingsDialog", "You don't have configured Collected database connections, you must first configure it before proceeding to detect changes.")
                self.logger.warning_msg(__name__, message)

            if not self._db_supplies.supplies_model_exists():
                message = QCoreApplication.translate("ChangeDetectionSettingsDialog", "You don't have configured Supplies database connections, you must first configure it before proceeding to detect changes.")
                self.logger.warning_msg(__name__, message)
        else:
            message = QCoreApplication.translate("ChangeDetectionSettingsDialog", "You have configured both Collected and Supplies database connections, now you can proceed to detect changes.")
            self.logger.message_with_buttons_change_detection_all_and_per_parcel_emitted.emit(message)


    def show_message_clean_layers_panel(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setText(message)
        msg.setWindowTitle(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Remove layers?"))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Yes, remove layers"))
        msg.button(QMessageBox.No).setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "No, don't remove"))
        msg.button(QMessageBox.Cancel).setText(QCoreApplication.translate("ChangeDetectionSettingsDialog", "Cancel"))
        reply = msg.exec_()

        if reply == QMessageBox.Yes:
            QgsProject.instance().layerTreeRoot().removeAllChildren()
            self.close_dialog()
        elif reply == QMessageBox.No:
            self.close_dialog()
        elif reply == QMessageBox.Cancel:
            pass  # Continue config db connections

    def reject(self):
        """
        The user discarded changes, so go back to initial state.
        """
        if self._db_collected_was_changed:
            self.settings_dialog.set_db_source(COLLECTED_DB_SOURCE)
            self.settings_dialog.set_db_connection(self._init_db_collected_active_mode, self._init_db_collected_dict_config[self._init_db_collected_active_mode])
            self._db_collected = self.settings_dialog.get_db_connection()
            self.conn_manager.db_connection_changed.emit(self._db_collected, self._db_collected.test_connection()[0], COLLECTED_DB_SOURCE)

        if self._db_supplies_was_changed:
            self.settings_dialog.set_db_source(SUPPLIES_DB_SOURCE)
            self.settings_dialog.set_db_connection(self._init_db_supplies_active_mode, self._init_db_supplies_dict_config[self._init_db_supplies_active_mode])
            self._db_supplies = self.settings_dialog.get_db_connection()
            self.conn_manager.db_connection_changed.emit(self._db_supplies, self._db_supplies.test_connection()[0], SUPPLIES_DB_SOURCE)

        self.show_message_change_detection_settings()  # Show information message indicating whether setting is OK
        self.done(QDialog.Rejected)

    def show_help(self):
        self.qgis_utils.show_help("change_detection_settings")

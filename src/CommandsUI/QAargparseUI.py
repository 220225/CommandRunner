from dataclasses import fields, MISSING
from typing import Any, Dict

import Core
from CommandBase import CommandUIBase
from qargparse import qargparse

logger = Core.get_logger()


class QAargparseUI(CommandUIBase):
    def __init__(self, cmd_cls):
        super().__init__(cmd_cls)

        self._data_filelds = []

    def on_parameter_changed(self, arg):
        pass

    def rebuild_ui(self):
        style = qargparse.DefaultStyle.copy()
        style["comboboxFillWidth"] = True
        self.ui = qargparse.QArgumentParser(style=style)

        base_height = 40

        if not self._cmd_cls:
            raise ValueError("Command class is not defined")

        self.data_fields = fields(self._cmd_cls)
        for data_field in self.data_fields:

            if 'items' in data_field.metadata:
                field_type = type(data_field.metadata['items'])
            else:
                field_type = data_field.type
            
            self.ui.add_argument(
                name=data_field.name,
                default=data_field.default,
                type=field_type,
                help=data_field.metadata.get("help", ""),
                items=data_field.metadata.get("items", []),
            )
        self.ui.setFixedHeight(base_height * len(self.data_fields))
        self.ui.changed.connect(self.on_parameter_changed)

    def get_param_value(self, item_name):
        item = self.ui.find(item_name)
        if not item:
            raise ValueError(f"Item {item_name} not found")

        value = item.read()
        if isinstance(item, qargparse.Enum):
            value = item.text(value)

        return value

    def get_parameters(self) -> Dict[str, Any]:
        params = {}
        for data_field in self.data_fields:
            name = data_field.name
            params[name] = self.get_param_value(name)

        return params

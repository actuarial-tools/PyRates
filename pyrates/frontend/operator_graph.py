from typing import Union, List, Type

from pyrates import PyRatesException
from pyrates.frontend.abc import AbstractBaseTemplate
from pyrates.ir.operator_graph import OperatorGraph
from pyrates.frontend.operator import OperatorTemplate
from pyrates.frontend.parser.yaml import TemplateLoader


class OperatorGraphTemplate(AbstractBaseTemplate):
    target_ir = OperatorGraph

    def __init__(self, name: str, path: str, operators: Union[str, List[str], dict],
                 description: str = "A node or an edge.", label: str = None):
        """For now: only allow single equation in operator template."""

        super().__init__(name, path, description)

        if label:
            self.label = label
        else:
            self.label = self.name

        self.operators = {}  # dictionary with operator path as key and variations to the template as values
        if isinstance(operators, str):
            operator_template = self._load_operator_template(operators)
            self.operators[operator_template] = {}  # single operator path with no variations
        elif isinstance(operators, list):
            for op in operators:
                operator_template = self._load_operator_template(op)
                self.operators[operator_template] = {}  # multiple operator paths with no variations
        elif isinstance(operators, dict):
            for op, variations in operators.items():
                operator_template = self._load_operator_template(op)
                self.operators[operator_template] = variations
        # for op, variations in operators.items():
        #     if "." not in op:
        #         op = f"{path.split('.')[:-1]}.{op}"
        #     self.operators[op] = variations

    def _load_operator_template(self, path: str) -> OperatorTemplate:
        """Load an operator template based on a path"""
        path = self._format_path(path)
        return OperatorTemplate.from_yaml(path)

    def apply(self, values: dict = None):
        """ Apply template to gain a node or edge intermediate representation.

        Parameters
        ----------
        values
            dictionary with operator/variable as keys and values to update these variables as items.

        Returns
        -------

        """

        value_updates = {}
        if values:
            for key, value in values.items():
                op_name, var_name = key.split("/")
                if op_name not in value_updates:
                    value_updates[op_name] = {}
                value_updates[op_name][var_name] = value

        operators = {}

        for template, variations in self.operators.items():
            values_to_update = variations

            if values_to_update is None:
                values_to_update = {}
            if template.name in value_updates:
                values_to_update.update(value_updates.pop(template.name))
            op_instance, op_variables, key = template.apply(return_key=True,
                                                            values=values_to_update)
            operators[key] = {"operator": op_instance,
                              "variables": op_variables}

        # fail gracefully, if any variables remain in `values` which means, that there is some typo
        if value_updates:
            raise PyRatesException(
                "Found value updates that did not fit any operator by name. This may be due to a "
                "typo in specifying the operator or variable to update. Remaining variables:"
                f"{value_updates}")
        return self.target_ir(operators=operators, template=self.path)


class OperatorGraphTemplateLoader(TemplateLoader):

    def __new__(cls, path, template_class):

        return super().__new__(cls, path, template_class)

    @classmethod
    def update_template(cls, template_cls: Type[OperatorGraphTemplate], base, name: str, path: str, label: str,
                        operators: Union[str, List[str], dict] = None,
                        description: str = None):
        """Update all entries of a base edge template to a more specific template."""

        if operators:
            cls.update_operators(base.operators, operators)
        else:
            operators = base.operators

        if not description:
            description = base.__doc__  # or do we want to enforce documenting a template?

        return template_cls(name=name, path=path, label=label, operators=operators,
                            description=description)

    @staticmethod
    def update_operators(base_operators: dict, updates: Union[str, List[str], dict]):
        """Update operators of a given template. Note that currently, only the new information is
        propagated into the operators dictionary. Comparing or replacing operators is not implemented.

        Parameters:
        -----------

        base_operators:
            Reference to one or more operators in the base class.
        updates:
            Reference to one ore more operators in the child class
            - string refers to path or name of single operator
            - list refers to multiple operators of the same class
            - dict contains operator path or name as key
        """
        # updated = base_operators.copy()
        updated = {}
        if isinstance(updates, str):
            updated[updates] = {}  # single operator path with no variations
        elif isinstance(updates, list):
            for path in updates:
                updated[path] = {}  # multiple operator paths with no variations
        elif isinstance(updates, dict):
            for path, variations in updates.items():
                updated[path] = variations
            # dictionary with operator path as key and variations as sub-dictionary
        else:
            raise TypeError("Unable to interpret type of operator updates. Must be a single string,"
                            "list of strings or dictionary.")
        # # Check somewhere, if child operators have same input/output as base operators?
        #
        return updated
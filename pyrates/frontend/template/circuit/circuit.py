
# -*- coding: utf-8 -*-
#
#
# PyRates software framework for flexible implementation of neural 
# network model_templates and simulations. See also:
# https://github.com/pyrates-neuroscience/PyRates
# 
# Copyright (C) 2017-2018 the original authors (Richard Gast and 
# Daniel Rose), the Max-Planck-Institute for Human Cognitive Brain 
# Sciences ("MPI CBS") and contributors
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>
# 
# CITATION:
# 
# Richard Gast and Daniel Rose et. al. in preparation
"""Basic neural mass backend class plus derivations of it.

This module includes the base circuit class that manages the set-up and simulation of population networks. Additionally,
it features various sub-classes that act as circuit constructors and allow to build circuits based on different input
arguments. For more detailed descriptions, see the respective docstrings.

"""

# external packages
from typing import List, Union, Dict
from copy import deepcopy

# pyrates internal imports
from pyrates.frontend.template.abc import AbstractBaseTemplate
from pyrates.frontend.template.edge import EdgeTemplate
from pyrates.frontend.template.node import NodeTemplate
from pyrates import PyRatesException
from pyrates.frontend.yaml import TemplateLoader

# from pyrates.frontend.operator import OperatorTemplate

# meta infos
from pyrates.ir.circuit import CircuitIR
from pyrates.ir.edge import EdgeIR

__author__ = "Richard Gast, Daniel Rose"
__status__ = "Development"


class CircuitTemplate(AbstractBaseTemplate):
    target_ir = CircuitIR

    def __init__(self, name: str, path: str, description: str = "A circuit template.", label: str = "circuit",
                 circuits: dict = None, nodes: dict = None, edges: List[tuple] = None):

        super().__init__(name, path, description)

        self.nodes = {}  # type: Dict[str, NodeTemplate]
        if nodes:
            for key, path in nodes.items():
                if isinstance(path, str):
                    path = self._format_path(path)
                    self.nodes[key] = NodeTemplate.from_yaml(path)

        self.circuits = {}
        if circuits:
            for key, path in circuits.items():
                if isinstance(path, str):
                    path = self._format_path(path)
                    self.circuits[key] = CircuitTemplate.from_yaml(path)

        if edges:
            self.edges = self._get_edge_templates(edges)
        else:
            self.edges = []

        self.label = label

    def apply(self, label: str = None):
        """Create a Circuit graph instance based on the template"""

        if not label:
            label = self.label

        # reformat node templates to NodeIR instances
        nodes = {key: temp.apply() for key, temp in self.nodes.items()}

        # reformat edge templates to EdgeIR instances
        edges = []
        for (source, target, template, values) in self.edges:
            # get edge template and instantiate it
            values = deepcopy(values)
            weight = values.pop("weight", 1.)
            # get delay
            delay = values.pop("delay", None)

            edge_ir = template.apply(values=values)  # type: EdgeIR # edge spec

            edges.append((source, target,  # edge_unique_key,
                          {"edge_ir": edge_ir,
                           "weight": weight,
                           "delay": delay
                           }))

        return CircuitIR(label, self.circuits, nodes, edges, self.path)

    def _get_edge_templates(self, edges: List[Union[tuple, dict]]):
        """
        Reformat edges from [source, target, template_path, variables] to
        [source, target, template_object, variables]

        Parameters
        ----------
        edges

        Returns
        -------
        edges_with_templates
        """
        edges_with_templates = []
        for edge in edges:
            if isinstance(edge, dict):
                edge = (edge["source"], edge["target"], edge["template"], edge["variables"])
            path = edge[2]
            path = self._format_path(path)
            temp = EdgeTemplate.from_yaml(path)
            edges_with_templates.append((*edge[0:2], temp, *edge[3:]))
        return edges_with_templates


class CircuitTemplateLoader(TemplateLoader):

    def __new__(cls, path):

        return super().__new__(cls, path, CircuitTemplate)

    @classmethod
    def update_template(cls, base, name: str, path: str, description: str = None,
                        label: str = None, circuits: dict = None, nodes: dict = None,
                        edges: List[tuple] = None):
        """Update all entries of the circuit template in their respective ways."""

        if not description:
            description = base.__doc__

        if not label:
            label = base.label

        if nodes:
            nodes = cls.update_dict(base.nodes, nodes)
        else:
            nodes = base.nodes

        if circuits:
            circuits = cls.update_dict(base.circuits, circuits)
        else:
            circuits = base.circuits

        if edges:
            edges = cls.update_edges(base.edges, edges)
        else:
            edges = base.edges

        return CircuitTemplate(name=name, path=path, description=description,
                               label=label, circuits=circuits, nodes=nodes,
                               edges=edges)

    @staticmethod
    def update_dict(base_dict: dict, updates: dict):

        updated = deepcopy(base_dict)

        updated.update(updates)

        return updated

    @staticmethod
    def update_edges(base_edges: List[tuple], updates: List[Union[tuple, dict]]):
        """Add edges to list of edges. Removing or altering is currently not supported."""

        updated = deepcopy(base_edges)
        for edge in updates:
            if isinstance(edge, dict):
                if "variables" in edge:
                    edge = [edge["source"], edge["target"], edge["template"], edge["variables"]]
                else:
                    edge = [edge["source"], edge["target"], edge["template"]]
            elif not 3 <= len(edge) <= 4:
                raise PyRatesException("Wrong edge data type or not enough arguments")
            updated.append(edge)

        return updated


def to_circuit(template):
    return template.apply()
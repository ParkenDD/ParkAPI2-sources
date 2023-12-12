"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import ABC, abstractmethod

from lxml.etree import Element

from common.models import ImportSourceResult
from common.xml_helper import XMLHelper
from .base_converter import BaseConverter


class XmlConverter(BaseConverter, ABC):
    xml_helper = XMLHelper()

    @abstractmethod
    def handle_xml(self, root: Element) -> ImportSourceResult:
        pass

"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from collections import defaultdict
from typing import List, Optional, Tuple

from lxml import etree


class XMLHelper:
    """
    Helper for converting data from XML strings to dicts.
    """

    @staticmethod
    def string_to_xml_etree(content_string: str) -> etree.Element:
        """
        Take a string object and (try to) convert it to an XML etree Element
        """
        content_tag: etree.Element = etree.fromstring(content_string, parser=etree.XMLParser(resolve_entities=False))  # noqa: S320

        return content_tag

    @staticmethod
    def xml_to_dict(
        tag: etree.Element,
        ensure_array_keys: Optional[List[Tuple[str, str]]] = None,
        remote_type_tags: Optional[List[str]] = None,
        conditional_remote_type_tags: Optional[List[Tuple[str, str]]] = None,
        ignore_attributes: Optional[List[str]] = None,
    ) -> dict:
        """
        Take XML input and convert it to a dict.

        Without the optional arguments, this:

            <Envelope>
                <Header>
                    <Security>
                        <UsernameToken>
                            <Username>Ghost</Username>
                            <Password>Boo</Password>
                        </UsernameToken>
                    </Security>
                </Header>
                <Body>
                    <Content>
                        <ContentText>
                            <Text>some text</Text>
                        </ContentText>
                    </Content>
                </Body>
            </Envelope>

        ... will beconverted to this:

        {
            'Envelope': {
                'Body': {
                    'Content': {
                        'ContentText': {
                            'Text': 'some text',
                        }
                    }
                },
                'Header': {
                    'Security': {
                        'UsernameToken': {
                            'Password': 'Boo',
                            'Username': 'Ghost',
                        }
                    }
                }
            }
        }

        The 'ensure_array_keys' list can be provided to specify for which keys in which tags, the values
        should always be interpreted as items of a list. In case there is only one child item, they would otherwise
        not be recognizable as a list in the XML.

        With ensure_array_keys=[('Envelope', 'Header'), ('Content', 'ContentText')],
        the example above would be converted to this,
        interpreting the values of the given keys as lists:

        {
            'Envelope': {
                'Body': {
                    'Content': {
                        'ContentText': [
                            {'Text': 'some text'},
                        ]
                    }
                },
                'Header': [
                    {
                        'Security': {
                            'UsernameToken': {
                                'Password': 'Boo',
                                'Username': 'Ghost'
                            }
                        }
                    },
                ]
            }
        }

        The 'remote_type_tags' list can be provided to specify which tags should be interpreted as names of types,
        e.g. enums, which don't need to be preserved as keys in the output dict.

        For example, this:

            <status>
                <ChargePointStatusType>Operative</ChargePointStatusType>
            </status>

        would usually be converted to this:

        {
            'status': {
                'ChargePointStatusType': 'Operative',
            }
        }

        But if 'ChargePointStatusType' is given in the 'remote_type_tags' list,
        it will be converted to this simpler version:

        {
            'status': 'Operative'
        }

        Which could then be parsed into an enum value if necessary.

        Another use case for 'remote_type_tags' would be to skip a level in the nested data
        that has only one field (!) of which the name does also not need to be preserved as a key.

        With remote_type_tags=['Envelope', 'Content', 'ContentText', 'Text', 'Security', 'UsernameToken'],
        the first example above can become as compact as this:

            {
                'Body': 'some text',
                'Header': {
                    'Password': 'Boo',
                    'Username': 'Ghost',
                }
            }

        The 'Body', 'Header', 'Username' and 'Password' keys can not be removed
        because there are multiple keys on their levels.

        The 'conditional_remote_type_tags' list can be used to skip a tag depending on the name of its parent tag.
        This is most useful for tags where the field name and the type name are the same,
        but only one of them should be skipped, for example:

        <resultCode>
            <resultCode>ok</resultCode>
        </resultCode>

        can be parsed into a non-nested field named 'resultCode' with the content 'ok'
        by giving conditional_remote_type_tags=[('resultCode', 'resultCode')].

        The 'ignore_attributes' list can be given to avoid parsing attributes with a certain name.
        This is useful if a tag could either have a simple string value as a child, or be self-closing -
        and the self-closing version should be interpreted as if the tag's value is null
        (because there might be attributes that say this, but in a weirdly complicated way).

        For example, a tag like this is 'null' in terms of practical use:

        <resultDescription xsi:nil="true" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>

        But it would normally be parsed as a dictionary here:

        'resultDescription': {'{http://www.w3.org/2001/XMLSchema-instance}nil': 'true'}

        And if we were to just skip the attribute by adding it to 'remote_type_tags', we would get this instead:

        'resultDescription': 'true'

        Which would be very misleading. So to parse this tag into a useful value for an 'Optional[str]' type field,
        the ignore_attributes list can be used.
        With ignore_attributes=['{http://www.w3.org/2001/XMLSchema-instance}nil'], we get a result that fits the type:

        'resultDescription': None

        """
        # default empty lists for the optional arguments:
        if ensure_array_keys is None:
            ensure_array_keys = []
        if remote_type_tags is None:
            remote_type_tags = []
        if conditional_remote_type_tags is None:
            conditional_remote_type_tags = []
        if ignore_attributes is None:
            ignore_attributes = []

        tag_name = etree.QName(tag).localname

        # only parse attributes if there are any of them not in the ignore list
        ignore_all_attribs: bool = False
        if tag.attrib:
            ignore_all_attribs = True
            for key in tag.attrib.keys():
                if key not in ignore_attributes:
                    ignore_all_attribs = False

        tag_dict = {tag_name: {} if (tag.attrib and not ignore_all_attribs) else None}
        children = list(tag)
        if children:
            aggregated_child_dict = defaultdict(list)
            for child in children:
                child_dict = XMLHelper.xml_to_dict(
                    child,
                    ensure_array_keys,
                    remote_type_tags,
                    conditional_remote_type_tags,
                    ignore_attributes,
                )
                for key, value in child_dict.items():
                    aggregated_child_dict[key].append(value)
            tag_dict = {tag_name: {}}
            for key, value in aggregated_child_dict.items():
                if key == 'class':
                    key = 'class_'
                if len(value) == 1 and (tag_name, key) not in ensure_array_keys:
                    value = value[0]
                tag_dict[tag_name][key] = value

        if tag.attrib and not ignore_all_attribs:
            for key, value in tag.attrib.items():
                if key not in ignore_attributes:
                    tag_dict[tag_name][key.replace('{http://www.w3.org/2001/XMLSchema-instance}', '')] = value

        if tag.text:
            text = tag.text.strip()
            if children or (tag.attrib and not ignore_all_attribs):
                if text:
                    tag_dict[tag_name]['_text'] = text
            else:
                tag_dict[tag_name] = text

        # filter out remote type tags at the child level:
        if isinstance(tag_dict[tag_name], dict):
            tag_items: list[tuple[str, str]] = [(key, value) for key, value in tag_dict[tag_name].items()]  # noqa: C416
            # it only works if there is exactly one key-value-pair at the child level!
            if len(tag_items) == 1:
                child_key = tag_items[0][0]
                child_value = tag_items[0][1]
                # filter second level:
                if child_key in remote_type_tags or (tag_name, child_key) in conditional_remote_type_tags:
                    tag_dict[tag_name] = child_value

        # finally, filter out remote type tags at the top level:
        if isinstance(tag_dict[tag_name], dict) and tag_name in remote_type_tags:
            # the return value still has to be a dict!
            tag_dict = tag_dict[tag_name]

        return tag_dict

    @staticmethod
    def xml_string_to_dict(
        xml_string: str,
        ensure_array_keys: Optional[List[Tuple[str, str]]] = None,
        remote_type_tags: Optional[List[str]] = None,
        conditional_remote_type_tags: Optional[List[Tuple[str, str]]] = None,
        ignore_attributes: Optional[List[str]] = None,
    ) -> dict:
        """
        Wrapper around 'string_to_xml_etree' and 'xml_to_dict'
        """
        result_tag: etree.Element = XMLHelper.string_to_xml_etree(xml_string)
        result_dict: dict = XMLHelper.xml_to_dict(
            result_tag,
            ensure_array_keys,
            remote_type_tags,
            conditional_remote_type_tags,
            ignore_attributes,
        )
        return result_dict

"""HiddenTanks operation: unhide tanks in a nation list.xml."""
import xml.etree.ElementTree as ET

from ..headers import xml_stamp
from .constants import TAGS_TO_REMOVE

_XML_STAMP_MARK = "HuntezPatch - Generated:"


def _split_xml_stamp(xml_content):
    """Split a leading generator comment. Returns (stamp_or_None, rest)."""
    if xml_content.startswith("<!--") :
        head, sep, rest = xml_content.partition("-->")
        if sep and _XML_STAMP_MARK in head:
            return head + sep, rest.lstrip("\n")
    return None, xml_content


def process_xml(xml_content):
    """Unhide tanks in a nation list.xml. Returns (new_xml, tank_data)."""
    stamp, xml_content = _split_xml_stamp(xml_content)
    if stamp is None:
        stamp = xml_stamp()
    root = ET.fromstring(xml_content)
    tank_data = {}
    for vehicle in root:
        name = vehicle.tag
        id_elem = vehicle.find('id')
        uid = id_elem.text if id_elem is not None else name

        price_elem = vehicle.find('price')
        price_has_gold = False
        if price_elem is not None:
            if price_elem.text and 'gold' in price_elem.text:
                price_has_gold = True
            elif price_elem.find('gold') is not None:
                price_has_gold = True

        not_in_shop_elem = vehicle.find('notInShop')
        not_in_shop = (
            not_in_shop_elem is not None
            and not_in_shop_elem.text is not None
            and not_in_shop_elem.text.lower() == 'true'
        )

        tags_elem = vehicle.find('tags')
        tags_str = tags_elem.text.strip() if tags_elem is not None and tags_elem.text else ""
        tags_set = set(tags_str.split())

        class_type = 'unknown'
        for ct in ('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG'):
            if ct in tags_set:
                class_type = ct
                break

        level_elem = vehicle.find('level')
        try:
            level = int(level_elem.text) if level_elem is not None else 1
        except (TypeError, ValueError):
            level = 1

        tank_data[name] = {
            'uid': uid,
            'tags_orig': tags_str,
            'price_gold': price_has_gold,
            'not_in_shop_orig': not_in_shop,
            'level': level,
            'class_type': class_type,
        }

        if not_in_shop_elem is not None:
            not_in_shop_elem.text = 'false'
        if tags_elem is not None:
            tags_elem.text = ' '.join(sorted(t for t in tags_set if t not in TAGS_TO_REMOVE))

    new_xml = ET.tostring(root, encoding='unicode')
    new_xml = new_xml.replace(' />', '/>')
    return stamp + "\n" + new_xml, tank_data

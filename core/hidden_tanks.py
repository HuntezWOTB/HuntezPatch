"""HiddenTanks processors: XML list + TechTree YAML (ported, cleaned)."""
import re
import xml.etree.ElementTree as ET
from copy import deepcopy  # noqa: F401  (kept for future transforms)

import yaml
from collections import OrderedDict  # noqa: F401

CLASS_ORDER = {'lightTank': 0, 'mediumTank': 1, 'heavyTank': 2, 'AT-SPG': 3}
TAGS_TO_REMOVE = {'deprecated', 'secret', 'testTank', 'lightTankArtefacts_User', 'grousers_user', 'event_battles'}

# nation_code -> (display, tree_rel, list_rel); rel paths are relative to Data/ (game) or packs/ (DLC)
NATIONS = {
    'CN': ('china', 'Configs/TechTree/china_tree.yaml', 'XML/item_defs/vehicles/china/list.xml'),
    'EU': ('european', 'Configs/TechTree/european_tree.yaml', 'XML/item_defs/vehicles/european/list.xml'),
    'FR': ('france', 'Configs/TechTree/france_tree.yaml', 'XML/item_defs/vehicles/france/list.xml'),
    'DE': ('germany', 'Configs/TechTree/germany_tree.yaml', 'XML/item_defs/vehicles/germany/list.xml'),
    'JP': ('japan', 'Configs/TechTree/japan_tree.yaml', 'XML/item_defs/vehicles/japan/list.xml'),
    'HN': ('other', 'Configs/TechTree/other_tree.yaml', 'XML/item_defs/vehicles/other/list.xml'),
    'UK': ('uk', 'Configs/TechTree/uk_tree.yaml', 'XML/item_defs/vehicles/uk/list.xml'),
    'US': ('usa', 'Configs/TechTree/usa_tree.yaml', 'XML/item_defs/vehicles/usa/list.xml'),
    'SU': ('ussr', 'Configs/TechTree/ussr_tree.yaml', 'XML/item_defs/vehicles/ussr/list.xml'),
}


def process_xml(xml_content):
    """Unhide tanks in a nation list.xml. Returns (new_xml, tank_data)."""
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
            tags_elem.text = ' '.join(t for t in tags_set if t not in TAGS_TO_REMOVE)

    new_xml = ET.tostring(root, encoding='unicode')
    new_xml = new_xml.replace(' />', '/>')
    return new_xml, tank_data


def parse_tree_yaml(text):
    commented = set()
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('#'):
            content = stripped[1:].strip()
            match = re.match(r'^([\w\-\.]+)\s*:', content)
            if match:
                commented.add(match.group(1))
    try:
        data = yaml.safe_load(text)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    premium_rows = data.get('premium_rows', 1)
    tanks_dict = data.get('tanks', {}) or {}
    existing = set(tanks_dict.keys())
    return premium_rows, existing, commented


def classify_tank(tank_name, tank_info):
    """Hidden-tank category (sort order: ordinary -> collectible -> premium).

    - ordinary (standard):   price NOT in gold and NO 'collectible' tag.
    - collectible:           'collectible' tag AND price in gold.
    - premium:               price in gold and NO 'collectible' tag.
    """
    tags = set((tank_info.get('tags_orig') or '').split())
    price_gold = bool(tank_info.get('price_gold'))
    if 'collectible' in tags and price_gold:
        return 'collectible'
    if price_gold:
        return 'premium'
    return 'ordinary'
    return 'premium'


def generate_tree_yaml(original_text, xml_tanks_data, nation_code=None):
    premium_rows, existing, commented = parse_tree_yaml(original_text)

    try:
        orig_data = yaml.safe_load(original_text) or {}
        orig_tanks = orig_data.get('tanks', {}) or {}
    except Exception:
        orig_tanks = {}

    if nation_code == 'HN':
        corrected = {}
        for name, params in orig_tanks.items():
            if isinstance(params, dict) and 'position' in params and name in xml_tanks_data:
                pos = params['position']
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    params = dict(params)
                    params['position'] = [xml_tanks_data[name]['level'], pos[1]]
            corrected[name] = params
        orig_tanks = corrected

    visible_by_level = {}
    max_row_global = 0
    for name, params in orig_tanks.items():
        if isinstance(params, dict) and 'position' in params:
            pos = params['position']
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                lvl, row = pos[0], pos[1]
                visible_by_level.setdefault(lvl, []).append((row, name))
                if isinstance(row, int) and row > max_row_global:
                    max_row_global = row

    all_hidden = set(commented)
    for name in xml_tanks_data:
        if name not in existing:
            all_hidden.add(name)

    level_data = {}
    for name in all_hidden:
        if name not in xml_tanks_data:
            continue
        info = xml_tanks_data[name]
        lvl = info['level']
        cat = classify_tank(name, info)
        level_data.setdefault(lvl, {'ordinary': [], 'collectible': [], 'premium': []})
        level_data[lvl][cat].append((name, info['class_type']))

    for lvl in level_data:
        for cat in level_data[lvl]:
            level_data[lvl][cat].sort(key=lambda x: (CLASS_ORDER.get(x[1], 99), x[0]))
    for lvl in visible_by_level:
        visible_by_level[lvl].sort(key=lambda x: x[0])

    output = [
        "# HiddenTanks-Generator",
        "# v 1.0.0",
        "# Generated code",
        f"premium_rows: {premium_rows}",
        "",
        "tanks:",
    ]
    for lvl in sorted(set(list(visible_by_level.keys()) + list(level_data.keys()))):
        if lvl in visible_by_level:
            output.append(f"# Visible - {lvl} level - HiddenTanks-Generator")
            for row, name in visible_by_level[lvl]:
                output.append(f"    {name}:")
                output.append(f"        position: [{lvl}, {row}]")
        if lvl in level_data:
            current_row = max_row_global + 1
            for cat in ('ordinary', 'collectible', 'premium'):
                if not level_data[lvl][cat]:
                    continue
                output.append(f"# Hidden - {lvl} level - HiddenTanks-Generator")
                for name, _ in level_data[lvl][cat]:
                    output.append(f"    {name}:")
                    output.append(f"        position: [{lvl}, {current_row}]")
                    current_row += 1
    return "\n".join(output) + "\n"


def get_nation_stat(tank_data, tree_yaml_text):
    visible = set()
    try:
        data = yaml.safe_load(tree_yaml_text) or {}
        if isinstance(data, dict) and 'tanks' in data and isinstance(data['tanks'], dict):
            visible = set(data['tanks'].keys())
    except Exception:
        pass
    hidden = {'ordinary': 0, 'collectible': 0, 'premium': 0}
    for name, info in tank_data.items():
        if name not in visible:
            hidden[classify_tank(name, info)] += 1
    return {
        'visible': len(visible),
        'hidden_ordinary': hidden['ordinary'],
        'hidden_collectible': hidden['collectible'],
        'hidden_premium': hidden['premium'],
    }

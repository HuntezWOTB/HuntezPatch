"""HiddenTanks constants: class order, tag cleanup, nation table."""
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

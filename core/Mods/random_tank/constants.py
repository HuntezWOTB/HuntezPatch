"""RandomTankSelector constants: target files, icon paths, headers, blocks."""
import re

RANDOMTANK_FILES = [
    "UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.yaml",
    "UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.actions",
]

YAML_REL = RANDOMTANK_FILES[0]
ACTIONS_REL = RANDOMTANK_FILES[1]

ICON_BASE_REL = "Gfx/Lobby/icons/randomtankselector_button_icon.packed.webp"
ICON_2X_REL = "Gfx/Lobby/icons/randomtankselector_button_icon@2x.packed.webp"
ICON_RELS = (ICON_BASE_REL, ICON_2X_REL)
ICON_SIZE = 32
ICON_2X_SIZE = 64
ICON_RES_PATH = "~res:/Gfx/Lobby/icons/randomtankselector_button_icon"

YAML_BUTTON_BLOCK = (
    '    -   class: "UIControl"\n'
    '        name: "RandomTankButtonHolder"\n'
    '        input: false\n'
    '        components:\n'
    '            Anchor:\n'
    '                rightAnchorEnabled: true\n'
    '                rightAnchor: 8.000000\n'
    '                topAnchorEnabled: true\n'
    '                topAnchor: -64.000000\n'
    '            IgnoreLayout: {}\n'
    '            SizePolicy:\n'
    '                horizontalPolicy: "PercentOfMaxChild"\n'
    '                verticalPolicy: "PercentOfMaxChild"\n'
    '            UIChildComponent0:\n'
    '                prototypePath: "~res:/UI/Screens3/Lobby/Common/IconButton.yaml"\n'
    '                args:\n'
    '                    "type": "eButtonType.OPTIONAL_DARK"\n'
    '                    "sound": "eButtonSound.CHOOSE"\n'
    '                    "buttonSize": "56"\n'
    '                    "imageSize": "32"\n'
    f'                    "image": "\\"{ICON_RES_PATH}\\""\n'
    '                    "enabled": "tanks.Size() > 1"\n'
    '                eventActions:\n'
    '                - ["ON_CLICK_BUTTON", "SELECT_RANDOM_TANK", ""]\n'
    '        bindings:\n'
    '        - ["visible", "not isNull(account) and not account.tutorialData.isTutorialActive"]\n'
)

ACTION_BLOCK = (
    'action SELECT_RANDOM_TANK\n'
    '{\n'
    '  PlaySound(sound="GUI/buttons/choose");\n'
    '  ChangeData(currentIndex, rand(Size(tanks)));\n'
    '\n'
    '  if((format("TankCell:%(tNation):%(tName)",'
    ' { "tNation" = str(tanks[currentIndex].info.nation, eNation, "autotests");'
    ' "tName" = tanks[currentIndex].info.technicalName; })) == selectedCellName)\n'
    '  {\n'
    '    Event("SELECT_RANDOM_TANK");\n'
    '  }\n'
    '  else\n'
    '  {\n'
    '    ScrollToEnsureControlOnScreen("**/PlayerTanks/"'
    ' + (format("TankCell:%(tNation):%(tName)",'
    ' { "tNation" = str(tanks[currentIndex].info.nation, eNation, "autotests");'
    ' "tName" = tanks[currentIndex].info.technicalName; })),'
    ' xPolicy=eScrollToControlPolicy.kNearest);\n'
    '    Wait(0.05); // ensure tank is loaded\n'
    '    DirectEvent("ON_TANK_PRESS", "**/PlayerTanks/"'
    ' + (format("TankCell:%(tNation):%(tName)",'
    ' { "tNation" = str(tanks[currentIndex].info.nation, eNation, "autotests");'
    ' "tName" = tanks[currentIndex].info.technicalName; })));\n'
    '  }\n'
    '}\n'
)

_RE_YAML_CLASS = re.compile(r'^\s*-\s*class:\s*"UIControl"\s*$')
_RE_YAML_FILTER_NAME = re.compile(r'^\s*name:\s*"Filter"\s*$')
_RE_ACTION_NEXT = re.compile(r'^\s*action\s+SELECT_NEXT_TANK\b')
_RE_ACTION_SELF = re.compile(r'^\s*action\s+SELECT_RANDOM_TANK\b')

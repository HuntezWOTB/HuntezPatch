"""ServersClusterSelector constants: login-screen server/cluster picker."""

# Actively managed files (functional changes). Row/login templates use the
# row index (childregions mapping) built by prime_row_index, so file order
# inside one pass does not matter.
SERVER_SELECT_FILES = [
    "UI/Screens3/PreLogin/ServerSelection.yaml",
    "regions_publish.yaml",
    "UI/Screens3/PreLogin/ServerDescriptionPrototype.yaml",
    "UI/Screens3/PreLogin/Entry.yaml",
    "UI/Screens3/PreLogin/NewGame.yaml",
]

# One-time migration: dev-button leftovers from older mod versions are
# reverted to stock here (never touched again afterwards).
LEGACY_REVERT_FILES = [
    "UI/Screens3/PreLogin/HelperButtons.yaml",
    "UI/Screens3/PreLogin/PreLogin.yaml",
    "UI/Screens3/PreLogin/PreLogin.actions",
]

# Shown as file meta in the GUI tile.
SERVER_SELECT_META_FILES = 6

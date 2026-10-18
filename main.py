import sys

# No __pycache__ garbage in the project folder on any launch path.
sys.dont_write_bytecode = True

from gui.app import main

if __name__ == "__main__":
    sys.exit(main())

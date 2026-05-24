import sys
import os

# This file fixes the "No module named 'app'" error on Windows.
# It tells Python to look in the project root folder when importing.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

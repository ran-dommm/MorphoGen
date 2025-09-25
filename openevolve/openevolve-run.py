#!/usr/bin/env python
"""
Entry point script for OpenEvolve
"""
import sys
from openevolve.cli import main
import os

# Set the proxy environment variables (use HTTP proxy on port 7890)
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

if __name__ == "__main__":
    sys.exit(main())

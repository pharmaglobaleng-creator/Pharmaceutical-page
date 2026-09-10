#!/usr/bin/env python3
"""Compatibility entry point: the approved phone CTA now lives in the header.
Existing workflows retain this filename; never reintroduce a floating badge.
"""
from apply_sitewide_header import main

if __name__ == "__main__":
    main()

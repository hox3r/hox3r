#!/usr/bin/env python3
"""Build monochrome animated ASCII portrait banners for the HOX3R profile."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'assets/source/portrait.png'
DEFAULT_DATA = ROOT / 'data/profile.json'
OUT = ROOT / 'assets/hero'

def load_profile(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('username','display_name','role','focus','about','focus_areas','projects'):
        if key not in data: raise ValueError(f'missing profile field: {key}')
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,default=DEFAULT_DATA); args=ap.parse_args()
    profile=load_profile(args.data)
    print(f"Loaded profile for {profile['username']}.")
if __name__=='__main__': main()

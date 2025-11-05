from dataclasses import fields
import sys
from pathlib import Path

# Ensure project root is on sys.path for 'file.*' imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from file.globalProperties import GlobalNote, GlobalBasegrid, GlobalMeasureNumbering
from file.SCORE import SCORE


def print_alias_info(dc_cls, title):
    print(f'\n=== {title} ===')
    for f in fields(dc_cls):
        alias = SCORE._json_field_name(f)
        meta = getattr(f, 'metadata', {}) or {}
        cfg = meta.get('dataclasses_json', None)
        cfg_type = type(cfg).__name__
        ends_q = isinstance(alias, str) and alias.endswith('?')
        print(f'{f.name:28s} -> alias: {alias!r:25s} endswith?: {ends_q}  (cfg type: {cfg_type})')
        if cfg_type == 'dict':
            try:
                mm = cfg.get('mm_field', None)
                print('   cfg keys:', list(cfg.keys()))
                print('   cfg.field_name:', cfg.get('field_name', None))
                print('   mm_field: ', type(mm).__name__, repr(mm))
                try:
                    dk = getattr(mm, 'data_key', None)
                    print('   mm_field.data_key:', dk)
                except Exception as e:
                    print('   mm_field.data_key error:', e)
            except Exception as e:
                print('   cfg inspect error:', e)


if __name__ == '__main__':
    print_alias_info(GlobalNote, 'GlobalNote')
    print_alias_info(GlobalBasegrid, 'GlobalBasegrid')
    print_alias_info(GlobalMeasureNumbering, 'GlobalMeasureNumbering')

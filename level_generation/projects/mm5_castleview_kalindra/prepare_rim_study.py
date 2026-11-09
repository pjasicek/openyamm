"""Plan an isolated cliff/space-boundary experiment from the exact current terrain mask."""
import argparse
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
OUTPUT = PROJECT/'review/rim_geometry_study_v5'


def prepare():
    from world_rim import plan_rim
    report = plan_rim(PROJECT)
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/'plan.json').write_text(json.dumps(report, indent=2)+'\n')
    print({'edges': len(report['edges']), 'nodes': len(report['nodes']),
           'fluidEdges': report['fluidEdgeCount']})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-version', default='rim_geometry_study_v5')
    OUTPUT = PROJECT/'review'/parser.parse_args().review_version
    prepare()

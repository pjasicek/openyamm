"""Reset persistent MM5 playtest settings from the repository's settings.ini."""
import configparser
from pathlib import Path


def configure():
    project = Path(__file__).resolve().parent
    installation = project/'local_playtest'
    destination = installation/'playtest/settings.ini'
    if not destination.is_file():
        raise SystemExit('Create the local installation with play.sh first.')

    settings = configparser.ConfigParser(interpolation=None)
    with (project.parents[2]/'settings.ini').open() as source:
        settings.read_file(source)
    overrides = {
        'assets': {'root': str(installation/'assets_dev')},
        'startup': {'start_in_main_menu': 'true', 'save_file': ''},
        'debug': {'start_world': 'mm5', 'start_map_file': 'mm5_sw.odm'},
    }
    for section, values in overrides.items():
        if not settings.has_section(section):
            settings.add_section(section)
        settings[section].update(values)
    with destination.open('w') as output:
        settings.write(output, space_around_delimiters=False)
    print('MM5 playtest settings copied from repository:', destination)


if __name__ == '__main__':
    configure()

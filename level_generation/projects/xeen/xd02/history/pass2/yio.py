"""YAML 1.2-ish load/dump for project files: only true/false are booleans (PyYAML would read the key `on` as True)."""
import re, yaml
class Loader(yaml.SafeLoader):
    pass
Loader.yaml_implicit_resolvers = {k: [r for r in v if r[0] != 'tag:yaml.org,2002:bool'] for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Loader.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:true|false)$'), list('tf'))
class Dumper(yaml.SafeDumper):
    pass
Dumper.yaml_implicit_resolvers = {k: [r for r in v if r[0] != 'tag:yaml.org,2002:bool'] for k, v in yaml.SafeDumper.yaml_implicit_resolvers.items()}
Dumper.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:true|false)$'), list('tf'))
def load(path):
    return yaml.load(open(path), Loader=Loader)
def save(path, data):
    yaml.dump(data, open(path, 'w'), Dumper=Dumper, sort_keys=False, allow_unicode=True, width=4096)

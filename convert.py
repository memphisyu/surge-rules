"""Convert a checked-out upstream snapshot; never read personal proxy profiles."""
import argparse
import hashlib
import ipaddress
import json
import re
import shutil
from pathlib import Path

import yaml

SUPPORTED = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'IP-CIDR',
             'IP-CIDR6', 'IP-ASN', 'PROCESS-NAME', 'DOMAIN-REGEX'}


def convert_rule(rule):
    if not isinstance(rule, str) or '\n' in rule or '\r' in rule:
        raise ValueError('Rule must be a single string')
    kind, value = rule.split(',', 1)
    if kind == 'DOMAIN-REGEX':
        if not value:
            raise ValueError('Empty regex')
        return kind, value
    value, *options = value.split(',')
    if kind not in SUPPORTED or not value or any(x != 'no-resolve' for x in options):
        raise ValueError(f'Unsupported rule: {rule}')
    if kind in ('IP-CIDR', 'IP-CIDR6'):
        net = ipaddress.ip_network(value, strict=False)
        if net.version != (6 if kind == 'IP-CIDR6' else 4):
            raise ValueError(f'Wrong address family: {rule}')
    elif kind == 'IP-ASN':
        if not value.isdecimal() or not 0 < int(value) <= 4294967295:
            raise ValueError(f'Invalid ASN: {rule}')
    elif options:
        raise ValueError(f'Unexpected rule options: {rule}')
    if kind in ('DOMAIN', 'DOMAIN-SUFFIX') and not re.fullmatch(r'(?:[A-Za-z0-9_](?:[A-Za-z0-9_-]*[A-Za-z0-9_])?\.)*[A-Za-z0-9_](?:[A-Za-z0-9_-]*[A-Za-z0-9_])?', value):
        raise ValueError(f'Invalid domain: {rule}')
    return kind, f'{kind},{value}' + (',no-resolve' if kind in ('IP-CIDR', 'IP-CIDR6', 'IP-ASN') else '')


def build(upstream, output, base_url, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Upstream revision must be a full commit SHA')
    if not re.fullmatch(r'https://raw\.githubusercontent\.com/[\w.-]+/[\w.-]+/main/Surge', base_url):
        raise ValueError('Expected a public GitHub raw URL ending in /main/Surge')
    # Read every rule before writing any generated files; malformed input stops publication.
    sets = {}
    for file in sorted((upstream / 'ruleset').glob('*/*.yaml')):
        brand = file.parent.name
        if file.stem != brand or not re.fullmatch(r'[\w-]+', brand, flags=re.ASCII):
            raise ValueError(f'Invalid ruleset path: {file}')
        doc = yaml.safe_load(file.read_text())
        if not isinstance(doc, dict) or set(doc) != {'payload'} or not isinstance(doc['payload'], list) or not doc['payload']:
            raise ValueError(f'Invalid payload: {file}')
        sets[brand] = [convert_rule(rule) for rule in doc['payload']]
    if not sets:
        raise ValueError('No upstream rulesets')

    template = (upstream / 'configs/Nikki/config.yaml').read_text().split('\nrules:', 1)[1]
    order = re.findall(r'^\s*(?:#\s*)?-\s*RULE-SET,([^,\s]+),([^\n]+)$', template, re.M)
    order = [(brand, policy.strip()) for brand, policy in order if brand != 'Applications']
    if len({b for b, _ in order}) != len(order) or {b for b, _ in order} != set(sets) - {'Applications'}:
        raise ValueError('Upstream routing template and ruleset inventory differ')

    files = {}
    manifest = {'upstream': 'Hawaiine/mihomo-rules', 'commit': revision, 'rulesets': {}}
    scripts = []
    for brand, rules in sets.items():
        patterns = [value for kind, value in rules if kind == 'DOMAIN-REGEX']
        name = 'HawaiineRegex-' + brand
        lines, inserted = [], False
        for kind, value in rules:
            if kind == 'DOMAIN-REGEX':
                if not inserted:
                    lines.append('SCRIPT,' + name)
                    inserted = True
            else:
                lines.append(value)
        files[brand + '.list'] = '\n'.join(lines) + '\n'
        if patterns:
            files[brand + '.js'] = ('const patterns = ' + json.dumps(patterns) + ';\n'
                'const hostname = $request.hostname;\n'
                '$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});\n')
            scripts.append(f'{name} = type=rule,script-path={base_url}/{brand}.js,script-update-interval=86400')
        manifest['rulesets'][brand] = {'source_rules': len(rules), 'regex_rules': len(patterns),
            'sha256': hashlib.sha256(files[brand + '.list'].encode()).hexdigest()}

    routes = [f'RULE-SET,{base_url}/{brand}.list,{policy},update-interval=86400' for brand, policy in order]
    files['rules.conf'] = '# Rule and script sections only; policies must exist in the main profile.\n[Rule]\n' + '\n'.join(routes) + '\n\n[Script]\n' + '\n'.join(scripts) + '\n'
    files['LICENSE'] = (upstream / 'LICENSE').read_text()
    files['NOTICE'] = 'Rules derived from https://github.com/Hawaiine/mihomo-rules at ' + revision + '\nSee LICENSE for the upstream license.\n'
    files['manifest.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    files['order.json'] = json.dumps(order, ensure_ascii=False, indent=2) + '\n'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name, data in files.items():
        (output / name).write_text(data)
    print(f'{len(sets)} rulesets, {sum(len(r) for r in sets.values())} source rules, {len(scripts)} regex scripts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('Surge'))
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if args.output.resolve() in (Path.cwd().resolve(), args.upstream.resolve()) or args.upstream.resolve().is_relative_to(args.output.resolve()):
        parser.error('Output must not contain the project or upstream source')
    build(args.upstream, args.output, args.base_url, args.revision)

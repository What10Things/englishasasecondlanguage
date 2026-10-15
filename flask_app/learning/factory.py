"""Read immutable, privately deployed teacher products without changing sold packs."""
import hashlib
import json
import re
from pathlib import Path
from flask import current_app
from .catalog import LANGUAGES, LEVELS

POLICY='efl-auto-release-v1'
ID=re.compile(r'teacher-[a-f0-9]{32}-[a-f0-9]{16}')


def directory():
    return Path(current_app.config['FACTORY_PRODUCTS_DIR'])


def validate(p):
    if not isinstance(p,dict) or not ID.fullmatch(p.get('id','')):raise ValueError('product_identity')
    if p.get('source')!='factory' or p.get('quality_policy')!=POLICY:raise ValueError('quality_policy')
    if p.get('filename')!=p['id']+'.zip':raise ValueError('filename')
    for name in ('sha256','bundle_hash','content_hash'):
        if not isinstance(p.get(name),str) or not re.fullmatch('[a-f0-9]{64}',p[name]):raise ValueError('hash')
    if p.get('level') not in LEVELS or p.get('currency')!='gbp' or type(p.get('price_pence')) is not int or p['price_pence']!=399:raise ValueError('commercial_contract')
    langs=p.get('languages')
    if not isinstance(langs,list) or not langs or len(set(langs))!=len(langs) or 'en' not in langs or any(x not in LANGUAGES for x in langs):raise ValueError('languages')
    if not isinstance(p.get('titles'),dict) or set(p['titles'])!=set(langs):raise ValueError('titles')
    if not isinstance(p.get('title'),str) or not p['title'].strip() or any(not isinstance(t,str) or not t.strip() for t in p['titles'].values()):raise ValueError('title')
    if not isinstance(p.get('version'),str) or not re.fullmatch('[a-f0-9]{12}',p['version']):raise ValueError('version')
    if type(p.get('question_count')) is not int or not 12<=p['question_count']<=40:raise ValueError('count')
    if type(p.get('duration_minutes')) is not int or not 30<=p['duration_minutes']<=120:raise ValueError('duration')
    if not isinstance(p.get('objectives'),list) or not 2<=len(p['objectives'])<=5 or any(not isinstance(x,str) for x in p['objectives']):raise ValueError('objectives')
    if not isinstance(p.get('samples'),list) or len(p['samples'])!=2:raise ValueError('samples')
    for sample in p['samples']:
        if not isinstance(sample,dict) or set(sample)!={'id','instruction','stimulus','prompt','options'}:raise ValueError('sample')
        if any(not isinstance(sample[k],str) for k in ('id','instruction','stimulus','prompt')):raise ValueError('sample_text')
        if not isinstance(sample['options'],list) or any(not isinstance(x,str) for x in sample['options']):raise ValueError('options')
    return p


def products():
    result=[]
    for file in sorted(directory().glob('teacher-*.json')):
        try:
            if file.is_symlink() or file.stat().st_size>100_000:continue
            p=validate(json.loads(file.read_text()))
            if file.name!=p['id']+'.json':continue
            archive=directory()/p['filename']
            if archive.is_symlink() or not archive.is_file():continue
            result.append(p)
        except (OSError,ValueError,KeyError,TypeError):
            current_app.logger.warning('Invalid factory product withheld')
    return result


def product_file(p):
    validate(p)
    path=directory()/p['filename']
    if path.is_symlink() or not path.resolve().is_relative_to(directory().resolve()):raise ValueError('download_path')
    if not path.is_file() or path.stat().st_size>10_000_000 or hashlib.sha256(path.read_bytes()).hexdigest()!=p['sha256']:
        raise ValueError('download_integrity')
    return path

#!/usr/bin/env python
import io
import requests
import json
import cfnlint
import pypandoc
import datetime
from pytablewriter import MarkdownTableWriter
from pathlib import Path

r = requests.get('https://raw.githubusercontent.com/avattathil/doc_demo/master/templates/aws-vpc.template.json')

template = cfnlint.decode.cfn_yaml.loads(r.content)
p_file = Path('docs/include/params.adoc')

label_mappings = {}
reverse_label_mappings = {}
parameter_mappings = {}
parameter_labels = {}
no_groups = {}

def determine_optional_value(param):
    optional = template['Metadata'].get('OptionalParams')
    if optional and (param in optional):
        return '__Optional__'
    return '**__Requires Input__**'

for label in template['Metadata']['AWS::CloudFormation::Interface']['ParameterGroups']:
    label_name = label['Label']['default']
    label_params = label['Parameters']
    label_mappings[label_name] = label_params
    for ln in label_params:
        reverse_label_mappings[ln] = label_name

for label_name, label_data in template['Metadata']['AWS::CloudFormation::Interface']['ParameterLabels'].items():
    parameter_labels[label_name] = label_data.get('default')

for label_name, label_data in template['Parameters'].items():
    parameter_mappings[label_name] = label_data
    if not reverse_label_mappings.get(label_name):
        no_groups[label_name] = label_data

with open(p_file, 'w') as new_params_file :
    _nl = '\n'
    _now = datetime.datetime.now()
    _ts_now=_now.strftime("%Y-%m-%d %H:%M:%S")
    new_params_file.write(f'IMPORTANT: Last Change to input parameters on: {_ts_now}{_nl}{_nl}')


for label_name, label_params in label_mappings.items():
    writer = MarkdownTableWriter()
    writer.table_name = label_name
    writer.headers = ["Parameter label (name)", "Default", "Description"]
    writer.value_matrix = []
    writer.stream = io.StringIO()
    for lparam in label_params:
        writer.set_indent_level(4)
        writer.value_matrix.append([
        f"**{str(parameter_labels.get(lparam, 'NO_LABEL'))}**<br>(`{lparam}`)",
        str(parameter_mappings[lparam].get('Default', determine_optional_value(lparam))),
        str(parameter_mappings[lparam].get('Description', 'NO_DESCRIPTION'))
        ])
    writer.write_table()

    with open (p_file, 'a') as p:
        p.write(pypandoc.convert_text(writer.stream.getvalue(), 'asciidoc', format='markdown'))

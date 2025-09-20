import json
import re

rgx_code = re.compile(r'`([^`]+)`')

def convert_to_rst(data: list[dict]) -> str:
    rst_lines = []
    for block in data:
        title = block.get('title')
        descr = block.get('description')
        vars: dict[str, str] = block.get('variables', {})

        rst_lines.append(title)
        rst_lines.append('-' * len(title))
        rst_lines.append('')
        rst_lines.append(descr)
        rst_lines.append('')

        rst_lines.append('.. list-table::')
        rst_lines.append('  :widths: 20 80')
        rst_lines.append('  :header-rows: 1')
        rst_lines.append('')
        rst_lines.append('  * - Variable (=[default])')
        rst_lines.append('    - Description')

        var_names = sorted(vars.keys())

        for var in var_names:
            var_dct = vars[var]
            default = var_dct.get('default', '')
            usage = var_dct.get('usage', '')

            usage = rgx_code.sub(r'``\1``', usage)

            default = str(default).strip()
            if default.lower() == 'required':
                default = '*REQUIRED*'
            elif default.lower() == 'optional':
                default = '*OPTIONAL*'
            elif default:
                default = f'``{default}``'
            else:
                default = '*OPTIONAL*'

            rst_lines.append(f"  * - ``{var}``")
            rst_lines.append('')
            rst_lines.append(f"      = {default}")
            rst_lines.append(f"    - {usage}")
        rst_lines.append('')

    return '\n'.join(rst_lines)

if __name__ == '__main__':
    with open('environment_variables.json') as f:
        data = json.load(f)
    rst = convert_to_rst(data)
    with open('source/user/_env_vars.rst', 'w') as f:
        f.write(rst)

import json


INIT_FILE = 'init.txt'


def get_problem_name(polygon_shortname):
    filename = 'polygon-contest/problems/%s/statements/russian/problem-properties.json' % polygon_shortname
    with open(filename, encoding='utf-8') as f:
        content = f.read()
    parsed = json.loads(content) 
    return parsed['name']

min_row = -4
max_row = 4
min_column = -5


with open('init_script.py', 'w', encoding='utf-8') as output_file:
    print('from map.models import *', file=output_file)
    print('AbstractTile.objects.all().delete()', file=output_file)
    
    with open(INIT_FILE, 'r', encoding='utf-8') as init:
        for line in init:
            line = line.strip().split()
            # 0 0 00 registration-newyear 100 0 
            column, row, polygon_id, polygon_shortname, award, open_time = line[:6]
            row = -int(row) + max_row
            column = int(column) - min_column
            bonus = ''
            if len(line) > 6:
                bonus = line[-1]
    
            if bonus == '':
                class_name = 'Problem'
            elif bonus == 'freetile':
                class_name = 'OpenAnyTileBonus'
            elif bonus == 'tangerines':
                class_name = 'GetTangerinesBonus'
            elif bonus == 'andrew':
                class_name = 'CallMasterBonus'
            else:
                raise Exception('Unknown bonus: %s' % bonus)
    
            parameters = 'row=%d, column=%d, ejudge_short_name="%02d", name="%s", statement_file_name="%02d.pdf", automatic_open_time=%d' % \
                (int(row), int(column), int(polygon_id), get_problem_name(polygon_shortname), int(polygon_id), int(open_time)) 
    
            if bonus == '':
                parameters += ', solved_award=%d, wrong_penalty=%d' % (int(award), int(award) // 20)
    
            print('%s(%s).save()' % (class_name, parameters), file=output_file)
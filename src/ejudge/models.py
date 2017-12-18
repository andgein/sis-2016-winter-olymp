import re
import datetime

from django.conf import settings


class Contest:
    def __init__(self, serve_cfg_name):
        self.serve_cfg = self.read_serve_cfg(serve_cfg_name)

        self.problems = self.extract_problems_from_serve_cfg(self.serve_cfg)

        self.start_time = settings.CONTEST_START_TIME
        self.finish_time = self.start_time + \
            datetime.timedelta(minutes=settings.CONTEST_DURATION)
        self.fog_time = self.finish_time - \
            datetime.timedelta(minutes=int(self.serve_cfg['_GLOBAL_']['board_fog_time']))
        self.unfog_time = self.finish_time + \
            datetime.timedelta(minutes=int(self.serve_cfg['_GLOBAL_']['board_unfog_time']))

    @staticmethod
    def read_serve_cfg(serve_cfg_name):
        multi_sections_names = {'language', 'problem', 'tester'}

        result = {'_GLOBAL_': {}}
        current_section = result['_GLOBAL_']
        with open(serve_cfg_name, encoding=settings.EJUDGE_SERVE_CFG_ENCODING) as serve_cfg:
            for line in serve_cfg:
                line = line.strip()
                if not len(line):
                    continue

                if line[0] == '#':
                    continue

                section_match = re.match(r'\[(.+)\]', line)
                if section_match:
                    section_name = section_match.group(1)
                    current_section = {}
                    if section_name in multi_sections_names:
                        if section_name not in result:
                            result[section_name] = []
                        # noinspection PyUnresolvedReferences
                        result[section_name].append(current_section)
                    else:
                        result[section_name] = current_section
                else:
                    splitted = line.split('=', 2)
                    param_name = splitted[0].strip()
                    param_value = splitted[1].strip() if len(splitted) > 1 else True
                    if type(param_value) is str and len(param_value) > 2 and param_value[0] == param_value[-1] == '"':
                        param_value = param_value[1:-1]

                    current_section[param_name] = param_value

        return result

    @staticmethod
    def extract_problems_from_serve_cfg(serve_cfg):
        problems = {}

        for problem_array in serve_cfg['problem']:
            problem = Problem(**problem_array)
            if problem.is_abstract:
                continue

            problems[int(problem.id)] = problem

        return problems


class Problem:
    def __init__(self, short_name, long_name='', **kwargs):
        self.id = kwargs.get('id', 'UNKNOWN')
        self.short_name = short_name
        self.long_name = long_name
        self.is_abstract = kwargs.get('abstract', False)

    def __str__(self):
        return 'Problem %s: «%s»' % (self.short_name, self.long_name)

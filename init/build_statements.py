#!/usr/bin/env python3

import codecs
import os
import os.path
import shutil
import subprocess
import logging
import glob
import json

CONTEST_DIR = 'polygon-contest'
BUILD_DIR = 'build'
LANGUAGE = 'russian'
FILES_DIR = 'files-' + LANGUAGE


def time_limit_from_int(tl):
    tl //= 1000
    return str(tl) + ' секунд' + ('a' if tl == 1 else 'ы')

def memory_limit_from_int(ml):
    return str(ml // (1024 ** 2)) + ' мегабайт'

def build_with_text(text, replace_data, result, section='', problem_name=''):
    text = text.replace('%TEXT%', section + '\n' + replace_data)

    with codecs.open(os.path.join(BUILD_DIR, 'data.tex'), 'w', 'utf-8') as data_file:
        data_file.write(text)

    cwd = os.getcwd()
    os.chdir(BUILD_DIR)
    logging.info('Compile problem %s' % problem_name)
    for _ in range(2):
        subprocess.check_output(['pdflatex', '-quiet', 'compile.tex'])
    os.chdir(cwd)

    shutil.copy(os.path.join(BUILD_DIR, 'compile.pdf'), os.path.join(FILES_DIR, result))


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    if not os.path.exists(FILES_DIR):
        logging.info('Create folder for output files: %s' % FILES_DIR)
        os.mkdir(FILES_DIR)
    if not os.path.exists(BUILD_DIR):
        logging.info('Create folder for build files: %s' % BUILD_DIR)
        os.mkdir(BUILD_DIR)

    problems_dir = os.path.join(CONTEST_DIR, 'problems')
    for problem_counter, problem_dir in enumerate(glob.glob(os.path.join(problems_dir, '*')), start=1):
        statement_dir = os.path.join(problem_dir, 'statements', LANGUAGE)
        properties_file_name = os.path.join(statement_dir, 'problem-properties.json')
        logging.info('Read problem properties file %s' % properties_file_name)

        with codecs.open(properties_file_name, 'r', 'utf-8') as properties_file:
            properties = json.load(properties_file)

            name = properties['name']
            legend = properties['legend']
            input_file = properties['inputFile']
            output_file = properties['outputFile']
            time_limit = time_limit_from_int(properties['timeLimit'])
            memory_limit = memory_limit_from_int(properties['memoryLimit'])
            input_format = properties['input']
            output_format = properties['output']

            # print('UPDATE problems SET description = "%s" WHERE id = %d;' % (legend, 14 + problem_counter))

            shutil.copy('template.tex', os.path.join(BUILD_DIR, 'compile.tex'))
            shutil.copy('olymp.sty', os.path.join(BUILD_DIR, 'olymp.sty'))
            with codecs.open('data.tex', 'r', 'utf-8') as data_file:
                data = data_file.read()

            data = data.replace('%NAME%', name).replace('%INPUT_FILE%', input_file).replace('%OUTPUT_FILE%', output_file).\
                        replace('%TIME_LIMIT%', time_limit).replace('%MEMORY_LIMIT%', memory_limit).\
                        replace('%PROBLEM_COUNTER%', str(problem_counter)).\
                        replace('%STATEMENT_DIR%', os.path.join('..', statement_dir).replace('\\', '/') + '/')

            problem_name = os.path.basename(problem_dir)
            build_with_text(data, legend + '\n\\InputFile\n' + input_format + '\n\\OutputFile\n' + output_format, problem_name + '.pdf', problem_name=problem_name)
            # build_with_text(data, input_format, problem_name + '-input-format.pdf', problem_name=problem_name, section=r'\InputFile')
            # build_with_text(data, output_format, problem_name + '-output-format.pdf', problem_name=problem_name, section=r'\OutputFile')


if __name__ == '__main__':
    main()
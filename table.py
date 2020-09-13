# python version 3.8 required

from sys import stdin as s
from sys import stdout

def add_table_headers_to_list(line: str) -> list:
    headers = []
    for header in line.split("] "):
        header = header.strip().replace("]", "").replace("[", "")
        headers.append(header.center(4))
    return headers

def add_data_to_rows(data: list) -> list:
    data_by_rows = []
    for row in data:
        data_by_rows.append(row.rstrip().split(" "))
    return data_by_rows

def create_table(headers: list, data: list) -> None:
    width = len(headers)
    for word in headers:
        width += len(word)

    width_table = [len(word) for word in headers]

    top_line = '.'
    for width in width_table:
        top_line += f'{"-"*width}+'
    top_line = f'{top_line[:-1]}.'

    mid_delimiter = "|"
    for width in width_table:
        mid_delimiter += f'{"-" * width}+'
    mid_delimiter = f'{mid_delimiter[:-1]}|'

    bottom_line = '\''
    for width in width_table:
        bottom_line += f'{"-"*width}+'
    bottom_line = f'{bottom_line[:-1]}\''

    table = f'{top_line}\n'
    # add the headers
    for header in headers:
        table += f'|{header}'
    table = table[:-1] + ' |'
    table += f'\n{mid_delimiter}\n|'

    # add the data
    for row in data:
        for i in range(0,len(row)):
            table += f'{row[i].center(width_table[i])}|'
        table += f'\n{mid_delimiter}\n|'

    # clean up the bottom
    table = table[:(len(table) - len(mid_delimiter) -2)]

    # add the bottom line
    table += f'{bottom_line}'

    return table

data = s.read().splitlines()
if table_headers := data.pop(0): # need python 3.8 for walrus use :=

    table_headers = add_table_headers_to_list(table_headers)
    data_by_rows = add_data_to_rows(data)

    stdout.write(create_table(table_headers, data_by_rows))
else:
    stdout.write("ERROR NO INPUT DATA")

# python version 3.8 required
# requires module tkinter

from sys import stdin as s
from sys import stdout
from sys import argv
import tkinterTrimmed as tk

from pyperclipTrimmed import copy  # pyperclip not necessary to install


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        print("open")
        topFrame = tk.Frame(self)
        topFrame.pack()

        rowsLbl = tk.Label(topFrame, text="Rows:")
        self.rowsEnt = tk.Entry(topFrame, width=5)
        rowsLbl.pack(side="left")
        self.rowsEnt.pack(side="left")

        colsLbl = tk.Label(topFrame, text="Columns:")
        self.colsEnt = tk.Entry(topFrame, width=5)
        colsLbl.pack(side="left")
        self.colsEnt.pack(side="left")

        enterBtn = tk.Button(text="Generate", width=22, command=self.createGrid)
        enterBtn.pack()

    def createGrid(self):
        if self.rowsEnt.get() and self.colsEnt.get():
            child = tk.Tk()

            rows = int(self.rowsEnt.get())
            cols = int(self.colsEnt.get())
            print(f"\n\n{rows}x{cols}\n\n")
            matrix = [[] for _ in range(rows)]
            for i in range(rows):
                child.rowconfigure(i, )  # minsize=50)

                for j in range(0, cols):
                    child.columnconfigure(j, weight=1, )
                    if i % 2 == 0:
                        entry = tk.Entry(master=child, justify="center", width=12, bg="gray90")  # {i} Column {j}")
                    else:
                        entry = tk.Entry(master=child, justify="center", width=12)
                    entry.grid(row=i, column=j, sticky="ew")  # pack(padx=2, pady=2)
                    matrix[i].append(entry)

            copyBtn = tk.Button(master=child, text="Copy", width=10, command=lambda: copy(entriesToTable(matrix)))
            copyBtn.grid(row=rows, column=0, columnspan=cols)
            child.mainloop()


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


def create_table(headers: list, data: list) -> str:
    width = len(headers)
    for word in headers:
        width += len(word)

    width_table = [len(word) for word in headers]

    top_line = '.'
    for width in width_table:
        top_line += f'{"-" * width}+'
    top_line = f'{top_line[:-1]}.'

    mid_delimiter = "|"
    for width in width_table:
        mid_delimiter += f'{"-" * width}+'
    mid_delimiter = f'{mid_delimiter[:-1]}|'

    bottom_line = '\''
    for width in width_table:
        bottom_line += f'{"-" * width}+'
    bottom_line = f'{bottom_line[:-1]}\''

    table = f'{top_line}\n'
    # add the headers
    for header in headers:
        table += f'|{header}'
    table = f'{table}|'
    table += f'\n{mid_delimiter}\n|'

    # add the data
    for row in data:
        for i in range(0, len(row)):
            table += f'{row[i].center(width_table[i])}|'
        table += f'\n{mid_delimiter}\n|'

    # clean up the bottom
    table = table[:(len(table) - len(mid_delimiter) - 2)]

    # add the bottom line
    table += f'{bottom_line}'

    return table


def entriesToTable(matrix):
    tableHeaders = [entry.get() for entry in matrix[0]]
    dataByRows = [[entry.get() for entry in matrix[i + 1]] for i in range(len(matrix) - 1)]
    return create_table(tableHeaders, dataByRows)


if len(argv) < 2:
    root = tk.Tk()
    app = App(root)
    app.mainloop()
else:
    data = s.read().splitlines()
    if table_headers := data.pop(0):  # need python 3.8 for walrus use :=

        table_headers = add_table_headers_to_list(table_headers)
        data_by_rows = add_data_to_rows(data)

        stdout.write(create_table(table_headers, data_by_rows))

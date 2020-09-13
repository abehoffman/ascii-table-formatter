# CS302 ASCII TABLE FORMATTER
This formatter allows you to automatically format an ASCII table for use on homeworks in CS202 so you don't have to spend a bunch of time working
on the ASCII art to make your truth tables look nice.

Here is an example output table:
```
.----+----+-----------+-------.
| A  | B  |Description|Output |
|----+----+-----------+-------|
| 0  | 0  |   zebra   |  1    |
|----+----+-----------+-------|
| 0  | 0  |    bear   |  0    |
|----+----+-----------+-------|
| 0  | 1  |  unicorn  |  1    |
|----+----+-----------+-------|
| 0  | 1  |   llama   |  0    |
|----+----+-----------+-------|
| 1  | 0  |   whale   |  1    |
|----+----+-----------+-------|
| 1  | 0  |  ostrich  |  0    |
|----+----+-----------+-------|
| 1  | 1  |   dragon  |  0    |
|----+----+-----------+-------|
| 1  | 1  |   monkey  |  0    |
'----+----+-----------+-------'
```

#### Prerequesites

This requires Python 3.8 which can be downloaded [here](https://www.python.org/downloads/) _(Python 3.8.x works great)_

If you don't want to download a new python, merely change line 63 in this [file](/table.py) to not use the `walrus operator :=`.

## Now on to the fun part, how you can use it––

Simply paste your pre-formatted table like the one seen below into the `in.txt`

**NOTE:The table headers are required to be wrapped in `[]`**

```
[A] [B] [Description] [Output]
0 0 zebra 1
0 0 bear 0
0 1 unicorn 1
0 1 llama 0
1 0 whale 1
1 0 ostrich 0
1 1 dragon 0
1 1 monkey 0
```

Since it uses `stdin` and `stdout` from the `sys` library, you can set the input and output file paths.
```python3 table.py < in.txt > out.txt```

Hopefully this saves you a bit of time.

### How can I use this?
Either copy and paste the table.py file into your editor of choice or clone the repo with git. More information on how to use git can be found [here](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository).



# Python M99

A M99 emulator written in Python.
This emulator allows you to run M99 programs on your computer and to run them step by step while watching the registers and memory change in real time.

## Usage

The python file [M99.py](M99.py) is the main file of the emulator. It can be used as a module or as a standalone program and it allow to run the M99 but you can't see the registers and memory change in real time.

The python file [M99_gui.py](M99_gui.py) is a standalone program that allow you to run the M99 and to see the registers and memory change in real time. In a graphical interface.

### Gui

The gui is composed of 3 parts:

- The registers
- The memory
- The controls buttons

#### Registers

The registers are displayed in a list. They are displayed in decimal.

#### Memory

The memory is displayed in a grid. You can't edit the memory for now but it will be possible in the future.
Under the values, the ASM code is displayed if it is relevant and valid.

The stack pointer is represented by a light blue square and the program counter by a light green square.

#### Controls buttons

There are 7 buttons:
| Button | Description |
| :----: | :---------: |
| `Load` | Load a M99 program from a file |
| `Jump` | Jump to a specific address |
| `Execute` | Execute the program until the end |
| `Step` | Execute the next instruction |
| `Reset` | Reset the registers |
| `Clear` | Clear the memory |
| `Quit` | Quit the program |

## Dependencies

The emulator is written using python `3.11.15`. Because it use the `match` statement, the minimum version of python required is `3.10.x`.

The GUI is written using the `tkinter` module. It is in most of the case already installed with python but if it is not the case you can install it with the command :

`pip install tkinter`.

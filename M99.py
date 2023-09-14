#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M99 Machine
"""
import re
import sys
import argparse

# Token format: (regex, (opcode, arg1, arg2, ...))
# if argument is negative, it refer to a regex group
# else it is a constant
REGISTER_TOKENS = "(A|B|R|PC|SB|RA)"
TOKENS = [
    (r"^\s*STR ([0-9]{1,2})$", (0, 0, -1)),
    (r"^\s*LDA ([0-9]{1,2})$", (1, 0, -1)),
    (r"^\s*LDB ([0-9]{1,2})$", (2, 0, -1)),
    (r"^\s*MOV " + REGISTER_TOKENS + " " + REGISTER_TOKENS + "$", (3, -1, -2)),
    (r"^\s*ADD$", (4, 0, 0)),
    (r"^\s*SUB$", (4, 0, 1)),
    (r"^\s*MUL$", (4, 0, 2)),
    (r"^\s*JMP ([0-9]{1,2})$", (5, 0, -1)),
    (r"^\s*JPP ([0-9]{1,2})$", (6, 0, -1)),
    (r"^\s*JEQ ([0-9]{1,2})$", (7, 0, -1)),
    (r"^\s*JNE ([0-9]{1,2})$", (8, 0, -1)),
    (r"^\s*CAL ([0-9]{1,2})$", (9, 0, -1)),
    (r"^\s*RET$", (4, 0, 9)),
    (r"^\s*PSH " + REGISTER_TOKENS + "$", (4, 8, -1)),
    (r"^\s*POP " + REGISTER_TOKENS + "$", (4, 9, -1)),
    (r"^\s*DAT ([0-9]{1,3})$", (0, 0, -1)),
]


class M99:
    def __init__(self) -> None:
        self.update_event = None
        self.mem = [0] * 99
        self.read_value = M99.read_value
        self.write_value = M99.write_value
        self.restart()

    def restart(self) -> None:
        self.reg = [
            0,  # R
            0,  # A
            0,  # B
            0,  # PC
            98,  # SB
            0,  # RA
        ]
        self._shutdown = False
        self.emit_update_event()

    def shutdown(self) -> None:
        self._shutdown = True
        self.emit_update_event()

    def after_exec(self, callback: callable) -> None:
        """
        Set the callback to be executed after each instruction.

        Args:
            callback (callable): callback to be executed after each instruction.
        """
        self.update_event = callback

    @staticmethod
    def read_value() -> int:
        """
        Read a value from the standard input.

        Returns:
            int: value read from the standard input.
        """
        print("Enter a value: ", end="")
        valid = False
        while not valid:
            value = input()
            if value.isnumeric():
                valid = True
            else:
                print("Invalid input. Enter a value: ", end="")
        return int(value)

    @staticmethod
    def write_value(value: int) -> None:
        """
        Write a value to the standard output.

        Args:
            value (int): value to be written to the standard output.
        """
        print(value)

    @staticmethod
    def reg_to_id(reg: str) -> int:
        """
        Convert the given register to its corresponding id.

        Args:
            reg (str): register to be converted.

        Returns:
            int: id of the given register.
        """
        match reg:
            case "R":
                return 0
            case "A":
                return 1
            case "B":
                return 2
            case "PC":
                return 3
            case "SB":
                return 4
            case "RA":
                return 5
            case _:
                raise ValueError("Invalid register.")

    @staticmethod
    def id_to_reg(id: int) -> str:
        """
        Convert the given register id to its corresponding register name.

        Args:
            id (int): register id to be converted.

        Returns:
            str: the corresponding register name.
        """
        match id:
            case 0:
                return "R"
            case 1:
                return "A"
            case 2:
                return "B"
            case 3:
                return "PC"
            case 4:
                return "SB"
            case 5:
                return "RA"
            case _:
                raise ValueError("Invalid register id.")

    @staticmethod
    def manage_overflow(value: int) -> int:
        """
        Make sure the given value is not greater than 999 and not less than -999
        by cycling it.

        Args:
            value (int): value to be managed.

        Returns:
            int: managed value.
        """
        while value > 999:
            value -= 1999

        while value < -999:
            value += 1999

        return value

    def exec_reg_op(self, opcode: int) -> None:
        match opcode:
            case 0:
                self.reg[0] = self.reg[1] + self.reg[2]
            case 1:
                self.reg[0] = self.reg[1] - self.reg[2]
            case 2:
                self.reg[0] = self.reg[1] * self.reg[2]
            case 9:
                self.reg[3] = self.reg[5] - 1
            case _:
                if opcode < 80:
                    raise ValueError("Invalid register operation.")

                self.stack_op(opcode)

        self.reg[0] = M99.manage_overflow(self.reg[0])

    def stack_op(self, opcode: int) -> None:
        """
        Execute a stack operation.

        Args:
            opcode (int): opcode to be executed in the form of a 3-digit integer.
        """
        stack_op = opcode // 10
        reg = opcode % 10
        if stack_op == 8:
            if self.reg[4] <= 0:
                raise ValueError("Stack overflow")
            self[self.reg[4]] = self.reg[reg]
            self.reg[4] -= 1
        elif stack_op == 9:
            if self.reg[4] >= 98:
                raise ValueError("Stack is empty.")
            self.reg[4] += 1
            self.reg[reg] = self[self.reg[4]]

    def __exec(self, opcode: int) -> None:
        """
        Execute the given opcode in the M99 machine.

        Args:
            opcode (int): opcode to be executed in the form of a 3-digit integer.
        """

        if opcode > 999 or opcode < 0:
            raise ValueError("Opcode must be a 3-digit integer.")

        data = opcode % 100
        identifier = opcode // 100

        match identifier:
            case 0:  # STR
                self[data] = self.reg[0]
            case 1:  # LDA
                self.reg[1] = self[data]
            case 2:  # LDB
                self.reg[2] = self[data]
            case 3:  # MOV
                reg1 = data // 10
                reg2 = data % 10
                self.reg[reg2] = self.reg[reg1]
            case 4:  # ADD, SUB, MUL, PSH, POP, RET...
                self.exec_reg_op(data)
            case 5:  # JMP
                self.reg[3] = data
            case 6:  # JPP
                if self.reg[0] > 0:
                    self.reg[3] = data - 1
            case 7:  # JEQ
                if self.reg[0] == 0:
                    self.reg[3] += 1
            case 8:  # JNE
                if self.reg[0] != 0:
                    self.reg[3] += 1
            case 9:  # CAL
                self.reg[5] = self.reg[3] + 1
                self.reg[3] = data - 1
            case _:  # Not a valid identifier
                raise ValueError("Invalid identifier.")

    def load(self, program: list[int], offset: int = 0) -> None:
        """
        Load a program into the M99 machine.

        Args:
            program (list[int]): program to be loaded into the M99 machine.
            offset (int): base memory address to load the program into.
        """

        if len(program) + offset > 98:
            raise ValueError("Program too long.")

        self.mem[offset : len(program) + offset] = program

    def clear(self) -> None:
        """
        Clear the memory of the M99 machine.
        """
        self.mem = [0] * 99

    def __getitem__(self, key: int) -> int:
        """
        Get the value of the memory cell at the given index.

        Args:
            key (int): index of the memory cell.

        Returns:
            int: value of the memory cell at the given index.
        """

        if key > 99 or key < 0:
            raise ValueError("Memory cell index out of range.")

        if key == 99:
            value = self.read_value()
            if value is None:
                self.shutdown()
                raise ValueError("Invalid input.")
            return M99.manage_overflow(value)

        return self.mem[key]

    def __setitem__(self, key: int, value: int) -> None:
        """
        Set the value of the memory cell at the given index.

        Args:
            key (int): index of the memory cell.
            value (int): value to be set.
        """

        if key > 99 or key < 0:
            raise ValueError("Memory cell index out of range.")

        value = M99.manage_overflow(value)

        if key == 99:
            self.write_value(value)
            return

        self.mem[key] = value

    def step(self) -> None:
        """
        Execute the instruction located in SP and increment it
        """
        if self._shutdown:
            return

        self.__exec(self.mem[self.reg[3]])

        self.reg[3] += 1
        if self.reg[3] >= 99:
            self._shutdown = True

        self.emit_update_event()

    def emit_update_event(self) -> None:
        if self.update_event:
            self.update_event()

    def run(self, offset: int = 0) -> None:
        """
        Run the program loaded into the M99 machine.

        Args:
            offset (int): base memory address to start the program from.
        """
        if offset > 0:
            self.reg[3] = offset

        while not self._shutdown:
            self.step()


def search_match(line: str, line_nb: int) -> tuple[re.Match, tuple[int, int, int]]:
    """
    Search for a match in the given line.

    Args:
        line (str): line to be searched.
        line_nb (int): line number.

    Returns:
        tuple[re.Pattern, tuple[int, int, int]]: match object and opcode.
    """
    for token in TOKENS:
        match = re.match(token[0], line)
        if match:
            return (match, token[1])

    raise ValueError(f"Invalid instruction at line {line_nb} : {line}")


def scan_labels(labels: dict[str, int], lines: list[str]) -> str:
    """
    Scan the code to find labels and return the code without labels
    This function also remove empty lines

    Args:
        labels (dict[str, int]): The labels dict
        lines (list[str]): list of lines representing the assembly code

    Returns:
        str: the code without labels
    """
    code = []
    address = 0
    for l in lines:
        if re.match(r"^\s*$", l):
            continue

        if m := re.match(r"^\s*:([A-Za-z][a-zA-Z09_\-]+)$", l):
            labels[m.group(1)] = address
        else:
            code.append(l)
            address += 1
    return code


def assemble(code: str) -> list[int]:
    """
    Assemble the given code into a program for the M99 machine.

    Args:
        code (str): code to be assembled.

    Returns:
        list[int]: assembled program.
    """

    program = []
    labels = {}
    lines = code.split("\n")
    lines = scan_labels(labels, lines)

    line_nb = 0

    for line in lines:
        # skip empty lines
        line_nb += 1

        line = replace_labels(labels, line)

        (instruction_match, token) = search_match(line, line_nb)
        if token is None:
            continue
        opcode = token[0]
        for i in range(1, len(token)):
            opcode *= 10
            if token[i] < 0:
                data = instruction_match.group(-token[i])
                if data.isnumeric():
                    opcode += int(data)
                else:
                    opcode += M99.reg_to_id(data)
            else:
                opcode += token[i]

        program.append(opcode)

    return program


def replace_labels(labels: dict[str, int], line: str) -> str:
    """
    Replace labels in the given line.

    Args:
        labels (dict[str, int]): labels dict.
        line (str): line to be processed.
    """

    for m in re.finditer(r"@([a-zA-Z][a-zA-Z0-9_\-]*)", line):
        line = line.replace(m.group(0), str(labels[m.group(1)]))

    return line


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="M99 Machine Emulator",
        epilog = "Error codes: 1: Assembler error 2: Runtime error"
    )
    parser.add_argument("file", type=argparse.FileType("r"), help="file to assemble and run")
    
    args = parser.parse_args()
    with open(args.file.name, "r") as f:
        code = f.read()
    
    try:
        program = assemble(code)
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    m99 = M99()
    try:
        m99.load(program)
        m99.run()
    except ValueError as e:
        print(e)
        sys.exit(2)

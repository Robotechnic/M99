import M99
from tkinter import Frame, Label, Tk, Button, Widget, LabelFrame
from tkinter.messagebox import showinfo, showerror
from tkinter.simpledialog import askinteger
from tkinter.filedialog import askopenfilename

# 1 means the instruction takes one argument and it's not a register
# 2 means the instruction takes two registers as arguments
# 0 means the instruction takes no argument
# -1 means the instruction takes one argument but it's a register

INSTRUCTIONS_REPR = {
    0: ("STR", 1),
    1: ("LDA", 1),
    2: ("LDB", 1),
    3: ("MOV", 2),
    4: {
        0: {0: ("ADD", 0), 1: ("SUB", 0), 2: ("MUL", 0), 9: ("RET", 0)},
        8: ("PSH", -1),
        9: ("POP", -1),
    },
    5: ("JMP", 1),
    6: ("JPP", 1),
    7: ("JEQ", 1),
    8: ("JNE", 1),
    9: ("CAL", 1),
}


class MemoryCell(Frame):
    def __init__(self, master: Widget, value: int, **kwargs) -> None:
        super().__init__(
            master,
            borderwidth=1,
            relief="solid",
            padx=8,
            pady=3,
            **kwargs,
        )
        self.grid_propagate(0)
        self.value = value
        self.create_widgets()
        self.set_bg(kwargs.get("bg", "white"))

    @staticmethod
    def opcode_to_str(opcode: int) -> str:
        """
        Convert an opcode to its string representation.

        Args:
            opcode (int): The opcode to convert.

        Returns:
            str: The string representation of the opcode.
        """
        if opcode == 0:
            return ""

        opcode_len = 3
        opcode_repr = INSTRUCTIONS_REPR
        while opcode_len > 0:
            opcode_len -= 1
            digit = opcode // (10 ** (opcode_len))
            opcode = opcode % (10**opcode_len)
            if digit not in opcode_repr:
                return ""

            opcode_repr = opcode_repr[digit]
            if isinstance(opcode_repr, tuple):
                match opcode_repr[1]:
                    case 0:
                        return opcode_repr[0]
                    case 1:
                        return f"{opcode_repr[0]} {opcode}"
                    case 2:
                        return f"{opcode_repr[0]} {M99.M99.id_to_reg(opcode // 10)} {M99.M99.id_to_reg(opcode % 10)}"
                    case -1:
                        return f"{opcode_repr[0]} {M99.M99.id_to_reg(opcode % 10)}"
                    case _:
                        raise ValueError("Invalid representation")

    def create_widgets(self) -> None:
        """
        Create the MemoryCell based on the value.
        It represent the value and if not null, the corresponding instruction
        """
        self.value_label = Label(
            self, text=f"{self.value}", font=("Monospace", 20), width=4
        )
        self.instruction_label = Label(
            self,
            text=f"{self.opcode_to_str(self.value)}",
            font=("Monospace", 10),
            width=6,
        )
        self.value_label.pack(side="top")
        self.instruction_label.pack(side="bottom")

    def set_opcode(self, opcode: int) -> None:
        """
        Set the opcode of the cell.

        Args:
            opcode (int): The opcode to set.
        """
        self.value = opcode
        self.value_label["text"] = f"{self.value}"
        self.instruction_label["text"] = f"{self.opcode_to_str(self.value)}"

    def set_bg(self, bg: str) -> None:
        """
        Set the background color of the cell.

        Args:
            bg (str): The background color to set.
        """
        self.value_label.config(bg=bg)
        self.instruction_label.config(bg=bg)

    def config(self, **kwargs) -> None:
        """
        Configure the cell.

        Args:
            **kwargs: The configuration to set.
        """
        super().config(**kwargs)
        if "bg" in kwargs:
            self.set_bg(kwargs["bg"])


class M99Interface(Frame):
    def __init__(self, master: Tk, machine: M99.M99) -> None:
        super().__init__(master)
        self.machine = machine
        self.machine.after_exec(self.update_display)
        self.machine.read_value = self.input_value
        self.machine.write_value = self.display_value
        self.pack()
        self.assembly = []
        self.create_widgets()

    def build_register_display(self) -> LabelFrame:
        """
        Build the display for the registers.
        """
        registers = LabelFrame(self, text="Registers")
        self.registers_labels = ["R", "A", "B", "PC", "SB", "RA"]
        self.reg_labels = []
        for i, reg in enumerate(self.registers_labels):
            self.reg_labels.append(
                Label(
                    registers,
                    text=f"{self.machine.reg[i]}",
                    height=2,
                    font=("Monospace", 20),
                )
            )
            Label(registers, text=f"{reg}:", height=2, font=("Monospace", 20)).grid(
                row=i, column=0
            )
            self.reg_labels[i].grid(row=i, column=1)

        return registers

    def display_value(self, value: int) -> None:
        """
        Display the given value.
        """
        print(value)
        showinfo("Value", f"The computer emit the value: {value}", parent=self)

    def input_value(self) -> int:
        """
        Input a value.
        """
        value = askinteger("Value", "Enter a value:", parent=self)
        print(f"Input: {value}")
        return value

    def update_register_display(self) -> None:
        """
        Update the register display.
        """
        for i, reg in enumerate(self.registers_labels):
            self.reg_labels[i]["text"] = f"{self.machine.reg[i]}"

    def build_memory_display(self) -> LabelFrame:
        """
        In format of 10 rows of 10 columns.
        """
        memory = LabelFrame(self, text="Memory")
        self.mem_labels = []
        for i in range(10):
            Label(memory, text=f"{i * 10}", width=4).grid(row=0, column=i + 1)
            row = []
            for j in range(10):
                Label(memory, text=f"{j}", width=4).grid(row=j + 1, column=0)
                if i == 9 and j == 9:
                    row.append(Label(memory, text="I/O"))
                else:
                    bg = "white"
                    if self.machine.reg[4] == i * 10 + j:
                        bg = "lightgreen"
                    elif self.machine.reg[3] == i * 10 + j:
                        bg = "lightblue"
                    row.append(MemoryCell(memory, self.machine.mem[i * 10 + j], bg=bg))
                row[j].grid(row=j + 1, column=i + 1)
            self.mem_labels.append(row)

        return memory

    def update_memory_display(self) -> None:
        """
        Update the memory display.
        """
        for i in range(10):
            for j in range(10):
                if i == 9 and j == 9:
                    continue
                bg = "white"
                if self.machine.reg[4] == i * 10 + j:
                    bg = "lightgreen"
                elif self.machine.reg[3] == i * 10 + j:
                    bg = "lightblue"
                self.mem_labels[i][j].set_opcode(self.machine.mem[i * 10 + j])
                self.mem_labels[i][j].config(bg=bg)

    def build_buttons(self) -> Frame:
        """
        Build the buttons.
        """
        buttons = Frame(self)
        Button(buttons, text="Jump", command=self.jump).grid(row=0, column=0)
        Button(buttons, text="Execute", command=self.run_machine).grid(row=0, column=1)
        Button(buttons, text="Step", command=self.next_instruction).grid(
            row=0, column=2
        )
        Button(buttons, text="Reset", command=self.machine.restart).grid(
            row=1, column=0
        )
        Button(buttons, text="Load", command=self.load).grid(row=1, column=1)
        Button(buttons, text="Quit", command=self.quit).grid(row=1, column=2)
        Button(buttons, text="Clear", command=self.machine.clear).grid(row=2, column=1)
        self.master.bind("<Return>",  lambda _: self.next_instruction())
        self.master.bind("<BackSpace>", lambda _: self.machine.clear())
        self.master.bind("<q>", lambda _: self.quit())
        self.master.bind("<c>", lambda _: self.machine.clear())
        self.master.bind("<l>", lambda _: self.load())
        self.master.bind("<j>", lambda _: self.jump())
        self.master.bind("<r>", lambda _: self.machine.restart())
        return buttons

    def next_instruction(self) -> None:
        """
        Execute the next instruction.
        """
        try:
            self.machine.step()
        except Exception as e:
            showerror("Error", f"An error occurred: {e}", parent=self)

    def run_machine(self) -> None:
        """
        Run the machine.
        """
        try:
            self.machine.run(-1)
        except Exception as e:
            showerror("Error", f"An error occurred: {e}", parent=self)

    def jump(self) -> None:
        """
        Jump to a specific address.
        """
        address = askinteger(
            "Jump", "Enter an address:", parent=self, minvalue=0, maxvalue=99
        )
        self.machine.reg[3] = address
        self.update_display()

    def load(self) -> None:
        """
        Load a program.
        """
        program_path = askopenfilename(
            title="Load a program", filetypes=[("M99 Program", "*.m99")]
        )
        if not program_path:
            return

        with open(program_path, "r") as program_file:
            program = program_file.read()

        try:
            self.assembly = M99.assemble(program)
            self.machine.load(self.assembly, 0)
            self.machine.restart()
            self.update_display()
        except Exception as e:
            showerror("Error", f"An error occurred:\n {e}", parent=self)

    def create_widgets(self) -> None:
        """
        Build the interface to debug the M99 machine.
        It displays registers, memory, and the stack.
        A button is provided to execute the next instruction.
        """
        self.build_register_display().grid(row=0, column=0)
        self.build_memory_display().grid(row=0, column=1, rowspan=2)
        self.build_buttons().grid(row=1, column=0)

    def update_display(self) -> None:
        """
        Update the display.
        """
        self.update_register_display()
        self.update_memory_display()
        self.update()


if __name__ == "__main__":
    root = Tk()
    pc = M99.M99()
    interface = M99Interface(root, pc)
    interface.mainloop()

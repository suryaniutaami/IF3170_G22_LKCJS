from util.parser import Parser
from core.state import State

packages, truck = Parser.parse("input.txt")

state = State(packages, truck)

import sys

from PyQt5 import QtCore

sys.path.append(sys.argv[1])

import PyTest.CppLib

mo = PyTest.CppLib.MyObject()

assert(mo.addThree(39) == 42)
assert(mo.addThree([38, 39, 40]) == [41, 42, 43])

assert(mo.addThree("SomeString") == "DefaultSomeStringThree")

assert(mo.findNeedle(["One", "Two", "Three"], "Two") == 1)
assert(mo.findNeedle(["One", "Two", "Three"], "Four") == -1)
assert(mo.findNeedle(["One", "Two", "Three"], "Th") == 2)
assert(mo.findNeedle(["One", "Two", "Three"], "Th", QtCore.Qt.MatchExactly) == -1)

assert(mo.const_parameters(30) == 15)
assert(mo.const_parameters(30, mo) == 10)

myMap = mo.getMyMap()
assert(myMap[42] == 7)
assert(not 7 in myMap)

keyMap = mo.getKeyBindings()
assert(keyMap[PyTest.CppLib.MyObject.TextCompletion] == "CTRL+A")

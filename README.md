# Parameters_Monitor
Python program for monitoring and recording cooling water flow and turbo and cryo pump parameters.
---
GUI and logic for acquisition of parameters form:
- custom build, Arduino based system for monitoring of MBE cooling water;
- turbo pumps;
- Edwards Cryo-Torr Cryopumps.

Data is saved in custom format in plain text file, suitable for the other program: PM_graph_viewer.

The .spec file is used for .exe creation with [PyInstaller](https://pyinstaller.org/).

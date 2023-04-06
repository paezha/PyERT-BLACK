# PyERT

Developer Names: Hongzhao Tan, Zabrain Ali, Jasper Leung, Mike Li, Linqi Jiang, Mengtong Shi
Supervisor: Dr. Antonio Paez

PyERT aims to emulate the main functionalities of GIS-based Episode Reconstruction Toolkit ([GERT](https://doi.org/10.1016/j.tbs.2017.04.001)) in a completely open-source package. GERT is a set of tools for working with GPS data and is used to identify stop and travel episodes and to match them to a network. among other functionality.

The folders and files for this project are as follows:

docs: Documentation for the project
gert-toolbox-files: Files of the original toolbox, source files and compiled files
refs: Reference material used for the project, including papers
quarto-example: Files for an example of how to use [Quarto](https://quarto.org/) computational notebooks 
src: Source code
test: Test cases

To run the program:
1. Run main.py (main_win.py if on a Windows machine)
2. Enter a path to the sample GPS data csv on your system (example data [here](https://github.com/paezha/PyERT-BLACK/tree/main/quarto-example/data/sample-gps))
3. (Optional) Enter a path to the OSM network data on your system (example data [here](https://github.com/paezha/PyERT-BLACK/tree/main/quarto-example/data/sample-osm)). This is an optional parameter, and the program will take the network data from the OpenStreetMap API if this input is left blank.
4. Enter a path to the output folder (can be any folder on your system). This is where the output files will be generated.
5. (Optional) Enter the radius in meters that activity location information will be collected from.
6. (Optional) Enter the number of points from the dataset to process
7. The program will then process the data. Output files will be generated in the specified output folder. If using main.py, the GeoJSON visualizations of the route and activity locations will appear in the browser. If using main_win.py, the hyperlinks for the GeoJSON files will be output in the console.

Inside the src folder, there are 8 main python files:
GPSPreprocess.py: processes GPS data points
ModeDetection.py: takes the processed GPS data points, separates them into segments, and determines travel modes for those segments.
Extractor.py: extracts stop segments and trip segments from the generated segments.
route_solver.py: matches GPS points in the trip segments onto transportation network and generate a route for the trip segments
variable_generator.py: generates route analysis variables for the route(s) that were generated by the Route Solver Module
activity_locations_identification.py: identifies and adds land use, buildings and/or amenities information from stop segments
main.py: Run this file to run the program. This file also generates the GeoJSON files for the generated routes and activity locations.
main_win.py: Run this file to run the program on a Windows machine. Basically the same as main.py


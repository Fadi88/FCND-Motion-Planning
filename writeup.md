## Project: 3D Motion Planning
![Quad Image](./misc/enroute.png)

---


# Required Steps for a Passing Submission:
1. Load the 2.5D map in the colliders.csv file describing the environment.
2. Discretize the environment into a grid or graph representation.
3. Define the start and goal locations.
4. Perform a search using A* or other search algorithm.
5. Use a collinearity test or ray tracing method (like Bresenham) to remove unnecessary waypoints.
6. Return waypoints in local ECEF coordinates (format for `self.all_waypoints` is [N, E, altitude, heading], where the drone’s start location corresponds to [0, 0, 0, 0].
7. Write it up.
8. Congratulations!  Your Done!

## [Rubric](https://review.udacity.com/#!/rubrics/1534/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it! Below I describe how I addressed each rubric point and where in my code each point is handled.

### Explain the Starter Code

#### 0. issues and solutions

seems that the interface between sim and code is not maintained/updated
those are some workarounds i had to do to get it to work.

1- when the sim starts, the vehicle is in a building, to get it to work i need to fly it manually first on top of that building

2- needed to install bresenham : pip install bresenham

3- scipy in the requirement doesnt work on ubuntu 24 : pip install --upgrade scipy

#### 1. Explain the functionality of what's provided in `motion_planning.py` and `planning_utils.py`
These scripts contain a basic planning implementation that includes...


### Implementing Your Path Planning Algorithm

#### 1. Set your global home position
Here students should read the first line of the csv file, extract lat0 and lon0 as floating point values and use the self.set_home_position() method to set global home. 

#### 2. creating graph from obstacle data
obstacles were porcessed in a seperate script create_graph.py, and saved as CSV to save processing time, hardcoding, target alt. and safety distance, and just read the graph and created the networkx graph in motion_planing.py

#### 3. generate a randon target and get closest graph node to it
using python random and get cloeset point as provided in the lecture

#### 4. A*
as provided in the lectures (with some changes), dropping the diagonals as it is not needed for a graph


### Execute the flight
#### 1. Does it work?
It works!

### Double check that you've met specifications for each of the [rubric](https://review.udacity.com/#!/rubrics/1534/view) points.

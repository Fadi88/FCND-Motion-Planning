# pylint: disable=C0115,E0401,C0116,C0301,C0209,W0511,W0212,C0103,C0114,W0401,W0614

import argparse
import time
import random
from enum import Enum, auto

import msgpack # type: ignore
import numpy as np
import networkx as nx
from udacidrone import Drone # type: ignore
from udacidrone.connection import MavlinkConnection # type: ignore
from udacidrone.frame_utils import global_to_local # type: ignore
from udacidrone.messaging import MsgID # type: ignore

from planning_utils import *


# need to update scipy on ubuntu 24 : pip install --upgrade scipy
# pip install bresenham
class States(Enum):
    MANUAL = auto()
    ARMING = auto()
    TAKEOFF = auto()
    WAYPOINT = auto()
    LANDING = auto()
    DISARMING = auto()
    PLANNING = auto()


class MotionPlanning(Drone):

    def __init__(self, connection):
        super().__init__(connection)

        self.target_position = np.array([0.0, 0.0, 0.0])
        self.waypoints = []
        self.in_mission = True
        self.check_state = {}

        # initial state
        self.flight_state = States.MANUAL

        # register all your callbacks here
        self.register_callback(MsgID.LOCAL_POSITION, self.local_position_callback)
        self.register_callback(MsgID.LOCAL_VELOCITY, self.velocity_callback)
        self.register_callback(MsgID.STATE, self.state_callback)

    def local_position_callback(self):
        if self.flight_state == States.TAKEOFF:
            if -1.0 * self.local_position[2] > 0.95 * self.target_position[2]:
                self.waypoint_transition()
        elif self.flight_state == States.WAYPOINT:
            if np.linalg.norm(self.target_position[0:2] - self.local_position[0:2]) < 1.0:
                if len(self.waypoints) > 0:
                    self.waypoint_transition()
                else:
                    if np.linalg.norm(self.local_velocity[0:2]) < 1.0:
                        self.landing_transition()

    def velocity_callback(self):
        if self.flight_state == States.LANDING:
            if self.global_position[2] - self.global_home[2] < 0.1:
                if abs(self.local_position[2]) < 0.01:
                    self.disarming_transition()

    def state_callback(self):
        if self.in_mission:
            if self.flight_state == States.MANUAL:
                self.arming_transition()
            elif self.flight_state == States.ARMING:
                if self.armed:
                    self.plan_path()
            elif self.flight_state == States.PLANNING:
                self.takeoff_transition()
            elif self.flight_state == States.DISARMING:
                if ~self.armed & ~self.guided:
                    self.manual_transition()

    def arming_transition(self):
        self.flight_state = States.ARMING
        print("arming transition")
        self.arm()
        self.take_control()

    def takeoff_transition(self):
        self.flight_state = States.TAKEOFF
        print("takeoff transition")
        self.takeoff(self.target_position[2])

    def waypoint_transition(self):
        self.flight_state = States.WAYPOINT
        print("waypoint transition")
        self.target_position = self.waypoints.pop(0)
        print("target position", self.target_position)
        self.cmd_position(
            self.target_position[0], self.target_position[1], self.target_position[2], self.target_position[3]
        )

    def landing_transition(self):
        self.flight_state = States.LANDING
        print("landing transition")
        self.land()

    def disarming_transition(self):
        self.flight_state = States.DISARMING
        print("disarm transition")
        self.disarm()
        self.release_control()

    def manual_transition(self):
        self.flight_state = States.MANUAL
        print("manual transition")
        self.stop()
        self.in_mission = False

    def send_waypoints(self):
        print("Sending waypoints to simulator ...")
        data = msgpack.dumps(self.waypoints)
        self.connection._master.write(data)

    def plan_path(self):
        self.flight_state = States.PLANNING
        print("Searching for a path ...")
        TARGET_ALTITUDE = 10
        SAFETY_DISTANCE = 5

        self.target_position[2] = TARGET_ALTITUDE

        # TODO: read lat0, lon0 from colliders into floating point values
        first_row = np.genfromtxt("colliders.csv", delimiter=",", max_rows=1, dtype=str)
        lat0 = float(first_row[0].strip().split()[1])
        lon0 = float(first_row[1].strip().split()[1])

        # TODO: set home position to (lon0, lat0, 0)
        self.set_home_position(lon0, lat0, 0)

        # TODO: retrieve current global position

        # TODO: convert to current local position using global_to_local()
        local_position = global_to_local(self.global_position, self.global_home)

        print(
            "global home {0}, position {1}, local position from obj {2}, local postion from utm{3}".format(
                self.global_home, self.global_position, self.local_position, local_position
            )
        )
        # Read in obstacle map
        data = np.loadtxt("colliders.csv", delimiter=",", dtype="Float64", skiprows=2)

        # Define a grid for a particular altitude and safety margin around obstacles
        grid, north_offset, east_offset = create_grid(data, TARGET_ALTITUDE, SAFETY_DISTANCE)
        print("North offset = {0}, east offset = {1}".format(north_offset, east_offset))
        # Define starting point on the grid (this is just grid center)
        grid_start = (-north_offset, -east_offset)
        # TODO: convert start position to current position rather than map center

        # Set goal as some arbitrary position on the grid
        # grid_goal = (-north_offset + 10, -east_offset + 10)
        # TODO: adapt to set goal as latitude / longitude position and convert

        n_rows, n_cols = grid.shape

        gx = random.randint(0, n_rows - 1)
        gy = random.randint(0, n_cols - 1)

        grid_goal = (gx, gy)

        # Run A* to find a path from start to goal
        # TODO: add diagonal motions with a cost of sqrt(2) to your A* implementation
        # or move to a different search space such as a graph (not done here)
        print("Local Start and Goal: ", grid_start, grid_goal)
        #path, _ = a_star(grid, heuristic, grid_start, grid_goal)
        # TODO: prune path to minimize number of waypoints
        #path = prune_path(path)
        #print(path)
        # TODO (if you're feeling ambitious): Try a different approach altogether!
        #g = create_graph(data, TARGET_ALTITUDE, SAFETY_DISTANCE)

        graph_data = np.loadtxt("graph.csv", delimiter=",", dtype="Float64", skiprows=2)

        g = nx.Graph()
        for e in graph_data:
            g.add_edge((e[0],e[1]) , (e[2],e[3]), weight = e[4])

        c_start = closest_point(g, grid_start)
        c_goal = closest_point(g, grid_goal)

        path, _ = a_star_graph(g, heuristic_graph, c_start, c_goal)
        print(len(path))
        print(path)
        # Convert path to waypoints
        waypoints = [[int(p[0] + north_offset), int(p[1] + east_offset), TARGET_ALTITUDE, 0] for p in path]
        # Set self.waypoints
        self.waypoints = waypoints
        # TODO: send waypoints to sim (this is just for visualization of waypoints)
        self.send_waypoints()

    def start(self):
        self.start_log("Logs", "NavLog.txt")

        print("starting connection")
        self.connection.start()

        # Only required if they do threaded
        # while self.in_mission:
        #    pass

        self.stop_log()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5760, help="Port number")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="host address, i.e. '127.0.0.1'")
    args = parser.parse_args()

    conn = MavlinkConnection("tcp:{0}:{1}".format(args.host, args.port), timeout=60)
    drone = MotionPlanning(conn)
    time.sleep(1)

    drone.start()

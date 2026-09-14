import pytest
import time
import math

from backend.autonomy.pose_estimator import PoseEstimator
from backend.autonomy.mapper import GlobalMapper, GRID_RESOLUTION_M
from backend.autonomy.planner import AStarPlanner, get_next_command
from backend.autonomy.explorer import FrontierExplorer

def test_pose_estimator_straight():
    est = PoseEstimator()
    est.update_velocity(1.0, 0.0) # 1 m/s straight
    est._last_update_time = time.time() - 1.0 # mock 1 second elapsed
    x, y, theta = est.get_pose()
    assert math.isclose(x, 1.0, abs_tol=0.1)
    assert math.isclose(y, 0.0, abs_tol=0.1)
    assert math.isclose(theta, 0.0, abs_tol=0.1)
    
def test_pose_estimator_turn():
    est = PoseEstimator()
    est.update_velocity(0.0, math.pi / 2) # Turn 90 degrees in 1 sec
    est._last_update_time = time.time() - 1.0
    x, y, theta = est.get_pose()
    assert math.isclose(x, 0.0, abs_tol=0.1)
    assert math.isclose(y, 0.0, abs_tol=0.1)
    assert math.isclose(theta, math.pi / 2, abs_tol=0.1)

def test_mapper_raycast():
    mapper = GlobalMapper()
    # Raycast forward 1.5m
    # 90 is straight ahead, 0 is right.
    mapper.update_from_tof((0.0, 0.0, 0.0), 90.0, 1500.0) # 1500mm = 1.5m
    
    # Origin is at mapper.origin_x, mapper.origin_y
    gx0, gy0 = mapper._world_to_grid(0.0, 0.0)
    gx1, gy1 = mapper._world_to_grid(1.5, 0.0)
    
    # Check that endpoint is occupied
    assert mapper._grid[gy1 * mapper.width + gx1] == 100
    
    # Check that midpoint is free
    gxm, gym = mapper._world_to_grid(0.5, 0.0)
    assert mapper._grid[gym * mapper.width + gxm] == 0

def test_planner():
    mapper = GlobalMapper()
    planner = AStarPlanner(mapper)
    
    # Make a clear path
    for i in range(10):
        gx, gy = mapper._world_to_grid(i * 0.1, 0.0)
        mapper._grid[gy * mapper.width + gx] = 0
        
    path = planner.plan((0.0, 0.0, 0.0), (0.9, 0.0))
    assert len(path) > 0
    
def test_next_command():
    pose = (0.0, 0.0, 0.0)
    
    # Path with next point far enough
    path = [(0.0, 0.5), (0.0, 1.0)]
    cmd, lin, ang = get_next_command(pose, path)
    assert cmd in ["FORWARD", "LEFT", "RIGHT"]
    
    # Empty path
    cmd, lin, ang = get_next_command(pose, [])
    assert cmd == "STOP"
    assert lin == 0.0
    assert ang == 0.0

@pytest.mark.asyncio
async def test_autonomy_engine_loop_regression():
    # Verify that the autonomy engine loop can successfully select a goal
    # without crashing due to missing imports (e.g., NameError for 'math')
    from backend.services.rover_state import RoverStateManager
    from backend.hardware.simulator.simulated_provider import SimulatedHardwareGateway
    from backend.websocket.manager import WebSocketManager
    from backend.autonomy.engine import AutonomyEngine
    import asyncio
    
    rover_state = RoverStateManager()
    rover_state.set_mode("AUTONOMOUS")
    gateway = SimulatedHardwareGateway(rover_state, WebSocketManager())
    engine = AutonomyEngine(rover_state, gateway, WebSocketManager())
    
    # Inject telemetry to create a frontier
    pose = (0.0, 0.0, 0.0)
    engine.mapper.update_from_tof(pose, 90.0, 1500.0)
    
    await gateway.start()
    await engine.start()
    
    # Allow the loop to tick a few times
    await asyncio.sleep(0.3)
    
    goal = engine._current_goal
    path = engine._current_path
    
    await engine.stop()
    await gateway.stop()
    
    # Verify it selected a goal and did not crash/emergency_stop
    assert goal is not None, "Engine failed to select a goal, likely due to a crash in the loop"
    assert len(path) > 0, "Engine failed to generate a path"
    assert rover_state.get_status().state != "EMERGENCY_STOP", "Engine threw an exception and stopped"

@pytest.mark.asyncio
async def test_engine_manual_mode_updates_pose():
    from backend.services.rover_state import RoverStateManager
    from backend.hardware.simulator.simulated_provider import SimulatedHardwareGateway
    from backend.websocket.manager import WebSocketManager
    from backend.autonomy.engine import AutonomyEngine
    import asyncio
    
    rover_state = RoverStateManager()
    rover_state.set_mode("MANUAL")
    gateway = SimulatedHardwareGateway(rover_state, WebSocketManager())
    engine = AutonomyEngine(rover_state, gateway, WebSocketManager())
    
    await gateway.start()
    await engine.start()
    
    # Simulate a manual movement command
    await gateway.send_command({"linear_mps": 0.3, "angular_rads": 0.0, "command_id": "test"})
    
    # Sleep to let engine loop run a few ticks and integrate velocity
    await asyncio.sleep(0.3)
    
    pose = engine.pose_estimator.get_pose()
    
    await engine.stop()
    await gateway.stop()
    
    # Pose X must be > 0.0 (integrated over ~0.3s)
    assert pose[0] > 0.05, "Pose did not update during MANUAL mode"
    assert pose[1] == 0.0, "Pose Y should not change for pure forward movement"

def test_mapper_moving_rover_raycast():
    mapper = GlobalMapper()
    
    # 1. Stationary origin, scan straight ahead
    mapper.update_from_tof((0.0, 0.0, 0.0), 90.0, 1500.0)
    
    # 2. Rover moved forward 2.0m, scan straight ahead
    mapper.update_from_tof((2.0, 0.0, 0.0), 90.0, 1500.0)
    
    # 3. Rover turned 90 degrees left (heading = pi/2), scan straight ahead
    mapper.update_from_tof((0.0, 0.0, math.pi / 2), 90.0, 1500.0)
    
    # The first should occupy (1.5, 0.0)
    gx1, gy1 = mapper._world_to_grid(1.5, 0.0)
    assert mapper._grid[gy1 * mapper.width + gx1] == 100
    
    # The second should occupy (3.5, 0.0)
    gx2, gy2 = mapper._world_to_grid(3.5, 0.0)
    assert mapper._grid[gy2 * mapper.width + gx2] == 100
    
    # The third should occupy (0.0, 1.5)
    gx3, gy3 = mapper._world_to_grid(0.0, 1.5)
    assert mapper._grid[gy3 * mapper.width + gx3] == 100

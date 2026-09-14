import asyncio
import time
import uuid
import logging
import math
from typing import Any

from backend.autonomy.pose_estimator import PoseEstimator
from backend.autonomy.mapper import GlobalMapper
from backend.autonomy.planner import AStarPlanner, get_next_command
from backend.autonomy.explorer import FrontierExplorer
from backend.models.schemas import RoverMode, CommandSource, ExplorationData, Point2D, NavigationData

logger = logging.getLogger(__name__)

class AutonomyEngine:
    """
    The main orchestrator for the autonomous exploration loop.
    Ties together pose estimation, mapping, frontier exploration, and path planning.
    """
    def __init__(self, rover_state: Any, gateway: Any, websocket_manager: Any):
        self.rover_state = rover_state
        self.gateway = gateway
        self.websocket_manager = websocket_manager
        
        self.pose_estimator = PoseEstimator()
        self.mapper = GlobalMapper()
        self.planner = AStarPlanner(self.mapper)
        self.explorer = FrontierExplorer(self.mapper)
        
        self._running = False
        self._task = None
        self._current_goal = None
        self._current_path = []
        
        self._last_map_publish_time = 0
        
    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())
            logger.info("Autonomy Engine started.")
            
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Autonomy Engine stopped.")
        
    async def _loop(self):
        while self._running:
            await asyncio.sleep(0.1) # 10 Hz loop
            
            try:
                # 1. ALWAYS Update Map from Telemetry and Broadcast Pose
                if hasattr(self.gateway, "get_current_velocity"):
                    lin, ang = self.gateway.get_current_velocity()
                    self.pose_estimator.update_velocity(lin, ang)
                    
                pose = self.pose_estimator.get_pose()
                self.rover_state.set_pose(pose[0], pose[1], pose[2])
                
                telemetry = self.gateway.get_telemetry()
                if telemetry and telemetry.tof_scan:
                    # Transform ToF using estimated pose
                    self.mapper.update_from_tof(
                        pose, 
                        telemetry.tof_scan.angle_deg, 
                        telemetry.tof_scan.distance_mm
                    )
                    
                # 2. ALWAYS Broadcast Map Update
                now = time.time()
                if now - self._last_map_publish_time >= 0.2: # 5 Hz map updates
                    self._last_map_publish_time = now
                    map_data = self.mapper.get_map_data()
                    await self.websocket_manager.broadcast("map_update", int(now*1000), map_data.model_dump())
                    
                # 3. Check safety and state for Autonomy
                status = self.rover_state.get_status()
                if not status.connected or status.state == "EMERGENCY_STOP" or status.mode != RoverMode.AUTONOMOUS:
                    # Halt exploration logic safely if interrupted
                    self._current_goal = None
                    self._current_path = []
                    continue
                    
                # 4. Explore & Plan
                if not self._current_goal or not self._current_path:
                    frontiers = self.explorer.find_frontiers()
                    if frontiers:
                        rx, ry, _ = pose
                        frontiers.sort(key=lambda f: math.hypot(f[0] - rx, f[1] - ry))
                        
                        self._current_goal = None
                        self._current_path = []
                        
                        for f in frontiers:
                            path = self.planner.plan(pose, f)
                            logger.info(f"Checking frontier {f} -> path len {len(path)}")
                            if path:
                                self._current_goal = Point2D(x=f[0], y=f[1])
                                self._current_path = path
                                logger.info(f"Selected goal {self._current_goal}")
                                break
                        if not self._current_path:
                            logger.info("All frontiers rejected by planner!")
                            
                # 5. Navigate
                cmd_str, lin_mps, ang_rads = get_next_command(pose, self._current_path)
                
                # Command generation
                command_req = {
                    "command_id": f"auto-{uuid.uuid4().hex[:8]}",
                    "timestamp_ms": int(time.time() * 1000),
                    "linear_mps": lin_mps,
                    "angular_rads": ang_rads,
                    "source": CommandSource.AUTONOMY.value
                }
                
                await self.gateway.send_command(command_req)
                
                if self._current_path:
                    target = self._current_path[0]
                    dist = ((target[0]-pose[0])**2 + (target[1]-pose[1])**2)**0.5
                    if dist < 0.2:
                        self._current_path.pop(0)
                
                # 6. Broadcast Exploration & Navigation updates
                if now - self._last_map_publish_time >= 0.0: # reuse timer
                    frontiers = self.explorer.find_frontiers()
                    exp_data = ExplorationData(
                        status="EXPLORING" if self._current_goal else "IDLE",
                        explored_percent=0.0,
                        frontier_count=len(frontiers),
                        current_goal=self._current_goal
                    )
                    await self.websocket_manager.broadcast("exploration_update", int(now*1000), exp_data.model_dump())
                    
                    nav_data = NavigationData(
                        status="NAVIGATING" if self._current_path else "IDLE",
                        goal=self._current_goal,
                        path=[Point2D(x=p[0], y=p[1]) for p in self._current_path]
                    )
                    await self.websocket_manager.broadcast("navigation_update", int(now*1000), nav_data.model_dump())
            
            except Exception as e:
                logger.error(f"Autonomy Engine error: {e}", exc_info=True)
                self.rover_state.emergency_stop()

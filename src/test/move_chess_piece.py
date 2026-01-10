#!/usr/bin/env python3

from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS

"""
This script commands some arbitrary positions to the arm joints:

To get started, open a terminal and type:

    ros2 launch interbotix_xsarm_control xsarm_control.launch robot_model:=wx250s

Then change to this directory and type:

    python3 move_chess_piece.py
"""


class Chess_Robot:

	def __init__(self):
		self.bot = InterbotixManipulatorXS(
			robot_model='wx250s',
			group_name='arm',
			moving_time=2.0,
			accel_time=1.0,
			gripper_name='gripper',
			gripper_pressure=2.5,
		)
		
	def startup(self):

		robot_startup()
		
		
	def shutdown(self):

		self.bot.arm.go_to_sleep_pose()

		robot_shutdown()
		
		
	def robot_move(self, from_x, to_x, from_y, to_y):
		above_z = 0.3
		on_z    = 0.25
		
		bot = self.bot
		
		bot.arm.go_to_home_pose()
		bot.gripper.release()
		
		# grab piece
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.grasp()
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		# move piece to target position
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.release()
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		bot.arm.go_to_home_pose()

	def robot_take(self, from_x, to_x, from_y, to_y):
		above_z = 0.3
		on_z    = 0.25

		trash_x = 0.25
		trash_y = -0.13
		
		bot = self.bot
		
		bot.arm.go_to_home_pose()
		bot.gripper.release()

		# grab enemy piece
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.grasp()
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=trash_x, y=trash_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.release()

		# grab piece
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.grasp()
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		# move piece to target position
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		bot.gripper.release()
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		bot.arm.go_to_home_pose()

	if __name__ == '__robot_move__':
		robot_move()

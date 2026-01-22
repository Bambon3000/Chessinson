#!/usr/bin/env python3

from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS

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


		
	# move a chess piece to a new, empty position
	def robot_move(self, from_x, to_x, from_y, to_y):
		above_z = 0.38 # height where the gripper doesn't interfere with pieces
		
		# height where gripper can grab pieces
		on_z_close = 0.26 # height to grab a piece when close
		on_z_far = 0.30   # height to grab a piece when far
		on_z = on_z_close if from_x < 0.4 else on_z_far # decide whether the piece is close or far
		
		bot = self.bot
		
		# make sure robot is ready for movement
		bot.arm.go_to_sleep_pose() # resting position
		bot.gripper.release()      # open gripper
		
		# --- grab piece ---
		# above origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# on origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		# grab piece
		bot.gripper.grasp()
		# above origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		# --- move piece to target position ---
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# on target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		# release piece
		bot.gripper.release()
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# back to resting position
		bot.arm.go_to_sleep_pose()



	# take the opponent's chess piece by moving a chess piece onto it
	# functionally, the opponent piece is taken first, then the piece is moved
	# onto the now empty field
	def robot_take(self, from_x, to_x, from_y, to_y):
		above_z = 0.38 # height where the gripper doesn't interfere with pieces
		
		# height where gripper can grab pieces
		on_z_close = 0.26 # height to grab a piece when close
		on_z_far = 0.30   # height to grab a piece when far
		on_z = on_z_close if from_x < 0.4 else on_z_far # decide whether the piece is close or far

		# coordinates where the robot drops off taken pieces
		trash_x   = 0.25
		trash_y   = -0.26
		trash_yaw = -0.75
		
		bot = self.bot
		
		# make sure robot is ready for movement
		bot.arm.go_to_sleep_pose() # resting position
		bot.gripper.release()      # open gripper

		# --- grab and dispose of enemy piece ---
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# on target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		# grab piece
		bot.gripper.grasp()
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# dropoff spot
		bot.arm.set_ee_pose_components(x=trash_x, y=trash_y, z=above_z, roll=0.0, pitch=0.0, yaw=-0.75)
		# release piece
		bot.gripper.release()

		# --- grab piece ---
		# above origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# on origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		# grab piece
		bot.gripper.grasp()
		# above origin
		bot.arm.set_ee_pose_components(x=from_x, y=from_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		
		# --- move piece to target position ---
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# on target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=on_z, roll=0.0, pitch=0.0, yaw=0.0)
		# release piece
		bot.gripper.release()
		# above target
		bot.arm.set_ee_pose_components(x=to_x, y=to_y, z=above_z, roll=0.0, pitch=0.0, yaw=0.0)
		# back to resting position
		bot.arm.go_to_sleep_pose()

	if __name__ == '__robot_move__':
		robot_move()

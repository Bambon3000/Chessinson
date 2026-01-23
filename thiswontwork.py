#!/usr/bin/env python3

from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS


class Chess_Robot:
    def __init__(self):
        self.bot = InterbotixManipulatorXS(
            robot_model="wx250s",
            group_name="arm",
            moving_time=2.0,
            accel_time=1.0,
            gripper_name="gripper",
            gripper_pressure=2.5,
        )

        # Cartesian-waypoint tuning (gerade Bahn, aber nicht zu ruckelig)
        self.wp_period = 0.03
        self.wp_moving_time = 0.15
        self.wp_accel_time = 0.075

        # Default EE orientation (anpassen, falls dein Toolframe anders definiert ist)
        self.ee_roll = 0.0
        self.ee_pitch = 0.0
        self.ee_yaw = 0.0

    def startup(self):
        robot_startup()

    def shutdown(self):
        self.bot.arm.go_to_sleep_pose()
        robot_shutdown()

    # ---------- helpers ----------

    @staticmethod
    def _is_success(result) -> bool:
        # Interbotix-Methoden liefern je nach Version bool, tuple(..., success) oder Listen.
        if result is False:
            return False
        if isinstance(result, bool):
            return result
        if isinstance(result, tuple) and len(result) >= 2 and isinstance(result[1], bool):
            return result[1]
        return True  # z.B. theta_list

    def _ik_move_abs(self, *, x, y, z, roll=None, pitch=None, yaw=None, moving_time=None):
        bot = self.bot
        roll = self.ee_roll if roll is None else roll
        pitch = self.ee_pitch if pitch is None else pitch
        yaw = self.ee_yaw if yaw is None else yaw

        guess = None
        if hasattr(bot.arm, "get_joint_commands"):
            guess = bot.arm.get_joint_commands()

        result = bot.arm.set_ee_pose_components(
            x=x, y=y, z=z,
            roll=roll, pitch=pitch, yaw=yaw,
            custom_guess=guess,      # reduziert Joint-Flips :contentReference[oaicite:4]{index=4}
            execute=True,
            blocking=True,
            moving_time=moving_time,
        )
        if not self._is_success(result):
            raise RuntimeError(f"IK move failed for pose x={x:.3f}, y={y:.3f}, z={z:.3f}")

    def _cart_rel(self, *, dx=0.0, dy=0.0, dz=0.0, droll=0.0, dpitch=0.0, dyaw=0.0, moving_time=1.5):
        bot = self.bot
        result = bot.arm.set_ee_cartesian_trajectory(
            x=dx, y=dy, z=dz,
            roll=droll, pitch=dpitch, yaw=dyaw,
            moving_time=moving_time,
            wp_moving_time=self.wp_moving_time,
            wp_accel_time=self.wp_accel_time,
            wp_period=self.wp_period,
        )
        if not self._is_success(result):
            raise RuntimeError(f"Cartesian move failed for dx={dx:.3f}, dy={dy:.3f}, dz={dz:.3f}")

    def _go_ready_pose(self):
        # Doku empfiehlt: aus Sleep erst in Home / y=0 Pose, dann arbeiten :contentReference[oaicite:5]{index=5}
        arm = self.bot.arm
        if hasattr(arm, "go_to_home_pose"):
            arm.go_to_home_pose()
        else:
            arm.go_to_sleep_pose()

    # ---------- chess actions ----------

    def robot_move(self, from_x, to_x, from_y, to_y):
        bot = self.bot

        above_z = 0.38
        on_z_close = 0.26
        on_z_far = 0.30
        on_z = on_z_close if from_x < 0.4 else on_z_far

        self._go_ready_pose()
        bot.gripper.release()

        # 1) über Start (absolute Pose, Kollision unwahrscheinlicher in z=above_z)
        self._ik_move_abs(x=from_x, y=from_y, z=above_z)

        # 2) senkrecht runter (gerade TCP-Bahn)
        self._cart_rel(dz=(on_z - above_z), moving_time=1.0)

        bot.gripper.grasp()

        # 3) senkrecht hoch
        self._cart_rel(dz=(above_z - on_z), moving_time=1.0)

        # 4) horizontal bei sicherer Höhe (gerade TCP-Bahn)
        self._cart_rel(dx=(to_x - from_x), dy=(to_y - from_y), moving_time=1.8)

        # 5) senkrecht runter, ablegen, wieder hoch
        self._cart_rel(dz=(on_z - above_z), moving_time=1.0)
        bot.gripper.release()
        self._cart_rel(dz=(above_z - on_z), moving_time=1.0)

        self.bot.arm.go_to_sleep_pose()

    def robot_take(self, from_x, to_x, from_y, to_y):
        bot = self.bot

        above_z = 0.38
        on_z_close = 0.26
        on_z_far = 0.30
        on_z = on_z_close if from_x < 0.4 else on_z_far

        trash_x = 0.25
        trash_y = -0.26
        trash_yaw = -0.75

        self._go_ready_pose()
        bot.gripper.release()

        # Gegnerfigur: über Ziel -> runter -> greifen -> hoch
        self._ik_move_abs(x=to_x, y=to_y, z=above_z)
        self._cart_rel(dz=(on_z - above_z), moving_time=1.0)
        bot.gripper.grasp()
        self._cart_rel(dz=(above_z - on_z), moving_time=1.0)

        # zur Ablage (absolute Pose auf sicherer Höhe)
        self._ik_move_abs(x=trash_x, y=trash_y, z=above_z, yaw=trash_yaw)
        bot.gripper.release()

        # eigene Figur holen und setzen (wie robot_move)
        self._ik_move_abs(x=from_x, y=from_y, z=above_z)
        self._cart_rel(dz=(on_z - above_z), moving_time=1.0)
        bot.gripper.grasp()
        self._cart_rel(dz=(above_z - on_z), moving_time=1.0)

        self._cart_rel(dx=(to_x - from_x), dy=(to_y - from_y), moving_time=1.8)

        self._cart_rel(dz=(on_z - above_z), moving_time=1.0)
        bot.gripper.release()
        self._cart_rel(dz=(above_z - on_z), moving_time=1.0)

        self.bot.arm.go_to_sleep_pose()


if __name__ == "__main__":
    # Beispiel: nur zum lokalen Test – in deinem Projekt rufst du die Methoden vermutlich aus einem anderen Modul auf.
    r = Chess_Robot()
    r.startup()
    # r.robot_move(...)
    r.shutdown()

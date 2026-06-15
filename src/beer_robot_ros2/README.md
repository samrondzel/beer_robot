# beer_robot_ros2_exact

This package splits `robot_logic_ncnn_optimized.py` into ROS2 nodes without changing the core detection/tracking/target/control/debug logic.

Original logic is preserved in:
- `ncnn_detector.py`
- `tracker.py`
- `target_manager.py`
- `debug.py`
- `config.py`

ROS2 only adds transport between the pieces.

## Topic architecture

```text
camera_node
  publishes /camera/image

detector_node
  subscribes /camera/image
  publishes /detections_raw

tracker_node
  subscribes /detections_raw
  publishes /detections_tracked

target_manager_node
  subscribes /detections_tracked
  publishes /target_state

debug_saver_node
  subscribes /camera/image and /target_state
  saves run_images/latest.jpg and frame_*.jpg
```

## Important

Put `best_ncnn_model/` in the directory from which you launch, for example:

```text
~/Beer_Robot/
  best_ncnn_model/
    model.ncnn.param
    model.ncnn.bin
  beer_robot_ws/
```

or run the launch command from a directory that contains `best_ncnn_model/`.

## Build

```bash
mkdir -p ~/beer_robot_ws/src
cd ~/beer_robot_ws/src
unzip ~/Beer_Robot/beer_robot_ros2_exact.zip

cd ~/beer_robot_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select beer_robot_ros2_exact
source install/setup.bash
```

## Run

Run from the directory that contains `best_ncnn_model`:

```bash
cd ~/Beer_Robot
source /opt/ros/jazzy/setup.bash
source ~/beer_robot_ws/install/setup.bash
ros2 launch beer_robot_ros2_exact beer_robot_pipeline.launch.py
```

## Debug

```bash
ros2 topic list
ros2 topic echo /target_state
ls run_images
```

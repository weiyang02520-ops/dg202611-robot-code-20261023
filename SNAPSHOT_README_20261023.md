# DG202611 机器人代码快照（2026-10-23 21:20）

这是机器人上代码的原样存档，只用来备份和对照，不是整理过的发布版本。

## 来源

- **根目录：** 机器人 `/home/nvidia/ros2_DL` 的当前工作区，包括已提交的文件、未提交的改动和未跟踪的文件，不含被 `.gitignore` 忽略的文件，也不含原来的 `.git`。
  - 原仓库：`liaojingwu20041031/electric-power-inspection-robot`
  - 分支：`robot/pre-vision-backup-20261020`
  - HEAD：`60c0e33a2ce014ecb8ebf4d024ed5f6acdb1bdc3`
  - 打包文件 sha256：`ef8c05feea70608266644d73792f8bb3c169aec8dbd8e2b2794e261d0f8395e7`，共 869 个文件。
- **`ROBOT_UNCOMMITTED_CHANGES_20261023.diff`：** 机器人仓库当时相对 HEAD 的未提交改动（`git diff`，共 14 个文件有变化）。其中：
  - 底盘参数和测试的改动不是视觉这边做的；
  - `ylhb_llm` 里的「相机画面」页是 10-23 加的。
- **`vision_isolated_ws_src/`：** 视觉的两个包 `vision_perception` 和 `vision_perception_interfaces`。机器人实际是从 `/home/nvidia/vision_isolated_ws/src` 运行它们的，那里没有 git；这里放的版本和机器人上的 88 个文件逐字一致（10-23 21:00 比对）。

## 不在这里的东西

- 视觉模型 ONNX：放在交付目录 `DG202611_视觉交付_20261023` 里，没有放进这个仓库。
- 构建产物、日志、数据集、录包。
- 任何密钥。上传前扫过一遍，只找到占位符和测试用的假值。

## 状态

`ARM_READY=NO`。视觉只在一个房间、一个白杯、一瓶水上做过实机复测；底盘的 CAN 通信问题在 10-22 的记录里还没解决。

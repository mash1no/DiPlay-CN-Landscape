# DiPlay CN Landscape · 横屏与连接恢复实验版

CarPlay 界面固定为 `reverseLandscape`，并加固无线会话保活与掉线恢复。当前版本为 **0.2.17-cn.2-landscape.3**，以预发布形式提供。

基于 [serein-morii/DiPlay-CN](https://github.com/serein-morii/DiPlay-CN) 的 v0.2.17-cn.2，上游源码固定到提交 [`48a8330e86926ad69647f0eed0bcb349264b8bec`](https://github.com/serein-morii/DiPlay-CN/tree/48a8330e86926ad69647f0eed0bcb349264b8bec)。保留原作者及贡献者署名，修改遵循 [GPL-3.0](LICENSE)。这是独立实验版本。

## 下载与源码

- [landscape.3 预发布及 APK](https://github.com/mash1no/DiPlay-CN-Landscape/releases/tag/v0.2.17-cn.2-landscape.3)
- [完整对应源码包](DiPlay-CN-landscape.3-corresponding-source.zip)，包含上游源码、修改和 Gradle 构建文件。
- [本次代码补丁](stability.patch)、[构建方法](BUILDING.md)、[构建入口](build_stability.py)。
- [验证记录](verification.json)及 [APK / 源码 SHA-256](SHA256SUMS)。

源码包不包含发布签名私钥或本地认证输入。源码构建和可直接连接 CarPlay 的独立构建分别说明在 [BUILDING.md](BUILDING.md)。根目录的旧 `build_variant.py` 对应 landscape.2；构建 landscape.3 请使用上述新入口。

## 本次修改

具体实现见 [stability.patch](stability.patch)：

- CarPlay Activity 固定反向横屏，应用 ID 为 `com.shihab.diplay.cn.landscape`。
- 为无线 TCP 连接设置保活参数，并对不支持的系统调用保留兼容回退；不以画面静止作为断线判据。
- 活跃会话的前台服务持有 CPU / 无线 Wi-Fi 锁，在停止会话时释放。
- 旧会话失败后进行有限次数恢复，防止多个控制器重复接管；开启自动连接时允许后续退避重试。
- 已选 iPhone 的蓝牙连接事件可请求恢复失败会话，保留防重复触发、用户主动断开和健康会话保护。

## 2026-10-14 实机结果

测试设备为 **HONOR 70 / FNE-AN00，Android 14 / API 34，arm64-v8a**。无线链路使用安卓系统 **5 GHz / WPA2 热点**，蓝牙完成 iAP2 启动。iPhone 型号和 iOS 版本未记录。每项为一次观察，四项初始测试见 [verification.json](verification.json)，蓝牙启动补充结果见 [bluetooth-wake-verification.json](bluetooth-wake-verification.json)。

| 场景 | 本轮结果 | 观察范围 |
| --- | --- | --- |
| 安卓在横竖方向之间转动 | CarPlay 始终横屏，未观察到会话重建；用户确认没有重连 | 要求竖持 / 横持各约 5 秒，重复 3 次；日志窗口 90 秒，系统自动旋转开启 |
| iPhone 锁屏后解锁 | 用户确认没有断连；日志持续有画面帧，未观察到会话重建 | 要求锁屏至少 2 分钟，再解锁；日志窗口 180 秒；允许锁定时使用 CarPlay 已开启 |
| iPhone Wi-Fi 和蓝牙关闭约 10 秒后恢复 | 用户确认自动连上；应用自行重建会话并恢复首帧 | 日志窗口 180 秒；检测到旧会话失败至恢复首帧 10.488 秒，用户开启无线的准确时间未记录 |
| 关闭进程后重新打开 DiPlay | 未按连接按钮，应用自动建立 CarPlay 会话并恢复画面 | 冷启动，日志窗口 90 秒；热点已经开启 |
| 安卓停在桌面，仅操作 iPhone 蓝牙 | DiPlay 自行打开并连接 CarPlay；启动来源为应用自身 | 本机用户已允许显示在其他应用上层；补充记录单独提供 |

**补充验证：蓝牙从安卓桌面自动打开已在本次配置下通过。** 用户明确允许 DiPlay“在其他应用上层显示”后，只在 iPhone 关闭 / 开启蓝牙并连接已配对安卓；用户确认 DiPlay 自行打开并进入 CarPlay。日志显示蓝牙连接事件后由 DiPlay 自身 UID 启动界面并恢复首帧，未出现系统桌面或 ADB 手动启动应用的记录。详见 [蓝牙启动补充验证](bluetooth-wake-verification.json)。此前关闭这项权限时，系统记录了后台启动拦截。

## 使用与已知限制

1. 安装 Release 中的 APK，完成首次 iPhone 蓝牙配对和 CarPlay 授权。
2. 选择目标 iPhone，开启“打开 DiPlay 时连接”，默认模式选“无线”。独立应用 ID 不继承原版私有设置。
3. 对本次 HONOR 测试采用的连接方式：先开启安卓系统热点，设置 5 GHz，在 DiPlay 中选择手动热点并填写同一热点的名称与密码。iPhone 保持蓝牙与 Wi-Fi 开启，关闭个人热点。
4. iPhone 中“允许在锁定时使用 CarPlay”应保持开启。配置入口参考 [Apple CarPlay 设置说明](https://support.apple.com/zh-cn/108415)。

需要从安卓桌面由蓝牙启动时，开启“已选 iPhone 重连蓝牙时自动连接”。本次 HONOR / Android 14 还需用户在系统“特殊应用访问 → 显示在其他应用的上层 → DiPlay”中允许显示权限；该权限允许应用覆盖其他应用界面，应由使用者按需要授权。对应系统规则见 [Android 后台启动说明](https://developer.android.com/guide/components/activities/secure-bal)。本次测试的热点已经开启，不能据此承诺重启后自动开启热点。

本次 HONOR 的 Wi-Fi Direct 建组返回了非预期组，未能连接；上述通过结果来自安卓系统热点。自动开启热点、重启后自动运行、已有会话在后台掉线后的恢复、新手机上的车载音频路由及其他型号均未完成实机验证。短时通过不能证明偶发断线彻底消失，也不能替代长期车载测试。

## 构建检查

[验证记录](verification.json)中记录：签名独立 Release 构建成功，mobile / home / maphost Debug 打包完成，Lint 0 错误，新增 18 项回归测试 0 失败。完整测试并非全绿：shared / common 共 3 项双栈网络测试失败，同样的失败已在未修改的上游源码复现，根因未确定。

APK 已完成签名、版本 / 方向和 16 KiB 原生库 ZIP 对齐检查；本次只在 arm64-v8a 新手机上验证运行。分发时请同时提供许可证和完整对应源码。感谢 DiPlay-CN 及其上游贡献者。

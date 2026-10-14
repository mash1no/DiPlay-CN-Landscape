# DiPlay CN 横屏与连接恢复实验版 · landscape.3

基于 DiPlay-CN v0.2.17-cn.2，固定反向横屏，加入 TCP 保活、活跃会话 CPU / Wi-Fi 锁，以及会话失败后的有限重试与退避恢复。独立应用 ID：`com.shihab.diplay.cn.landscape`，版本代码 112。代码改动见 `stability.patch`，完整对应源码、GPLv3 许可证、构建方法及验证记录公开提供。

## 本次实机通过范围

2026-10-14，在 HONOR 70 / FNE-AN00、Android 14 / API 34、arm64-v8a 上安装本 Release 的 APK，使用安卓系统 5 GHz / WPA2 热点：

- 安卓横竖方向转动：用户确认始终横屏、没有重连；90 秒日志窗口未观察到会话重建。
- iPhone 锁屏至少 2 分钟再解锁：用户确认没有断连；180 秒日志窗口持续有画面帧。
- iPhone Wi-Fi / 蓝牙关闭约 10 秒后恢复：用户确认自动连上；日志显示自动重建会话，检测到失败至恢复首帧 10.488 秒。无线开启的准确时刻未记录，不能把该值作为开启后等待时间。
- 关闭应用进程后重新打开：未按连接按钮，自动建立 CarPlay 会话并恢复画面。

每项只是一轮短时观察；iPhone 型号和 iOS 版本未记录。独立蓝牙唤醒、重启 / 自动开热点、后台恢复、长期偶发掉线及其他型号尚不能算实机通过。本次 HONOR 的 Wi-Fi Direct 建组失败，通过结果仅覆盖安卓系统热点；使用该模式前需开启安卓热点并在 DiPlay 中保存对应配置。

## 构建与下载

签名独立 Release 构建完成；Lint 0 错误，新增 18 项回归测试 0 失败。全套测试有 3 项双栈网络测试失败，未修改上游也复现相同失败，根因未知。详情见附件 `verification.json`。

下载 `DiPlay-cn-v0.2.17-cn.2-landscape.3.apk` 安装；`DiPlay-CN-landscape.3-corresponding-source.zip` 是完整对应源码。校验值见 `SHA256SUMS`。根目录的新 `build_stability.py` 和 `BUILDING.md` 说明源码与独立构建的不同输入。

感谢 [serein-morii/DiPlay-CN](https://github.com/serein-morii/DiPlay-CN) 及其上游贡献者。本实验版按 GPL-3.0 发布，保留原作者署名；本地签名私钥与认证输入不包含在源码包中。

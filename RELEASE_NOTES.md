# DiPlay CN 固定横屏实验版 · landscape.2

基于 DiPlay-CN v0.2.17-cn.2，将 CarPlay Activity 方向从 fullSensor 改为 reverseLandscape，使用独立应用 ID 与本地签名。安装包、构建脚本及对应源码公开提供，许可证为 GPLv3。

下载 APK 后按仓库 README 设置目标 iPhone 和无线自动连接。源码包包含完整上游应用源码快照与本次修改脚本；签名私钥不公开。

已完成：签名、ZIP、Manifest、413 个保留条目比较、原生库对齐检查及 Android 7.1.2 安装。未完成：最终方向实机连续转动、iPhone 锁屏偶发断连、完整无线掉线恢复和其他设备兼容性测试。本版本未修改无线传输代码，不应视为熄屏断连已经修复。

校验值见 SHA256SUMS；范围与验证记录见 verification.json。感谢 serein-morii/DiPlay-CN 及其上游贡献者。

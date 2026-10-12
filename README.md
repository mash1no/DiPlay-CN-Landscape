# DiPlay CN Landscape · 固定横屏实验版

给 Android 端 DiPlay 的 CarPlay 界面固定一个横屏方向。默认使用 `reverseLandscape`，避免随手机传感器在横竖屏之间切换。

本项目基于 [serein-morii/DiPlay-CN](https://github.com/serein-morii/DiPlay-CN) 的 **v0.2.17-cn.2**，是独立的 Manifest 重打包工具和实验性发布。原项目作者及贡献者保留其署名和权利；本项目遵循 **GPL-3.0**，不是原作者官方版本。

## 下载与源码

- 在本仓库 **Releases** 下载 `DiPlay-cn-v0.2.17-cn.2-landscape.2.apk`。
- 本仓库 `build_variant.py` 公开本地修改的完整构建脚本。
- 同一 Release 提供 `DiPlay-CN-landscape.2-corresponding-source.zip`，包含固定版本的上游应用源码、许可证、本构建脚本、源代码方向补丁和说明。
- 上游源码固定到提交 [`48a8330e86926ad69647f0eed0bcb349264b8bec`](https://github.com/serein-morii/DiPlay-CN/tree/48a8330e86926ad69647f0eed0bcb349264b8bec)。源码包不包含本项目发布签名私钥；构建者使用自己的签名。

## 修改范围

| 项目 | 上游 APK | 本实验版 |
| --- | --- | --- |
| CarPlay Activity 方向 | `fullSensor` / 10 | `reverseLandscape` / 8 |
| 应用 ID | `com.shihab.diplay.cn` | `com.shihab.diplay.cn.landscape` |
| 启动器名称 | DiPlay | DiPlay 横屏修正版 |
| 版本名 | `0.2.17-cn.2` | `0.2.17-cn.2-landscape.2` |

重打包保留 **413 个非签名条目**的原始内容，包括 DEX、资源、原生库和原有运行时资源。没有修改蓝牙协议、Wi-Fi Direct、音频或认证代码。仅修改二进制 Manifest 并重新签名；没有重新编译上游 Android 应用。

不同横屏方向可用构建脚本的 `--orientation landscape` 参数选择。公开下载的 APK 固定为 `reverseLandscape`。

## 安装与连接

1. 下载 APK，在安卓设备上确认安装；保留原版安装和数据可以便于回退。
2. 两个 DiPlay 版本不要同时自动连接同一 iPhone。先关闭原版的自动连接并停止原版，再使用“DiPlay 横屏修正版”。
3. 在修正版选择目标 iPhone，设置无线连接方式并完成首次蓝牙和 CarPlay 授权。安卓无 SIM 卡也可建立 CarPlay 链路，联网内容由 iPhone 及所选网络提供。
4. 按需开启“打开 DiPlay 时连接”和“已选 iPhone 重连蓝牙时自动连接”，默认模式选择“无线”。首次安装的独立应用 ID 不会自动继承原版私有设置。
5. 使用 Wi-Fi Direct 时避免同时把安卓连到同一 iPhone 的个人热点。具体步骤参考[上游连接说明](https://github.com/serein-morii/DiPlay-CN/blob/v0.2.17-cn.2/docs/CONNECTION_SETUP.md)。

需覆盖更新时使用相同的签名；本项目签名与官方签名不同，因此使用独立应用 ID。卸载会删除该应用的设置。

## 验证与已知问题

公开 APK 已完成 JAR 签名校验、ZIP 完整性、Manifest 方向校验、保留条目内容比较及原生库 4096 字节对齐检查，并在 Android 7.1.2 设备上安装，ADB 返回 `Success`。记录见 [verification.json](verification.json)，下载校验值见 [SHA256SUMS](SHA256SUMS)。

**以下尚未完成验证，不能视为已修复：**

- 最终 `reverseLandscape` 版本在实机连续转动时是否始终不重连。
- iPhone 熄屏后偶发断连，以及长时间无线运行的稳定性。
- Wi-Fi 和蓝牙完全断开后，从后台自动恢复会话。
- 其他安卓型号、Android 版本、音频设备和车载环境。

本版本的固定方向用于移除屏幕旋转这一触发因素；它不是无线链路稳定性补丁。应用保活、安卓 Wi-Fi 休眠策略和系统电池优化属于设备配置，本 APK 不会自动替用户修改它们。未执行上游 Gradle 全套 CI；本次验证针对重打包流程，不等同于上游源码重新编译通过。

## 复现构建

需要 Python 3.9+、JDK 17 和 Android SDK 的 `aapt2`。脚本只使用 Python 标准库。

```sh
python3 build_variant.py --download --java-home /path/to/jdk-17 --aapt2 /path/to/android-sdk/build-tools/aapt2
```

也可以使用已经下载的官方 APK：

```sh
python3 build_variant.py --input /path/to/DiPlay-cn-v0.2.17-cn.2.apk --java-home /path/to/jdk-17 --aapt2 /path/to/aapt2
```

脚本强制核对官方 APK 的 SHA-256，然后修改 Manifest、使用本地签名并完成最小充分检查。输出在 `dist/`；本地签名文件和随机口令也在此目录，该目录被 Git 忽略。请自行保管签名以便后续更新。可以通过 `DIPLAY_SIGNING_PASSWORD` 环境变量提供自己的签名口令；不要提交该变量或私钥。

公开 APK 与重建 APK 因签名密钥及签名时间可能有不同 SHA-256；可复现的是修改范围和保留条目的内容，不能承诺逐字节一致。

源代码方向补丁见 `manifest-orientation.patch`。直接编译上游应用需按上游说明配置 SDK 和运行时资源；普通源码构建不自动提供独立 CarPlay 认证身份。不要把个人认证材料或签名私钥提交到仓库。

## 许可证与致谢

本项目和修改遵循 [GNU GPL v3](LICENSE)。感谢 [serein-morii/DiPlay-CN](https://github.com/serein-morii/DiPlay-CN) 及其上游贡献者。分发二进制时请保留许可证、修改说明和相应源码获取途径。

# 构建 landscape.3

完整应用源码位于 `DiPlay-CN-landscape.3-corresponding-source.zip`。解压后的根目录为 `DiPlay-CN-Landscape/`，其中已经包含 stability.patch 对应的修改，不要再次应用补丁。

本次使用 JDK 25、Gradle 9.5.0、Android SDK 37 和 NDK 28.2.13676358 构建。源码的 Gradle Wrapper 和 JVM 配置固定了相应版本；SDK、NDK 及 Gradle 依赖需要自行安装或下载。打包验证范围见 [verification.json](verification.json)。

## 普通源码构建

需要 Python 3.9+。下面的入口校验源码包的固定 SHA-256，解压到新目录、设置 SDK 路径并执行源码内的 Gradle Wrapper：

```sh
python3 build_stability.py \
  --java-home /path/to/jdk-25 \
  --android-sdk /path/to/android-sdk
```

默认目录为 `build-landscape3/DiPlay-CN-Landscape`，执行 `:mobile:assembleDebug`。普通源码构建不包含 CarPlay 认证身份，适合开发和源码检查，不能据此承诺可以独立连接 CarPlay。

构建入口的 `--dry-run` 仅打印计划，不解压、不运行构建。发布 APK 的历史构建已经完成；此入口只进行了语法和计划输出检查，没有另行重复整个构建。

## 带显式本地认证输入的构建

自行提供运行时认证目录，其中必须存在：

```text
local-auth/
  offline-mfi/
    identity.pk8
    certificate.p7b
```

认证输入通过源码中的 `DIPLAY_AUTH_ASSETS_DIR` 接入，不会自动从其他目录导入。不要把这些本地输入或个人签名密钥提交到仓库。

```sh
python3 build_stability.py \
  --java-home /path/to/jdk-25 \
  --android-sdk /path/to/android-sdk \
  --task standalone-debug \
  --auth-assets /path/to/local-auth
```

Release 需要自己的签名文件，并事先在环境中设置 `ANDROID_KEYSTORE_PASSWORD`、`ANDROID_KEY_ALIAS`、`ANDROID_KEY_PASSWORD`；脚本不会输出它们。

```sh
python3 build_stability.py \
  --java-home /path/to/jdk-25 \
  --android-sdk /path/to/android-sdk \
  --task standalone-release \
  --auth-assets /path/to/local-auth \
  --keystore /path/to/your-keystore.p12
```

任务分别为 `:mobile:assembleStandaloneDebug` / `:mobile:assembleStandaloneRelease`，APK 输出在解压后源码的 `mobile/build/outputs/apk/` 中。版本、签名和设备是否接受安装应由构建者检查；使用自己的签名不能直接覆盖安装本项目发布签名的版本。

## 检查范围

源码包含新增回归测试和原有测试。常规检查入口为：

```sh
./gradlew :shared:testDebugUnitTest :common:testDebugUnitTest :home:testDebugUnitTest \
  :mobile:lintDebug :home:lintDebug :maphost:lintDebug \
  :mobile:assembleDebug :home:assembleDebug :maphost:assembleDebug
```

上述完整检查在本次环境仍有 3 项双栈网络测试失败，未修改的上游也复现相同失败。不能将该记录写成全部 CI 通过；详情见 [verification.json](verification.json)。

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
import textwrap

from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from webapp.app import models  # noqa: E402
from builder.config import get_settings
from builder.database import SessionLocal

settings = get_settings()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def ensure_commandline_tools() -> None:
    target = Path(settings.android_sdk_root) / "cmdline-tools" / "latest" / "bin" / "sdkmanager"
    if target.exists():
        return
    download_to = Path("/tmp/cmdline-tools.zip")
    download_to.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(settings.android_cmdline_url, download_to)
    extract_base = Path(settings.android_sdk_root) / "cmdline-tools"
    extract_base.mkdir(parents=True, exist_ok=True)
    subprocess.run(["unzip", "-qo", str(download_to), "-d", str(extract_base)], check=True)
    extracted = extract_base / "cmdline-tools"
    if extracted.exists():
        (extract_base / "latest").mkdir(parents=True, exist_ok=True)
        for item in extracted.iterdir():
            shutil.move(str(item), str(extract_base / "latest" / item.name))
        extracted.rmdir()
    download_to.unlink(missing_ok=True)


def ensure_android_packages() -> None:
    ensure_commandline_tools()
    sdkmanager = Path(settings.android_sdk_root) / "cmdline-tools" / "latest" / "bin" / "sdkmanager"
    cmd = [str(sdkmanager), f"--sdk_root={settings.android_sdk_root}"] + settings.android_packages
    subprocess.run(cmd, input=b"y\n" * 10, check=True)


def ensure_gradle() -> str:
    gradle_base = Path(settings.gradle_home)
    gradle_dir = gradle_base / f"gradle-{settings.gradle_version}"
    gradle_bin = gradle_dir / "bin" / "gradle"
    if gradle_bin.exists():
        return str(gradle_bin)
    gradle_base.mkdir(parents=True, exist_ok=True)
    download_url = f"https://services.gradle.org/distributions/gradle-{settings.gradle_version}-bin.zip"
    archive = Path("/tmp/gradle.zip")
    urllib.request.urlretrieve(download_url, archive)
    subprocess.run(["unzip", "-qo", str(archive), "-d", str(gradle_base)], check=True)
    archive.unlink(missing_ok=True)
    return str(gradle_bin)


def bootstrap_toolchain() -> None:
    print("Ensuring Gradle distribution...")
    ensure_gradle()
    print("Ensuring Android SDK command-line tools and packages...")
    ensure_android_packages()


def create_android_project(base_dir: Path, app_project: models.AppProject, keystore: models.Keystore, log_lines: list[str]) -> None:
    package_path = Path("app/src/main/java") / Path(app_project.package_name.replace(".", "/"))
    manifest = textwrap.dedent(
        f"""
        <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{app_project.package_name}">
            <uses-permission android:name="android.permission.INTERNET" />
            <application
                android:label="{app_project.name}"
                android:allowBackup="true"
                android:icon="@android:drawable/sym_def_app_icon"
                android:supportsRtl="true">
                <activity
                    android:name=".MainActivity"
                    android:exported="true"
                    android:theme="@style/Theme.AppCompat.Light.NoActionBar">
                    <intent-filter>
                        <action android:name="android.intent.action.MAIN" />
                        <category android:name="android.intent.category.LAUNCHER" />
                    </intent-filter>
                </activity>
            </application>
        </manifest>
        """
    ).strip()
    write_file(base_dir / "app/src/main/AndroidManifest.xml", manifest)

    main_activity = textwrap.dedent(
        f"""
        package {app_project.package_name}

        import android.os.Bundle
        import android.webkit.WebView
        import android.webkit.WebViewClient
        import androidx.appcompat.app.AppCompatActivity

        class MainActivity : AppCompatActivity() {{
            override fun onCreate(savedInstanceState: Bundle?) {{
                super.onCreate(savedInstanceState)
                val webView = WebView(this)
                webView.settings.javaScriptEnabled = true
                webView.webViewClient = WebViewClient()
                webView.loadUrl("{app_project.url}")
                setContentView(webView)
            }}
        }}
        """
    ).strip()
    write_file(base_dir / package_path / "MainActivity.kt", main_activity)

    strings = textwrap.dedent(
        f"""
        <resources>
            <string name="app_name">{app_project.name}</string>
        </resources>
        """
    ).strip()
    write_file(base_dir / "app/src/main/res/values/strings.xml", strings)

    styles = textwrap.dedent(
        """
        <resources>
            <style name="Theme.AppCompat.Light.NoActionBar" parent="Theme.AppCompat.Light.NoActionBar" />
        </resources>
        """
    ).strip()
    write_file(base_dir / "app/src/main/res/values/themes.xml", styles)

    colors = """<resources><color name=\"placeholder\">#6200EE</color></resources>"""
    write_file(base_dir / "app/src/main/res/values/colors.xml", colors)

    settings_gradle = textwrap.dedent(
        f"""
        rootProject.name = "webview-{app_project.id}"
        include(":app")
        """
    ).strip()
    write_file(base_dir / "settings.gradle", settings_gradle)

    gradle_root = textwrap.dedent(
        """
        buildscript {
            repositories {
                google()
                mavenCentral()
            }
            dependencies {
                classpath 'com.android.tools.build:gradle:8.1.4'
                classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.10'
            }
        }

        allprojects {
            repositories {
                google()
                mavenCentral()
            }
        }

        task clean(type: Delete) {
            delete rootProject.buildDir
        }
        """
    ).strip()
    write_file(base_dir / "build.gradle", gradle_root)

    module_build = textwrap.dedent(
        f"""
        apply plugin: 'com.android.application'
        apply plugin: 'org.jetbrains.kotlin.android'

        android {{
            namespace "{app_project.package_name}"
            compileSdkVersion {app_project.target_sdk}

            defaultConfig {{
                applicationId "{app_project.package_name}"
                minSdkVersion {app_project.min_sdk}
                targetSdkVersion {app_project.target_sdk}
                versionCode {app_project.version_code}
                versionName "{app_project.version_name}"
            }}

            signingConfigs {{
                release {{
                    storeFile file('{keystore.keystore_path}')
                    storePassword '{keystore.store_password}'
                    keyAlias '{keystore.alias}'
                    keyPassword '{keystore.key_password}'
                }}
            }}

            buildTypes {{
                debug {{
                    signingConfig signingConfigs.release
                }}
                release {{
                    signingConfig signingConfigs.release
                    minifyEnabled false
                    shrinkResources false
                }}
            }}
        }}

        dependencies {{
            implementation 'androidx.core:core-ktx:1.12.0'
            implementation 'androidx.appcompat:appcompat:1.6.1'
            implementation 'androidx.activity:activity-ktx:1.8.2'
            implementation 'androidx.webkit:webkit:1.9.0'
        }}
        """
    ).strip()
    write_file(base_dir / "app/build.gradle", module_build)

    gradle_props = textwrap.dedent(
        """
        android.useAndroidX=true
        android.enableJetifier=true
        org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
        """
    ).strip()
    write_file(base_dir / "gradle.properties", gradle_props)

    local_props = textwrap.dedent(
        f"""
        sdk.dir={settings.android_sdk_root}
        """
    ).strip()
    write_file(base_dir / "local.properties", local_props)

    log_lines.append(f"Gradle project generated in {base_dir}")


def run_gradle_build(base_dir: Path, log_lines: list[str]) -> None:
    gradle_bin = ensure_gradle()
    env = os.environ.copy()
    env.setdefault("ANDROID_SDK_ROOT", settings.android_sdk_root)
    env["PATH"] = f"{Path(gradle_bin).parent}:{env.get('PATH', '')}"
    commands = [
        [gradle_bin, "wrapper"],
        ["./gradlew", "assembleRelease", "bundleRelease", "-x", "lint"],
    ]
    for cmd in commands:
        proc = subprocess.run(
            cmd,
            cwd=base_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        log_lines.append(proc.stdout)
        if proc.returncode != 0:
            log_lines.append(proc.stderr)
            raise RuntimeError(f"Command {' '.join(cmd)} failed with code {proc.returncode}")


def collect_artifacts(base_dir: Path, job: models.BuildJob, log_lines: list[str]) -> tuple[str, str]:
    apk_src = base_dir / "app/build/outputs/apk/release/app-release.apk"
    aab_src = base_dir / "app/build/outputs/bundle/release/app-release.aab"
    artifacts_dir = Path(settings.artifact_dir) / str(job.app_project_id) / str(job.id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    if not apk_src.exists() or not aab_src.exists():
        raise FileNotFoundError("Expected Gradle outputs were not produced")
    apk_dest = artifacts_dir / "app.apk"
    aab_dest = artifacts_dir / "app.aab"
    shutil.copy(apk_src, apk_dest)
    shutil.copy(aab_src, aab_dest)
    log_lines.append(f"Artifacts stored to {artifacts_dir}")
    return str(apk_dest), str(aab_dest)


def process_build(db: Session, job: models.BuildJob):
    log_lines: list[str] = []
    job.status = models.BuildStatus.running.value
    db.commit()
    db.refresh(job)

    app_project = db.get(models.AppProject, job.app_project_id)
    if not app_project:
        raise RuntimeError("Associated AppProject not found")
    keystore = app_project.keystore
    base_dir = Path(settings.build_work_dir) / str(job.id)
    base_dir.mkdir(parents=True, exist_ok=True)
    log_lines.append(f"Working directory: {base_dir}")

    create_android_project(base_dir, app_project, keystore, log_lines)
    run_gradle_build(base_dir, log_lines)
    apk_path, aab_path = collect_artifacts(base_dir, job, log_lines)

    job.status = models.BuildStatus.success.value
    job.apk_path = apk_path
    job.aab_path = aab_path
    job.log = "\n".join(log_lines)
    job.finished_at = datetime.utcnow()
    db.commit()


def main():
    bootstrap_toolchain()
    while True:
        with SessionLocal() as db:
            job = (
                db.query(models.BuildJob)
                .filter(models.BuildJob.status == models.BuildStatus.pending.value)
                .order_by(models.BuildJob.created_at.asc())
                .first()
            )
            if not job:
                time.sleep(5)
                continue
            try:
                process_build(db, job)
            except Exception as exc:  # noqa: BLE001
                job.status = models.BuildStatus.failed.value
                job.log = str(exc)
                job.finished_at = datetime.utcnow()
                db.commit()
        time.sleep(1)


if __name__ == "__main__":
    main()

import os
import sys
import time
from datetime import datetime

from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from webapp.app import models  # noqa: E402
from builder.config import get_settings
from builder.database import SessionLocal

settings = get_settings()


def simulate_build(db: Session, job: models.BuildJob):
    job.status = models.BuildStatus.running.value
    db.commit()
    db.refresh(job)

    app_project = db.get(models.AppProject, job.app_project_id)
    keystore = app_project.keystore
    log_lines = []
    base_dir = f"/data/builds/{job.id}"
    os.makedirs(base_dir, exist_ok=True)
    log_lines.append(f"Working directory: {base_dir}")
    os.makedirs(settings.artifact_dir, exist_ok=True)

    manifest_path = os.path.join(base_dir, "AndroidManifest.xml")
    with open(manifest_path, "w") as f:
        f.write("<!-- TODO: real manifest -->\n")
        f.write(f"<!-- Package: {app_project.package_name} URL: {app_project.url} -->\n")
    log_lines.append("Generated AndroidManifest.xml")

    main_activity = os.path.join(base_dir, "MainActivity.kt")
    with open(main_activity, "w") as f:
        f.write("// TODO: real WebView activity\n")
        f.write(f"// Loads {app_project.url}\n")
    log_lines.append("Generated MainActivity.kt")

    artifacts_dir = os.path.join(settings.artifact_dir, str(app_project.id), str(job.id))
    os.makedirs(artifacts_dir, exist_ok=True)
    apk_path = os.path.join(artifacts_dir, "app.apk")
    aab_path = os.path.join(artifacts_dir, "app.aab")
    with open(apk_path, "w") as f:
        f.write(f"Dummy APK for build {job.id}\n")
        f.write("TODO: replace with Gradle output\n")
    with open(aab_path, "w") as f:
        f.write(f"Dummy AAB for build {job.id}\n")
        f.write("TODO: replace with Gradle bundle\n")
    log_lines.append("Simulated APK/AAB artifacts created")

    log_lines.append(
        f"Signing would use keystore {keystore.keystore_path} with alias {keystore.alias}"
    )

    job.status = models.BuildStatus.success.value
    job.apk_path = apk_path
    job.aab_path = aab_path
    job.log = "\n".join(log_lines)
    job.finished_at = datetime.utcnow()
    db.commit()


def main():
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
                simulate_build(db, job)
            except Exception as exc:  # noqa: BLE001
                job.status = models.BuildStatus.failed.value
                job.log = str(exc)
                job.finished_at = datetime.utcnow()
                db.commit()
        time.sleep(1)


if __name__ == "__main__":
    main()

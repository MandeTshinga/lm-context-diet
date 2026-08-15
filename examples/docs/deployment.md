# Deployment

> The three rules that apply **before** you deploy live in [`../CLAUDE.after.md`](../CLAUDE.after.md):
> a rollback does not roll back migrations, always check `make deploy-status` afterwards,
> and migrations run as a dedicated task rather than at container start.
> This file holds the reasoning.

## The pipeline

Deploys go through GitHub Actions to ECS. The pipeline builds an image, runs tests, pushes to ECR, then updates the service.

## The two-task migration race

The original pipeline ran migrations as part of the container start command. This broke the first time we scaled to two tasks, because both containers ran the migration simultaneously and one of them failed on a duplicate index.

We moved migrations to a separate one-off task that runs before the service update.

## Rollbacks

`make rollback` points the service at the previous task definition. It does not touch the database, which is why every migration has to be backwards compatible with the previous release.

## Blue-green, abandoned

We tried blue-green deployment and abandoned it, because the Celery workers hold long-running tasks and draining them took longer than the deployment window allowed.

## The S3 lifecycle incident

Static files go to S3 through `collectstatic` in the build step, not at runtime. The bucket had a lifecycle rule deleting objects older than 90 days, which once deleted the static files of a release we had pinned for a customer. The rule now excludes the `static/` prefix.

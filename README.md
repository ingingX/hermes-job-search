# Hermes Job Search

Run a private job-search workspace with Hermes in Docker on Ubuntu 26.04. This repository includes the job-search workflows, portal tools, CV templates, and container definition. Users do not need to clone the upstream project or install Hermes, Bun, or TeX on the host.

## Start

Install Git, Docker Engine, and the Docker Compose plugin. Make sure your user can run `docker compose version` and access the Docker daemon. Then:

```sh
git clone https://github.com/OWNER/hermes-job-search.git
cd hermes-job-search
./run.sh
```

Replace `OWNER` with the GitHub account that hosts this project.

The first run copies the bundled workflow into ignored `work/`, builds the container image, and prompts for a separate Codex OAuth login and model choice inside the container. Later runs use the same private workspace and login; the image build reuses cached layers. The script refuses to overwrite an existing, uninitialized workspace. To renew the login, run `docker compose run --rm hermes auth add openai-codex --type oauth` after `./run.sh` has created the directories.

In Hermes, use `/hermes-job-search` and ask it to set up your profile, search for jobs, rank results, evaluate a pasted job description or URL, draft an application, or record a confirmed outcome. Review every draft before use. An application is never submitted automatically.

Exit Hermes to stop the interactive container. `docker compose down` removes project containers and the network; it keeps `work/` and `.runtime/hermes/`. Rebuild after updating the repository by running `./run.sh` again. The private workspace is a separate copy, so workflow changes are not silently copied over user edits.

## Files and privacy

`work/` holds your profile, searches, tracker, drafts, and application history. `.runtime/hermes/` holds this project's Hermes configuration and authentication. Both are ignored by Git. Only these two directories are mounted in the container. No host Hermes or Codex directory, Docker socket, or host port is mounted.

The initial workspace contains placeholder profile templates. Add your real details only inside `work/`, never to the tracked source templates. Before publishing changes, inspect the staged file list.

## Maintenance

The workflow files under `.claude/` and portal definitions under `.agents/skills/` come from [Mads Lorentzen's ai-job-search](https://github.com/MadsLorentzen/ai-job-search), pinned at `e16acee`. The Hermes skill at `.hermes/skills/hermes-job-search/` points to those workflows. Keep the upstream license and attribution when redistributing this derivative. No upstream Git remote is needed to run the project.

The original upstream setup guide, `SETUP.md`, describes its Claude Code workflow; use this README for the Hermes container.

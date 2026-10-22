#!/bin/sh
set -eu

cd "$(dirname "$0")"
command -v docker >/dev/null 2>&1 || { echo 'Docker is required.' >&2; exit 1; }
docker compose version >/dev/null

mkdir -p .runtime/hermes
chmod 700 .runtime/hermes

if [ ! -e work/.hermes-workspace ]; then
    if [ -e work ]; then
        echo 'work exists but is not initialized; refusing to overwrite it.' >&2
        exit 1
    fi
    staging=".work-$$"
    bundle=".work-$$.tar"
    mkdir "$staging"
    trap 'rm -rf "$staging"; rm -f "$bundle"' EXIT HUP INT TERM
    if [ -d .agents/skills ]; then
        agents=.agents
    else
        agents=portal-skills
    fi
    tar -cf "$bundle" AGENTS.md CLAUDE.md LICENSE .gitignore .claude \
        .hermes cv cover_letters documents templates tools job_scraper \
        salary_lookup.py upskill company_research "$agents"
    tar -xf "$bundle" -C "$staging"
    if [ "$agents" = portal-skills ]; then
        mv "$staging/portal-skills" "$staging/.agents"
    fi
    touch "$staging/.hermes-workspace"
    mv "$staging" work
    rm -f "$bundle"
    trap - EXIT HUP INT TERM
fi

export HJS_UID="$(id -u)" HJS_GID="$(id -g)"
docker compose build hermes
if [ ! -f .runtime/hermes/auth.json ]; then
    docker compose run --rm hermes auth add openai-codex --type oauth
    docker compose run --rm hermes model
fi
docker compose run --rm hermes

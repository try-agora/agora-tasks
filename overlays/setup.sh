#!/usr/bin/env bash
# Runs only inside the disposable task container, before agent execution.
set -euo pipefail
phase="${1:?phase required}"
arm="${2:?arm required}"
export DEBIAN_FRONTEND=noninteractive
locks=/opt/benchmark-overlay/locks

case "$phase" in
  common)
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends ripgrep make g++ xz-utils
    case "$(uname -m)" in
      aarch64) arch=arm64; digest=08bfbf538bad0e8cbb0269f0173cca28d705874a67a22f60b57d99dc99e30050 ;;
      x86_64) arch=x64; digest=69b09dba5c8dcb05c4e4273a4340db1005abeafe3927efda2bc5b249e80437ec ;;
      *) echo 'Unsupported architecture' >&2; exit 1 ;;
    esac
    curl -fSL --retry 2 "https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-$arch.tar.xz" -o /tmp/overlay-node.tar.xz
    echo "$digest  /tmp/overlay-node.tar.xz" | sha256sum --check
    tar -xJf /tmp/overlay-node.tar.xz -C /usr/local --strip-components=1
    sha256sum "$locks/common/package-lock.json"
    npm ci --prefix "$locks/common" --no-audit --no-fund
    ln -s "$locks/common/node_modules/.bin/codex" /usr/local/bin/codex
    node --version
    codex --version
    python --version
    dpkg-query -W
    ;;
  install)
    case "$arm" in
      baseline) rg --version ;;
      codegraph)
        sha256sum "$locks/codegraph/package-lock.json"
        npm ci --prefix "$locks/codegraph" --no-audit --no-fund
        ln -s "$locks/codegraph/node_modules/.bin/codegraph" /usr/local/bin/codegraph
        codegraph --version
        npm list --prefix "$locks/codegraph" --all --json
        ;;
      gitnexus)
        sha256sum "$locks/gitnexus/package-lock.json"
        GITNEXUS_SKIP_OPTIONAL_GRAMMARS=1 ONNXRUNTIME_NODE_INSTALL=skip npm ci --prefix "$locks/gitnexus" --no-audit --no-fund
        ln -s "$locks/gitnexus/node_modules/.bin/gitnexus" /usr/local/bin/gitnexus
        gitnexus --version
        npm list --prefix "$locks/gitnexus" --all --json
        ;;
      graphify)
        python -m venv /opt/graphify
        sha256sum "$locks/graphify.txt"
        /opt/graphify/bin/pip install --only-binary=:all: --require-hashes -r "$locks/graphify.txt"
        ln -s /opt/graphify/bin/graphify /usr/local/bin/graphify
        ln -s /opt/graphify/bin/graphify-mcp /usr/local/bin/graphify-mcp
        graphify --version
        /opt/graphify/bin/pip freeze
        ;;
      codebase-memory-mcp)
        case "$(uname -m)" in
          aarch64) arch=arm64; digest=5697d986d9716c913163b4bff7b3a294287f3b843e993bc1ff71e78dcdc21781 ;;
          x86_64) arch=amd64; digest=6eef49652bc0c7820f43114125044d40bf7f4d97c11b2592f6b0f6a307702325 ;;
          *) echo 'Unsupported architecture' >&2; exit 1 ;;
        esac
        curl -fSL --retry 2 "https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.10.8/codebase-memory-mcp-linux-$arch-portable.tar.gz" -o /tmp/overlay-cbm.tar.gz
        echo "$digest  /tmp/overlay-cbm.tar.gz" | sha256sum --check
        tar -xzf /tmp/overlay-cbm.tar.gz -C /usr/local/bin
        codebase-memory-mcp --version
        ;;
      *) echo 'Unknown overlay' >&2; exit 1 ;;
    esac
    ;;
  index)
    test "$PWD" = /app
    git init -q
    git add -A
    git -c user.name=benchmark -c user.email=benchmark@example.invalid commit -qm 'Frozen task input'
    case "$arm" in
      baseline) echo 'No graph; baseline uses shell search.' ;;
      codegraph) CODEGRAPH_TELEMETRY=0 CODEGRAPH_NO_DAEMON=1 codegraph init /app ;;
      gitnexus)
        GITNEXUS_LBUG_EXTENSION_INSTALL=auto gitnexus analyze /app --index-only --workers 1
        python -c 'import json,sys; m=json.load(open("/app/.gitnexus/meta.json")); print(json.dumps(m["capabilities"])); sys.exit(0 if m["capabilities"]["fts"]["status"] == "available" else "GitNexus FTS unavailable; refusing a degraded arm")'
        ;;
      graphify) GRAPHIFY_QUERY_LOG_DISABLE=1 graphify update /app --no-cluster ;;
      # This engine rejects /app as a broad root. All dataset code is under src/.
      codebase-memory-mcp) codebase-memory-mcp cli index_repository --repo-path /app/src --name app --mode fast ;;
      *) echo 'Unknown overlay' >&2; exit 1 ;;
    esac
    # Initialization may add tool data, but must not alter the supplied workspace.
    git diff --exit-code HEAD
    git status --short
    ;;
  *) echo 'Unknown setup phase' >&2; exit 1 ;;
esac

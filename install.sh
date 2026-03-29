#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/nexurlabs/rica.git"
DEFAULT_DIR="${HOME}/.nexurlabs/rica"
INSTALL_DIR="${RICA_DIR:-$DEFAULT_DIR}"

have() { command -v "$1" >/dev/null 2>&1; }
log() { printf '\n==> %s\n' "$1" >&2; }
warn() { printf '\n[warn] %s\n' "$1" >&2; }

ensure_sudo() {
  if have sudo; then
    sudo "$@"
  else
    "$@"
  fi
}

install_linux_pkgs() {
  if have apt-get; then
    ensure_sudo apt-get update
    ensure_sudo apt-get install -y "$@"
  elif have dnf; then
    ensure_sudo dnf install -y "$@"
  elif have pacman; then
    ensure_sudo pacman -Sy --noconfirm "$@"
  else
    warn "No supported package manager found. Please install manually: $*"
    return 1
  fi
}

ensure_git() {
  if have git; then return 0; fi
  log "Installing git"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    if ! have brew; then
      warn "Homebrew is required to auto-install git on macOS. Install brew first: https://brew.sh"
      exit 1
    fi
    brew install git
  else
    install_linux_pkgs git
  fi
}

ensure_python() {
  if ! have python3; then
    log "Installing Python 3"
    if [[ "$(uname -s)" == "Darwin" ]]; then
      if ! have brew; then
        warn "Homebrew is required to auto-install Python on macOS. Install brew first: https://brew.sh"
        exit 1
      fi
      brew install python
    else
      install_linux_pkgs python3 python3-pip python3-venv
    fi
    return 0
  fi

  if [[ "$(uname -s)" != "Darwin" ]] && have apt-get; then
    # Debian/Ubuntu often have python3 but not venv support installed.
    python3 -m venv .venv-check >/dev/null 2>&1 || install_linux_pkgs python3-venv python3-pip
    rm -rf .venv-check >/dev/null 2>&1 || true
  fi
}

ensure_node() {
  if have node && have npm; then return 0; fi
  log "Installing Node.js + npm"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    if ! have brew; then
      warn "Homebrew is required to auto-install Node.js on macOS. Install brew first: https://brew.sh"
      exit 1
    fi
    brew install node
  else
    if have apt-get; then
      ensure_sudo apt-get update
      ensure_sudo apt-get install -y nodejs npm
    else
      install_linux_pkgs nodejs npm
    fi
  fi
}

resolve_repo_dir() {
  if [[ -f "pyproject.toml" ]] && grep -q 'name = "rica"' pyproject.toml; then
    pwd
    return
  fi

  ensure_git
  mkdir -p "$(dirname "$INSTALL_DIR")"
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    log "Updating existing Rica checkout at $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only >&2
  else
    log "Cloning Rica into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR" >&2
  fi
  printf '%s\n' "$INSTALL_DIR"
}

main() {
  ensure_python
  ensure_node

  local repo_dir
  repo_dir="$(resolve_repo_dir)"
  cd "$repo_dir"

  log "Setting up Python virtual environment"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate

  log "Upgrading pip"
  python -m pip install --upgrade pip

  log "Installing Rica backend dependencies"
  pip install -e '.[dev]'
  pip install -r bot/requirements.txt -r dashboard/api/requirements.txt

  log "Installing Rica dashboard web dependencies"
  (cd dashboard/web && npm install)

  log "Launching Rica onboarding"
  rica onboard

  printf '\nRica is installed. Next steps:\n'
  printf '  source %s/.venv/bin/activate\n' "$repo_dir"
  printf '  cd %s\n' "$repo_dir"
  printf '  rica start\n\n'
}

main "$@"

#!/bin/zsh

cd "$(dirname "$0")/.." || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "This needs a free program called Python. It is not on this computer yet."
  echo "Install it from: https://www.python.org/downloads/"
  echo "Then double-click this file again."
  echo
  read "reply?Press Return to close."
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Python is installed, but it is too old."
  echo "Install Python 3.10 or newer from: https://www.python.org/downloads/"
  echo "Then double-click this file again."
  echo
  read "reply?Press Return to close."
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "Preparing Chess Clock for first use…"
  python3 -m venv .venv || exit 1
fi

source .venv/bin/activate
python -m pip install --quiet --disable-pip-version-check -r requirements.txt || exit 1

echo
read "host?BUSY Bar IP [10.0.4.20 for USB]: "

args=()
if [[ -n "$host" ]]; then
  args+=(--host "$host")
fi

echo
python install_on_bar.py "${args[@]}"
status=$?

echo
if [[ $status -ne 0 ]]; then
  echo "Install stopped with an error. Check the message above."
fi
read "reply?Press Return to close."
exit $status

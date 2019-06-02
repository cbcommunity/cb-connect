SCRIPTPATH=$(dirname "$BASH_SOURCE")

if [[ ! -d "${SCRIPTPATH}/.env" ]]; then
    python3.6 -m venv "${SCRIPTPATH}/.env"
fi

. ${SCRIPTPATH}/.env/bin/activate

pip install --upgrade pip
pip install cbapi
pip install jupyter[notebook]


#!/usr/bin/env bash

if [ -z "$PYTHON" ]; then
    PYTHON=python
fi

if [ -z "$VENV_DIR" ]; then
    VENV_DIR="$(dirname "$0")/venv"
fi

mkdir tmp 2>/dev/null

check_pip() {
    $PYTHON -mpip --help >tmp/stdout.txt 2>tmp/stderr.txt
    if [ $? -eq 0 ]; then
        start_venv
    elif [ -z "$PIP_INSTALLER_LOCATION" ]; then
        show_stdout_stderr
    else
        $PYTHON "$PIP_INSTALLER_LOCATION" >tmp/stdout.txt 2>tmp/stderr.txt
        if [ $? -eq 0 ]; then
            start_venv
        else
            echo "Couldn't install pip"
            show_stdout_stderr
        fi
    fi
}

start_venv() {
    if [ "$VENV_DIR" = "-" ] || [ "$SKIP_VENV" = "1" ]; then
        return
    fi

    if [ -x "$VENV_DIR/bin/python" ]; then
        activate_venv
    else
        PYTHON_FULLNAME=$(python -c "import sys; print(sys.executable)")
        echo "Creating venv in directory $VENV_DIR using python $PYTHON_FULLNAME"
        $PYTHON_FULLNAME -m venv "$VENV_DIR" >tmp/stdout.txt 2>tmp/stderr.txt
        if [ $? -eq 0 ]; then
            upgrade_pip
        else
            echo "Unable to create venv in directory $VENV_DIR"
            show_stdout_stderr
        fi
    fi
}

upgrade_pip() {
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    if [ $? -eq 0 ]; then
        activate_venv
    else
        echo "Warning: Failed to upgrade PIP version"
    fi
}

activate_venv() {
    PYTHON="$VENV_DIR/bin/python"
    source "$VENV_DIR/bin/activate"
    echo "venv $PYTHON"
}

launch() {
    $PYTHON run_server.py "$@"
    read -p "Press any key to continue..."
    exit
}

show_stdout_stderr() {
    echo
    echo "exit code: $?"

    if [ -s "tmp/stdout.txt" ]; then
        echo
        echo "stdout:"
        cat tmp/stdout.txt
    fi

    if [ -s "tmp/stderr.txt" ]; then
        echo
        echo "stderr:"
        cat tmp/stderr.txt
    fi
}

$PYTHON -c "" >tmp/stdout.txt 2>tmp/stderr.txt
if [ $? -eq 0 ]; then
    check_pip
else
    echo "Couldn't launch python"
    show_stdout_stderr
fi

# Main script execution
launch

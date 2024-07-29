#!/bin/bash

# cleanup_pyenv.sh
# This script uninstalls pyenv and cleans up associated files.
# Make sure to give it execute permissions: chmod +x cleanup_pyenv.sh

set -e

# Function to display messages
function echo_message {
	echo "==> $1"
}

# Function to clean up pyenv
function cleanup_pyenv {
	echo_message "Starting pyenv cleanup..."

	if command -v pyenv &> /dev/null; then
		echo_message "pyenv found. Proceeding with uninstallation."

		# Deactivate any active pyenv virtual environment
		if pyenv version-name &> /dev/null; then
			echo_message "Deactivating active pyenv virtual environment..."
			pyenv deactivate || true
		fi

		# Remove pyenv installation
		echo_message "Removing pyenv installation..."
		rm -rf "$(pyenv root)"

		# Remove pyenv initialization from shell profiles
		echo_message "Cleaning up shell profiles..."
		sed -i '/pyenv/d' ~/.bash_profile || true
		sed -i '/pyenv/d' ~/.bashrc || true
		sed -i '/pyenv/d' ~/.zshrc || true

		# Remove pyenv environment variables
		echo_message "Removing pyenv environment variables..."
		unset PYENV_ROOT
		unset PATH

		echo_message "pyenv uninstalled successfully."
	else
		echo_message "pyenv is not installed. No action needed."
	fi

	echo_message "pyenv cleanup completed."
}

# Run the cleanup function
cleanup_pyenv
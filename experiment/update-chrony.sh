#!/bin/bash

DRY_RUN=false

# Check for --dry-run flag
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
fi

# Detect the primary network interface and its subnet
CIDR=$(ip -o -f inet addr show | awk '/scope global/ {print $4; exit}')
NETWORK=$(ipcalc -n "$CIDR" | awk '/Network/ {print $2}')

# Path to chrony.conf
CHRONY_CONF="/etc/chrony/chrony.conf"

# Check if the subnet is already allowed
if grep -q "allow $NETWORK" "$CHRONY_CONF"; then
    echo "Subnet $NETWORK is already allowed in $CHRONY_CONF."
else
    if $DRY_RUN; then
        echo "Would add 'allow $NETWORK' to $CHRONY_CONF."
        echo "Would restart chrony service."
    else
        echo "Adding 'allow $NETWORK' to $CHRONY_CONF..."
        echo -e "\nallow $NETWORK" | sudo tee -a "$CHRONY_CONF" > /dev/null
        echo "Done. Restarting chrony..."
        sudo systemctl restart chrony
    fi
fi


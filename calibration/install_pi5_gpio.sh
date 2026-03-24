#!/bin/bash
# Install GPIO libraries for Raspberry Pi 5
# Run with: bash calibration/install_pi5_gpio.sh

echo "=========================================="
echo "Installing GPIO libraries for Raspberry Pi 5"
echo "=========================================="

echo ""
echo "Step 1: Updating package list..."
sudo apt-get update

echo ""
echo "Step 2: Installing lgpio..."
sudo apt-get install -y python3-lgpio

echo ""
echo "Step 3: Installing gpiozero (Pi 5 compatible)..."
sudo apt-get install -y python3-gpiozero

echo ""
echo "Step 4: Installing pigpio (alternative library)..."
sudo apt-get install -y python3-pigpio pigpio

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "You can now use:"
echo "  - lgpio (recommended for Pi 5)"
echo "  - gpiozero with lgpio backend"
echo "  - pigpio"
echo ""
echo "Testing installation..."
python3 -c "import lgpio; print('✓ lgpio installed successfully')" 2>/dev/null || echo "✗ lgpio not found"
python3 -c "import gpiozero; print('✓ gpiozero installed successfully')" 2>/dev/null || echo "✗ gpiozero not found"
python3 -c "import pigpio; print('✓ pigpio installed successfully')" 2>/dev/null || echo "✗ pigpio not found"
echo ""

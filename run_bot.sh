#!/bin/bash

# Activate venv
source .venv/bin/activate

echo "=================================="
echo "    Nifty Shop Bot Manager"
echo "=================================="
echo "1. Login (Generate Token)"
echo "2. Start Daily Scheduler (Real Money)"
echo "3. Start Immediate run (Dry Run)"
echo "4. Start Daily Scheduler (Dry Run)"
echo "5. Test Single Order (ALSTONE)"
echo "6. Exit"
echo "=================================="
read -p "Select option: " choice

case $choice in
    1)
        python -m src.main --login
        ;;
    2)
        python -m src.main --schedule --real
        ;;
    3)
        python -m src.main --run-now --real --dry-run
        ;;
    4)
        python -m src.main --schedule --real --dry-run
        ;;
    5)
        # Testing specific stock as requested
        python -m src.main --test-order "ALSTONE" --real
        ;;
    6)
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac

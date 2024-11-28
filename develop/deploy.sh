#!/bin/bash
set -x

cp ./scheduler.service /usr/lib/systemd/system
systemctl daemon-reload
systemctl enable scheduler
systemctl start scheduler

#!/bin/bash
for agent in weather news translation; do
    lxc launch ubuntu:jammy ${agent}_agent -p deployment/lxc_profiles/${agent}.conf
    lxc exec ${agent}_agent -- apt update && apt install -y python3-pip
    lxc file push task_agents/${agent}.py ${agent}_agent/root/
done

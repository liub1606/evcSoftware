tmux send-keys -t telem C-c
pkill -TERM -f "gunicorn app:app"
tmux kill-session -t telem

tmux new-session -d -s telem

tmux new-window -t telem:1 -n 'app'
tmux split-window -h -t telem:1
tmux send-keys -t telem:1.0 'cd lhssevc-app/' Enter
tmux send-keys -t telem:1.0 '. venv/bin/activate' Enter
tmux send-keys -t telem:1.0 'gunicorn app:app' Enter

tmux new-window -t telem:2 -n 'host'
tmux send-keys -t telem:2 'cd host/' Enter
tmux send-keys -t telem:2 '. venv/bin/activate' Enter
tmux send-keys -t telem:2 'python host.py -s http://127.0.0.1:8080 /dev/ttyUSB0' Enter

# tmux new-window -t telem:3 -n 'web'
tmux send-keys -t telem:1.1 'cd lhssevc-app/tel-interface/' Enter
tmux send-keys -t telem:1.1 'sleep 5' Enter
tmux send-keys -t telem:1.1 'xdg-open http://127.0.0.1:8080' Enter

tmux new-window -t telem:3 -n 'tunnel'
tmux send-keys -t telem:3 'cloudflared tunnel --url http://127.0.0.1:8080' Enter

tmux attach -t telem


LOGFILE0="/tmp/log0.log"
LOGFILE1="/tmp/log1.log"
IP=224.1.1.1
RESX=1920
RESY=1080

nohup </dev/null gst-launch-1.0 -v -e uvch264src device=/dev/video0 name=src auto-start=true src.vidsrc ! video/x-h264,width=$RESX,height=$RESY,framerate=30/1 ! h264parse ! rtph264pay ! udpsink host=$IP port=5000 >$LOGFILE0 2>&1 &

nohup </dev/null gst-launch-1.0 -v -e uvch264src device=/dev/video1 name=src auto-start=true src.vidsrc ! video/x-h264,width=$RESX,height=$RESY,framerate=30/1 ! h264parse ! rtph264pay ! udpsink host=$IP port=5001 >$LOGFILE1 2>&1 &
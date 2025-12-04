# Clahe
`python clahe.py /Users/eigen/Desktop/道玄坂_2車室_21-24`

`scp -r /Users/eigen/Desktop/道玄坂_2車室_21-24/clahe_results eigen@43.16.136.152:/ext_storage/user/eigen/`  

# SSH to 152
`ssh eigen@43.16.136.152`

# SSH to T4
`ssh root@192.168.11.209`

# Configure
`sshfs eigen@192.168.11.7:/ext_storage/user/eigen/clahe_results Type4_IE_LPR_sdk-v1.0.20-94a048b_20241128/sample/build/mount_point/`

`./start.sh eval`

# Exec
`cd /TSDK/sample/build`

`cp mount_point/lpr.sh lpr.sh`

`sh lpr.sh`

# Download, Check
`scp -r eigen@43.16.136.152:/ext_storage/user/eigen/clahe_results /Users/eigen/Desktop/道玄坂_2車室_21-24/`

`python clahe_viewer.py /Users/eigen/Desktop/道玄坂_2車室_21-24`

